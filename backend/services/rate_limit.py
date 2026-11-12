"""Cuota en memoria para la explicación generativa de la instancia única."""

import hashlib
import hmac
import math
import os
import secrets
import threading
import time
from collections import deque

from fastapi import HTTPException, Request


def _positive_env(name: str, default: int) -> int:
    try:
        value = int(os.getenv(name, str(default)))
    except ValueError:
        return default
    return value if value > 0 else default


class SlidingWindowLimiter:
    def __init__(self, per_client: int, global_limit: int, window_seconds: int):
        self.per_client = per_client
        self.global_limit = global_limit
        self.window_seconds = window_seconds
        self._lock = threading.Lock()
        self._secret = secrets.token_bytes(32)
        self._clients: dict[str, deque[float]] = {}
        self._global: deque[float] = deque()

    def check(self, client: str, now: float | None = None, cost: int = 1) -> int | None:
        """Reserva el coste máximo de una operación o devuelve el próximo cupo."""
        if cost < 1 or cost > min(self.per_client, self.global_limit):
            raise ValueError("El coste excede la cuota configurada.")
        now = time.monotonic() if now is None else now
        key = hmac.new(self._secret, client.encode(), hashlib.sha256).hexdigest()
        cutoff = now - self.window_seconds
        with self._lock:
            while self._global and self._global[0] <= cutoff:
                self._global.popleft()
            for stored_key, timestamps in list(self._clients.items()):
                while timestamps and timestamps[0] <= cutoff:
                    timestamps.popleft()
                if not timestamps:
                    del self._clients[stored_key]

            client_calls = self._clients.get(key)
            waits = []
            global_to_expire = len(self._global) + cost - self.global_limit
            if global_to_expire > 0:
                waits.append(self._global[global_to_expire - 1] + self.window_seconds - now)
            client_to_expire = len(client_calls or ()) + cost - self.per_client
            if client_to_expire > 0 and client_calls:
                waits.append(client_calls[client_to_expire - 1] + self.window_seconds - now)
            if waits:
                return max(1, math.ceil(max(waits)))

            self._global.extend([now] * cost)
            self._clients.setdefault(key, deque()).extend([now] * cost)
            return None


explanation_limiter = SlidingWindowLimiter(
    per_client=_positive_env("GEMINI_RATE_LIMIT_PER_CLIENT", 12),
    global_limit=_positive_env("GEMINI_RATE_LIMIT_GLOBAL", 30),
    window_seconds=_positive_env("GEMINI_RATE_LIMIT_WINDOW_SECONDS", 60),
)


def limit_explanation_requests(request: Request) -> None:
    # Uvicorn recibe la IP del proxy de confianza; no leer X-Forwarded-For aquí.
    client = request.client.host if request.client else "unknown"
    retry_after = explanation_limiter.check(client)
    if retry_after is not None:
        raise HTTPException(
            status_code=429,
            detail="Demasiadas solicitudes de explicación. Intenta de nuevo más tarde.",
            headers={"Retry-After": str(retry_after)},
        )


def limit_agent_requests(request: Request) -> None:
    """Reserva hasta cuatro llamadas del selector de herramientas por ejecución."""
    client = request.client.host if request.client else "unknown"
    try:
        retry_after = explanation_limiter.check(client, cost=4)
    except ValueError:
        raise HTTPException(503, "La cuota configurada es insuficiente para el agente.")
    if retry_after is not None:
        raise HTTPException(
            status_code=429,
            detail="Demasiadas solicitudes del agente. Intenta de nuevo más tarde.",
            headers={"Retry-After": str(retry_after)},
        )
