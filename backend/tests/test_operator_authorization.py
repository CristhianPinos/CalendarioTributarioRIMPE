"""Pruebas HTTP de la frontera de autorización de recordatorios."""

import asyncio
import base64
from types import SimpleNamespace

import httpx
import pytest
from fastapi import HTTPException
from fastapi.security import HTTPBasicCredentials

from backend.main import app
from backend.operator_auth import optional_operator, require_operator, require_dispatch_operator
from backend.services.agent_service import EnviarRecordatorioOutput, ResultadoAgente


PASSWORD = "clave-de-prueba-muy-larga-y-unica"


def test_auth_dependency_fails_closed_and_checks_identity(monkeypatch):
    monkeypatch.delenv("REMINDER_OPERATOR_USER", raising=False)
    monkeypatch.delenv("REMINDER_OPERATOR_PASSWORD", raising=False)
    with pytest.raises(HTTPException) as missing_config:
        require_operator(None)
    assert missing_config.value.status_code == 503
    with pytest.raises(HTTPException) as anonymous:
        require_dispatch_operator(None)
    assert anonymous.value.status_code == 401

    monkeypatch.setenv("REMINDER_OPERATOR_USER", "operador_prueba")
    monkeypatch.setenv("REMINDER_OPERATOR_PASSWORD", PASSWORD)
    assert optional_operator(HTTPBasicCredentials(username="operador_prueba", password=PASSWORD)) == "operador_prueba"
    with pytest.raises(HTTPException) as wrong_password:
        optional_operator(HTTPBasicCredentials(username="operador_prueba", password="incorrecta"))
    assert wrong_password.value.status_code == 401


def _request(method, path, *, json=None, auth=None):
    """Ejecuta una petición ASGI sin depender de TestClient en Python 3.14."""
    headers = {}
    if auth:
        encoded = base64.b64encode(f"{auth[0]}:{auth[1]}".encode()).decode()
        headers["Authorization"] = f"Basic {encoded}"

    async def run():
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            return await client.request(method, path, json=json, headers=headers)

    return asyncio.run(run())


def _auth():
    return ("operador_prueba", PASSWORD)


def _agent_payload(confirm):
    return {
        "instruccion": "Preparar recordatorio",
        "perfil": {"ruc": "0923456784001", "tipo_regimen": "RIMPE_EMPRENDEDOR", "email": "contribuyente@example.com"},
        "confirmacion_envio": confirm,
    }


def _send_payload(confirm):
    return {
        "destinatario": "contribuyente@example.com",
        "asunto": "Recordatorio de IVA",
        "texto": "Recordatorio de prueba con cita [LRTI, Art. 97.6]",
        "confirmacion_usuario": confirm,
    }


def test_no_dispatch_without_config_or_credentials(monkeypatch):
    monkeypatch.delenv("REMINDER_OPERATOR_USER", raising=False)
    monkeypatch.delenv("REMINDER_OPERATOR_PASSWORD", raising=False)
    for path, payload in (
        ("/api/agente/ejecutar", _agent_payload(True)),
        ("/api/agente/herramientas/enviar-recordatorio", _send_payload(True)),
    ):
        assert _request("POST", path, json=payload).status_code == 401
    assert _request("GET", "/api/flujo/recordatorios-pendientes").status_code == 503


def test_all_flow_routes_require_operator(monkeypatch):
    monkeypatch.setenv("REMINDER_OPERATOR_USER", "operador_prueba")
    monkeypatch.setenv("REMINDER_OPERATOR_PASSWORD", PASSWORD)
    assert _request("GET", "/api/flujo/recordatorios-pendientes").status_code == 401
    assert _request("POST", "/api/flujo/ejecutar-tarea-diaria", json={}).status_code == 401
    assert _request("POST", "/api/flujo/confirmar-recordatorio/REC-1", json={}).status_code == 401
    assert _request("POST", "/api/flujo/confirmar-todos", json={}).status_code == 401
    assert _request("POST", "/api/flujo/confirmar-todos", json={}, auth=("operador_prueba", "incorrecta")).status_code == 401


