"""Borradores temporales del correo revisado; no persisten perfiles ni destinatarios."""

import hashlib
import hmac
import secrets
import threading
import time

from backend.schemas import ExplicacionObligacionRequest, ExplicacionObligacionResponse, PerfilTributarioCreate
from backend.services.agent_service import RedactarRecordatorioInput, RedactarRecordatorioOutput, tool_redactar_recordatorio
from backend.services.calculator import calcular_vencimientos

_lock = threading.Lock()
_key = secrets.token_bytes(32)
_explanations = {}
_drafts = {}
_TTL = 900


def _prune(now):
    for bucket in (_explanations, _drafts):
        for identifier, item in list(bucket.items()):
            if item[0] < now:
                bucket.pop(identifier, None)
        while len(bucket) > 512:
            bucket.pop(next(iter(bucket)))


def remember_explanation(request: ExplicacionObligacionRequest, response: ExplicacionObligacionResponse) -> str:
    identifier = secrets.token_urlsafe(24)
    with _lock:
        _prune(time.monotonic())
        _explanations[identifier] = (time.monotonic() + _TTL, request.model_copy(deep=True), response.model_copy(deep=True))
    return identifier


def _fingerprint(profile: PerfilTributarioCreate, email: str, year: int, code: str) -> str:
    raw = f"{profile.ruc}|{profile.razon_social}|{profile.tipo_regimen.value}|{profile.tiene_actividades_excluidas}|{email.lower()}|{year}|{code}"
    return hmac.new(_key, raw.encode(), hashlib.sha256).hexdigest()


def prepare_draft(explanation_id: str, profile: PerfilTributarioCreate, email: str, year: int, code: str) -> dict:
    with _lock:
        _prune(time.monotonic())
        snapshot = _explanations.get(explanation_id)
    if snapshot is None:
        raise ValueError("La explicación caducó; regenera el contenido antes de enviar.")
    _, request, response = snapshot
    if request.codigo_obligacion != code or request.tipo_regimen != profile.tipo_regimen or request.es_declaracion_en_cero and code not in {"IVA_SEMESTRAL_1", "IVA_SEMESTRAL_2"}:
        raise ValueError("La explicación no coincide con el perfil y la obligación.")
    if request.tiene_actividades_excluidas != profile.tiene_actividades_excluidas:
        raise ValueError("La explicación no coincide con las actividades del perfil.")
    calendar = calcular_vencimientos(profile.ruc, profile.tipo_regimen.value, year, profile.tiene_actividades_excluidas)
    event = next((e for e in calendar["eventos"] if e["codigo_obligacion"] == code), None)
    if event is None or event["fecha_vencimiento"] != request.fecha_vencimiento:
        raise ValueError("La fecha u obligación no corresponde al calendario calculado.")
    base = tool_redactar_recordatorio(RedactarRecordatorioInput(
        codigo_obligacion=code, ruc=profile.ruc, razon_social=profile.razon_social,
        tipo_regimen=profile.tipo_regimen.value, fecha_vencimiento=event["fecha_vencimiento"],
        titulo_obligacion=event["titulo"], anio_fiscal=year,
    ))
    explanation = response.obligacion
    sources = response.fuentes_rag
    fecha_texto = (
        f"Fecha orientativa mostrada en este calendario: {event['fecha_vencimiento']}. Confirma la fecha aplicable en SRI en Línea."
        if code == "IVA_REGIMEN_GENERAL_MIXTO"
        else f"Fecha de vencimiento calculada por Python: {event['fecha_vencimiento']}."
    )
    body = (
        f"Estimado(a) {profile.razon_social} (RUC: {profile.ruc[:4]}****{profile.ruc[10:]}),\n\n"
        f"Obligación: {event['titulo']} (ejercicio fiscal {year}).\n"
        f"{fecha_texto}\n\n"
        f"Resumen explicativo: {explanation.explicacion_sencilla}\n\n"
        f"Comprobantes y documentos: {explanation.comprobantes_validos}\n\n"
        f"Acción sugerida: {explanation.sugerencia_accion}\n"
        f"Canal recomendado: {explanation.canal_recomendado}\n\n"
        f"Base legal: {explanation.base_legal_oficial}\n"
        + (f"Fuentes recuperadas: {', '.join(sources)}\n" if sources else "")
        + ("Origen de la explicación: catálogo determinista de contingencia.\n" if response.modelo_utilizado == "fallback-determinista-sri" else "Origen de la explicación: Gemini con fuentes normativas recuperadas.\n")
        + "\nRecordatorio informativo de Calendario RIMPE. Envío sujeto a autorización del usuario. "
        "No constituye una comunicación oficial del SRI."
    )
    draft = RedactarRecordatorioOutput(
        asunto=base.asunto, cuerpo_recordatorio=body,
        citas_normativas=[explanation.base_legal_oficial, *sources],
        codigo_obligacion=code, fecha_vencimiento=event["fecha_vencimiento"],
    )
    identifier = secrets.token_urlsafe(24)
    with _lock:
        _prune(time.monotonic())
        _drafts[identifier] = (time.monotonic() + _TTL, _fingerprint(profile, email, year, code), draft)
    return {"borrador_id": identifier, "asunto": draft.asunto, "cuerpo": draft.cuerpo_recordatorio,
            "caduca_en_segundos": _TTL}


def take_draft(identifier: str, profile: PerfilTributarioCreate, email: str, year: int, code: str) -> RedactarRecordatorioOutput:
    with _lock:
        _prune(time.monotonic())
        entry = _drafts.get(identifier)
        if entry is None or not hmac.compare_digest(entry[1], _fingerprint(profile, email, year, code)):
            raise ValueError("El borrador caducó o no corresponde al destinatario y perfil.")
        _drafts.pop(identifier, None)
    return entry[2]


def check_draft(identifier: str, profile: PerfilTributarioCreate, email: str, year: int, code: str) -> None:
    with _lock:
        _prune(time.monotonic())
        entry = _drafts.get(identifier)
        if entry is None or not hmac.compare_digest(entry[1], _fingerprint(profile, email, year, code)):
            raise ValueError("El borrador caducó o no corresponde al destinatario y perfil.")
