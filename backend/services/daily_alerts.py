"""Escaneo general de vencimientos, sin perfiles ni destinatarios almacenados."""

from datetime import date, datetime, timedelta
from threading import Lock
from zoneinfo import ZoneInfo

from backend.services.calculator import calcular_vencimientos_por_digito
from backend.services.config_loader import get_feriados_2026, load_parametros

_lock = Lock()
_cache = None
_WINDOW = 5


def _business_days_between(start: date, end: date, holidays: set) -> int:
    current = start + timedelta(days=1)
    count = 0
    while current <= end:
        if current.weekday() < 5 and (current.month, current.day) not in holidays:
            count += 1
        current += timedelta(days=1)
    return count


def scan_alerts(today: date | None = None) -> dict:
    """Prepara alertas por combinación tributaria para el ejercicio configurado."""
    global _cache
    today = today or datetime.now(ZoneInfo("America/Guayaquil")).date()
    with _lock:
        if _cache is not None and _cache["fecha_escaneo"] == today.isoformat():
            return _cache
        year = int(load_parametros()["parametros_economicos"]["anio_fiscal"])
        feriados = {(item["mes"], item["dia"]) for item in get_feriados_2026()}
        alerts = {}
        for digit in range(10):
            for regimen in ("RIMPE_NEGOCIO_POPULAR", "RIMPE_EMPRENDEDOR"):
                for excluded in (False, True):
                    events = calcular_vencimientos_por_digito(digit, regimen, year, excluded)["eventos"]
                    matched = []
                    for event in events:
                        due = date.fromisoformat(event["fecha_vencimiento"])
                        if due < today:
                            continue
                        days = _business_days_between(today, due, feriados)
                        if days <= _WINDOW:
                            matched.append({
                                "codigo_obligacion": event["codigo_obligacion"],
                                "fecha_vencimiento": event["fecha_vencimiento"],
                                "dias_habiles_restantes": days,
                                "vence_hoy": due == today,
                            })
                    alerts[(digit, regimen, excluded)] = matched
        _cache = {"fecha_escaneo": today.isoformat(), "anio_fiscal": year, "alertas": alerts}
        return _cache


def alerts_for_profile(digit: int, regimen: str, excluded: bool, year: int) -> dict:
    result = scan_alerts()
    if year != result["anio_fiscal"]:
        raise ValueError("El ejercicio solicitado no tiene un escaneo normativo configurado.")
    if type(digit) is not int or not 0 <= digit <= 9 or type(excluded) is not bool:
        raise ValueError("Parámetros de alerta inválidos.")
    key = (digit, regimen, excluded)
    if key not in result["alertas"]:
        raise ValueError("Régimen inválido.")
    return {"fecha_escaneo": result["fecha_escaneo"], "ventana_dias_habiles": _WINDOW,
            "alertas": result["alertas"][key]}