def test_confirmed_agent_requires_operator_and_records_identity(monkeypatch):
    monkeypatch.setenv("REMINDER_OPERATOR_USER", "operador_prueba")
    monkeypatch.setenv("REMINDER_OPERATOR_PASSWORD", PASSWORD)
    monkeypatch.setattr("backend.routers.agente_router._STORE_GLOBAL", SimpleNamespace(has_consent=lambda ruc, email: True))

    def fake_execute(self, **kwargs):
        return ResultadoAgente(
            instruccion_original=kwargs["instruccion"], exito=True, num_iteraciones=1,
            limite_alcanzado=False, trazas_herramientas=[], respuesta_final="Preparado",
            estado_envio="PENDIENTE_CONFIRMACION",
        )

    monkeypatch.setattr("backend.routers.agente_router.AgenteTributarioRIMPE.ejecutar", fake_execute)
    assert _request("POST", "/api/agente/ejecutar", json=_agent_payload(True)).status_code == 401
    assert _request("POST", "/api/agente/ejecutar", json=_agent_payload(True), auth=("operador_prueba", "incorrecta")).status_code == 401
    approved = _request("POST", "/api/agente/ejecutar", json=_agent_payload(True), auth=_auth())
    assert approved.status_code == 200
    assert approved.json()["usuario_confirmador"] == "operador_prueba"
    prepared = _request("POST", "/api/agente/ejecutar", json=_agent_payload(False))
    assert prepared.status_code == 200
    assert prepared.json()["usuario_confirmador"] is None


def test_direct_dispatch_requires_operator(monkeypatch):
    monkeypatch.setenv("REMINDER_OPERATOR_USER", "operador_prueba")
    monkeypatch.setenv("REMINDER_OPERATOR_PASSWORD", PASSWORD)
    monkeypatch.setattr("backend.routers.agente_router._STORE_GLOBAL", SimpleNamespace(has_consent_email=lambda email: True))

    def fake_send(params):
        return EnviarRecordatorioOutput(
            estado="ENVIADO", destinatario=params.destinatario, canal="email",
            confirmado=True, mensaje_accion="Enviado", timestamp="2026-11-07T00:00:00Z",
            id_registro_auditoria="AUD-PRUEBA",
        )

    monkeypatch.setattr("backend.routers.agente_router.tool_enviar_recordatorio", fake_send)
    assert _request("POST", "/api/agente/herramientas/enviar-recordatorio", json=_send_payload(True)).status_code == 401
    response = _request("POST", "/api/agente/herramientas/enviar-recordatorio", json=_send_payload(True), auth=_auth())
    assert response.status_code == 200
    assert response.json()["usuario_confirmador"] == "operador_prueba"


def test_confirmed_queue_uses_authenticated_identity(monkeypatch):
    monkeypatch.setenv("REMINDER_OPERATOR_USER", "operador_prueba")
    monkeypatch.setenv("REMINDER_OPERATOR_PASSWORD", PASSWORD)
    captured = {}

    def fake_confirm(**kwargs):
        captured.update(kwargs)
        return EnviarRecordatorioOutput(
            estado="ENVIADO", destinatario="contribuyente@example.com", canal="email",
            confirmado=True, mensaje_accion="Enviado", timestamp="2026-11-07T00:00:00Z",
            id_registro_auditoria="AUD-PRUEBA", usuario_confirmador=kwargs["usuario_confirmador"],
        )

    monkeypatch.setattr("backend.routers.flujo_router.confirmar_y_despachar_recordatorio", fake_confirm)
    response = _request("POST",
        "/api/flujo/confirmar-recordatorio/REC-1",
        json={"usuario_confirmador": "suplantador"}, auth=_auth(),
    )
    assert response.status_code == 200
    assert captured["usuario_confirmador"] == "operador_prueba"
    assert response.json()["usuario_confirmador"] == "operador_prueba"


def test_batch_confirmation_uses_authenticated_identity(monkeypatch):
    monkeypatch.setenv("REMINDER_OPERATOR_USER", "operador_prueba")
    monkeypatch.setenv("REMINDER_OPERATOR_PASSWORD", PASSWORD)
    captured = {}

    def fake_confirm_all(**kwargs):
        captured.update(kwargs)
        return []

    monkeypatch.setattr("backend.routers.flujo_router.confirmar_todos_los_pendientes", fake_confirm_all)
    response = _request("POST", "/api/flujo/confirmar-todos", json={"usuario_confirmador": "suplantador"}, auth=_auth())
    assert response.status_code == 200
    assert captured["usuario_confirmador"] == "operador_prueba"
