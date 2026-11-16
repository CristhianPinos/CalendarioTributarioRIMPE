"""Escaneo general, aislamiento de datos y disparador protegido."""

from datetime import date

import pytest
from fastapi import HTTPException

from backend.routers.calendario_router import ejecutar_escaneo
from backend.services import daily_alerts
from backend.services.calculator import calcular_vencimientos, calcular_vencimientos_por_digito


def test_digit_core_preserves_public_calendar():
    profile = calcular_vencimientos("0923456784001", "RIMPE_EMPRENDEDOR", 2026, True)
    generic = calcular_vencimientos_por_digito(8, "RIMPE_EMPRENDEDOR", 2026, True)
    assert {key: value for key, value in profile.items() if key != "ruc"} == generic


def test_scan_prepares_only_nonidentifying_near_alerts():
    daily_alerts._cache = None
    result = daily_alerts.scan_alerts(date(2026, 7, 9))
    assert len(result["alertas"]) == 40
    matching = result["alertas"][(1, "RIMPE_EMPRENDEDOR", False)]
    assert any(item["codigo_obligacion"] == "IVA_SEMESTRAL_1" for item in matching)
    assert result["alertas"][(1, "RIMPE_NEGOCIO_POPULAR", False)] == []
    assert "ruc" not in str(result).lower()
    assert "email" not in str(result).lower()
    assert daily_alerts.scan_alerts(date(2026, 7, 9)) is result


def test_scan_rolls_to_next_local_day_and_rejects_unconfigured_year():
    daily_alerts._cache = None
    first = daily_alerts.scan_alerts(date(2026, 7, 9))
    second = daily_alerts.scan_alerts(date(2026, 7, 10))
    assert first is not second
    assert second["alertas"][(1, "RIMPE_EMPRENDEDOR", False)][0]["vence_hoy"]
    try:
        daily_alerts.alerts_for_profile(1, "RIMPE_EMPRENDEDOR", False, 2027)
    except ValueError:
        pass
    else:
        raise AssertionError("El escaneo no debe extrapolar reglas a otro ejercicio")


def test_january_deadline_from_previous_fiscal_year_is_detected():
    daily_alerts._cache = None
    result = daily_alerts.scan_alerts(date(2027, 1, 18))
    assert result["alertas"][(8, "RIMPE_EMPRENDEDOR", False)] == [
        {"codigo_obligacion": "IVA_SEMESTRAL_2", "fecha_vencimiento": "2027-01-25",
         "dias_habiles_restantes": 5, "vence_hoy": False}
    ]


def test_trigger_requires_secret_and_only_returns_counts(monkeypatch):
    monkeypatch.setenv("SCAN_TRIGGER_TOKEN", "test-secret")
    with pytest.raises(HTTPException) as missing:
        ejecutar_escaneo(None)
    assert missing.value.status_code == 403
    with pytest.raises(HTTPException) as wrong:
        ejecutar_escaneo("wrong")
    assert wrong.value.status_code == 403
    response = ejecutar_escaneo("test-secret")
    assert response["combinaciones_evaluadas"] == 40
    assert set(response) == {"fecha_escaneo", "anio_fiscal", "combinaciones_evaluadas", "alertas_preparadas"}
