"""Envío puntual de recordatorios al correo verificado, sin perfiles persistidos."""

import hashlib
import hmac
import secrets
import threading
import time
from collections import deque

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr, Field

from backend.schemas import PerfilTributarioCreate
from backend.services.agent_service import AgenteTributarioRIMPE, ResultadoAgente
from backend.services.mailjet_service import MailjetError, MailjetUncertainError, configurado, enviar_correo


router = APIRouter(prefix="/api/correo", tags=["Envío puntual verificado"])
_lock = threading.Lock()
_secret = secrets.token_bytes(32)
_pending = {}
_requests = {}
_global_requests = deque()
_sent = {}


class SolicitarCodigo(BaseModel):
    email: EmailStr


class EnviarRecordatorioVerificado(BaseModel):
    email: EmailStr
    codigo: str = Field(min_length=6, max_length=6)
    perfil: PerfilTributarioCreate
    anio: int = Field(default=2026, ge=2024, le=2030)
    codigo_obligacion: str = Field(min_length=3)
    confirmacion_envio: bool


def _email_key(email: str) -> str:
    return hmac.new(_secret, email.lower().encode(), hashlib.sha256).hexdigest()


def _code_hash(key: str, code: str) -> str:
    return hmac.new(_secret, f"{key}:{code}".encode(), hashlib.sha256).hexdigest()


def _prune_state(now: float):
    """Elimina códigos caducados y ventanas de tasa vencidas bajo _lock."""
    while _global_requests and _global_requests[0] <= now - 3600:
        _global_requests.popleft()
    for key, (_, expires, _) in list(_pending.items()):
        if expires < now:
            _pending.pop(key, None)
    for counters in (_requests, _sent):
        for key, timestamps in list(counters.items()):
            active = [timestamp for timestamp in timestamps if timestamp > now - 3600]
            if active:
                counters[key] = active
            else:
                counters.pop(key, None)


def _mail_ready():
    if not configurado():
        raise HTTPException(503, "El envío de correo no está configurado en este servicio.")


def _send_code(email: str, code: str):
    return enviar_correo(
        email, "Código para recibir tu recordatorio RIMPE",
        f"Tu código de verificación es {code}. Caduca en 10 minutos. Si no lo solicitaste, ignora este mensaje.",
    )


@router.post("/solicitar-codigo")
def solicitar_codigo(payload: SolicitarCodigo):
    _mail_ready()
    email = str(payload.email).lower()
    key = _email_key(email)
    now = time.monotonic()
    with _lock:
        _prune_state(now)
        recent = _requests.get(key, [])
        if len(_global_requests) >= 60 or len(recent) >= 3 or (recent and recent[-1] > now - 60):
            raise HTTPException(429, "Espera antes de solicitar otro código.")
        recent.append(now)
        _requests[key] = recent
        _global_requests.append(now)
        code = f"{secrets.randbelow(1000000):06d}"
        _pending[key] = (_code_hash(key, code), now + 600, 0)
    try:
        _send_code(email, code)
    except MailjetUncertainError:
        return {"mensaje": "Mailjet no confirmó el envío. Si recibes el código, puedes usarlo.", "caduca_en_segundos": 600, "estado": "INCIERTO"}
    except MailjetError:
        with _lock:
            _pending.pop(key, None)
        raise HTTPException(503, "No se pudo enviar el código de verificación.")
    return {"mensaje": "Mailjet aceptó el código para envío.", "caduca_en_segundos": 600, "estado": "ACEPTADO"}


@router.post("/enviar-recordatorio", response_model=ResultadoAgente)
def enviar_recordatorio(payload: EnviarRecordatorioVerificado):
    if not payload.confirmacion_envio:
        raise HTTPException(403, "Se requiere confirmación explícita del envío.")
    email = str(payload.email).lower()
    if str(payload.perfil.email).lower() != email:
        raise HTTPException(403, "El correo verificado no coincide con el destinatario.")
    _mail_ready()
    key = _email_key(email)
    now = time.monotonic()
    with _lock:
        _prune_state(now)
        entry = _pending.get(key)
        if not entry or entry[1] < now:
            raise HTTPException(403, "El código no existe o caducó.")
        expected, expiry, failures = entry
        if not hmac.compare_digest(expected, _code_hash(key, payload.codigo)):
            failures += 1
            if failures >= 3:
                _pending.pop(key, None)
            else:
                _pending[key] = (expected, expiry, failures)
            raise HTTPException(403, "Código incorrecto o caducado.")
        sent = _sent.get(key, [])
        if len(sent) >= 3 or (sent and sent[-1] > now - 60):
            raise HTTPException(429, "Ya se solicitó un recordatorio para este correo recientemente.")
        _pending.pop(key, None)
        sent.append(now)
        _sent[key] = sent
    perfil = payload.perfil.model_dump(mode="json")
    perfil.update(email=email, anio=payload.anio)
    # El código de un solo uso ya se consumió: evitar una dependencia de red adicional.
    resultado = AgenteTributarioRIMPE(usar_seleccion_gemini=False).ejecutar(
        instruccion="Preparar y despachar recordatorio tributario autorizado",
        perfil=perfil,
        confirmacion_envio=True,
        codigo_obligacion=payload.codigo_obligacion,
    )
    return resultado
