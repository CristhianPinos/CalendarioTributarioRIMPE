"""Cuota real del endpoint generativo sin exponer identificadores de clientes."""

from concurrent.futures import ThreadPoolExecutor
from unittest.mock import Mock, patch

import pytest
from fastapi import HTTPException, Request
from fastapi.routing import APIRoute

from backend.main import app
from backend.routers.obligaciones_router import router as obligaciones_router
from backend.schemas import ExplicacionObligacionRequest
from backend.services.rate_limit import SlidingWindowLimiter, limit_explanation_requests, limit_agent_requests
from backend.services import rate_limit
from backend.services.llm import _invocar_gemini_raw, MAX_OUTPUT_TOKENS


def test_client_limit_and_retry_after_without_raw_ip():
    limiter = SlidingWindowLimiter(per_client=2, global_limit=10, window_seconds=60)
    assert limiter.check("192.0.2.10", now=100.0) is None
    assert limiter.check("192.0.2.10", now=101.0) is None
    assert limiter.check("192.0.2.10", now=102.0) == 58
    assert limiter.check("192.0.2.11", now=102.0) is None
    assert "192.0.2.10" not in limiter._clients
    assert limiter.check("192.0.2.10", now=160.0) is None


def test_global_limit_is_atomic_under_concurrency():
    limiter = SlidingWindowLimiter(per_client=20, global_limit=5, window_seconds=60)
    with ThreadPoolExecutor(max_workers=12) as executor:
        results = list(executor.map(lambda n: limiter.check(f"192.0.2.{n}", now=100.0), range(12)))
    assert results.count(None) == 5
    assert results.count(60) == 7


def test_agent_reservation_counts_up_to_four_model_calls():
    limiter = SlidingWindowLimiter(per_client=8, global_limit=8, window_seconds=60)
    assert limiter.check("192.0.2.10", now=100, cost=4) is None
    assert limiter.check("192.0.2.10", now=101, cost=4) is None
    assert limiter.check("192.0.2.10", now=102) == 58
    assert limiter.check("192.0.2.11", now=102, cost=4) == 58
    assert limiter.check("192.0.2.11", now=160, cost=4) is None


def test_agent_dependency_returns_429_and_retry_after(monkeypatch):
    limiter = SlidingWindowLimiter(per_client=4, global_limit=8, window_seconds=60)
    monkeypatch.setattr(rate_limit, "explanation_limiter", limiter)
    request = Request({"type": "http", "method": "POST", "path": "/api/agente/ejecutar",
                       "headers": [], "client": ("192.0.2.25", 1000)})
    limit_agent_requests(request)
    with pytest.raises(HTTPException) as caught:
        limit_agent_requests(request)
    assert caught.value.status_code == 429
    assert 1 <= int(caught.value.headers["Retry-After"]) <= 60


def test_http_dependency_returns_429_with_retry_after(monkeypatch):
    limiter = SlidingWindowLimiter(per_client=1, global_limit=5, window_seconds=60)
    monkeypatch.setattr(rate_limit, "explanation_limiter", limiter)
    request = Request({"type": "http", "method": "POST", "path": "/api/obligaciones/explicar",
                       "headers": [], "client": ("192.0.2.25", 1000)})
    limit_explanation_requests(request)
    with pytest.raises(HTTPException) as caught:
        limit_explanation_requests(request)
    assert caught.value.status_code == 429
    assert 1 <= int(caught.value.headers["Retry-After"]) <= 60
    assert "192.0.2.25" not in caught.value.detail


def test_only_generative_route_uses_the_quota():
    # FastAPI puede conservar include_router como _IncludedRouter hasta el arranque.
    assert any(getattr(route, "original_router", None) is obligaciones_router for route in app.routes)
    routes = {route.path: route for route in obligaciones_router.routes if isinstance(route, APIRoute)}
    quota_routes = {
        path for path, route in routes.items()
        if any(dep.call is limit_explanation_requests for dep in route.dependant.dependencies)
    }
    assert quota_routes == {"/api/obligaciones/explicar"}
    assert "/api/simulador/renta" not in quota_routes


def test_obligation_code_length_is_bounded():
    with pytest.raises(ValueError):
        ExplicacionObligacionRequest(
            codigo_obligacion="X" * 65,
            tipo_regimen="RIMPE_EMPRENDEDOR",
            fecha_vencimiento="2027-05-20",
        )


def test_gemini_request_has_bounded_output():
    response = Mock(status_code=200)
    response.json.return_value = {
        "candidates": [{"content": {"parts": [{"text": "{}"}]}}],
        "usageMetadata": {"totalTokenCount": 2},
    }
    with patch("backend.services.llm._enviar_http_gemini", return_value=response) as send:
        parsed, _ = _invocar_gemini_raw.__wrapped__("Explica IVA", "test-key")
    assert parsed == {}
    assert send.call_args.args[1]["generationConfig"]["maxOutputTokens"] == MAX_OUTPUT_TOKENS
    assert 256 <= MAX_OUTPUT_TOKENS <= 8192
