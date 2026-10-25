"""
Pruebas de Integración y Validación para calendario_router.py
Asignatura: Ingeniería de Software con IA Generativa
Caso N.º 11 – Grupo 11
"""

import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

# RUCs reales de prueba válidos para personas naturales (Módulo 10)
RUC_GUAYAS_VAL = "0923456784001"    # Noveno dígito: 8
RUC_PICHINCHA_VAL = "1710034065001" # Noveno dígito: 6
RUC_AZUAY_VAL = "0910000009001"     # Noveno dígito: 0


def test_calcular_vencimientos_emprendedor_exitoso():
    """Verifica el cálculo de calendario para RIMPE Emprendedor (3 obligaciones base)."""
    payload = {
        "ruc": RUC_GUAYAS_VAL,
        "tipo_regimen": "RIMPE_EMPRENDEDOR",
        "anio": 2026,
        "tiene_actividades_excluidas": False
    }
    response = client.post("/api/perfil/calcular-vencimientos", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["ruc"] == RUC_GUAYAS_VAL
    assert data["noveno_digito"] == 8
    assert data["tipo_regimen"] == "RIMPE_EMPRENDEDOR"
    assert data["anio_fiscal"] == 2026
    assert data["total_obligaciones"] == 3
    assert len(data["eventos"]) == 3

    codigos = [e["codigo_obligacion"] for e in data["eventos"]]
    assert "IVA_SEMESTRAL_1" in codigos
    assert "IVA_SEMESTRAL_2" in codigos
    assert "RENTA_ANUAL_EMPRENDEDOR" in codigos

    # Verificar cabecera de observabilidad LOPDP
    assert "x-process-time-ms" in response.headers


def test_calcular_vencimientos_negocio_popular_exitoso():
    """Verifica el cálculo para RIMPE Negocio Popular (1 sola obligación anual)."""
    payload = {
        "ruc": RUC_PICHINCHA_VAL,
        "tipo_regimen": "RIMPE_NEGOCIO_POPULAR",
        "anio": 2026,
        "tiene_actividades_excluidas": False
    }
    response = client.post("/api/perfil/calcular-vencimientos", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["noveno_digito"] == 6
    assert data["total_obligaciones"] == 1
    assert data["eventos"][0]["codigo_obligacion"] == "RENTA_ANUAL_NEGOCIO_POPULAR"
    assert data["eventos"][0]["categoria"] == "RIMPE"
    assert "2027-05" in data["eventos"][0]["fecha_vencimiento"]
    assert "progresiva" in data["eventos"][0]["descripcion"].lower()


def test_calcular_vencimientos_actividades_excluidas():
    """Verifica que al marcar actividades excluidas se añada la obligación de IVA Régimen General."""
    payload = {
        "ruc": RUC_GUAYAS_VAL,
        "tipo_regimen": "RIMPE_EMPRENDEDOR",
        "anio": 2026,
        "tiene_actividades_excluidas": True
    }
    response = client.post("/api/perfil/calcular-vencimientos", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["tiene_actividades_excluidas"] is True
    assert data["total_obligaciones"] == 4

    codigos = [e["codigo_obligacion"] for e in data["eventos"]]
    assert "IVA_REGIMEN_GENERAL_MIXTO" in codigos


def test_alias_calendario_calcular():
    """Verifica que el endpoint alternativo /api/calendario/calcular funcione idéntico."""
    payload = {
        "ruc": RUC_AZUAY_VAL,
        "tipo_regimen": "RIMPE_EMPRENDEDOR",
        "anio": 2026
    }
    response = client.post("/api/calendario/calcular", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["noveno_digito"] == 0
    assert len(data["eventos"]) == 3


def test_calcular_vencimientos_ruc_invalido():
    """Verifica que un RUC con Módulo 10 erróneo sea rechazado con HTTP 422."""
    payload = {
        "ruc": "0923456789001",  # Dígito verificador incorrecto
        "tipo_regimen": "RIMPE_EMPRENDEDOR",
        "anio": 2026
    }
    response = client.post("/api/perfil/calcular-vencimientos", json=payload)
    assert response.status_code == 422
    assert "detail" in response.json()


def test_calcular_vencimientos_regimen_invalido():
    """Verifica que un régimen inexistente sea rechazado con HTTP 422."""
    payload = {
        "ruc": RUC_GUAYAS_VAL,
        "tipo_regimen": "REGIMEN_INEXISTENTE",
        "anio": 2026
    }
    response = client.post("/api/perfil/calcular-vencimientos", json=payload)
    assert response.status_code == 422


def test_validar_ruc_endpoint_valido():
    """Verifica la validación rápida de RUC exitosa."""
    payload = {"ruc": RUC_GUAYAS_VAL}
    response = client.post("/api/perfil/validar-ruc", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["valido"] is True
    assert data["noveno_digito"] == 8
    assert data["codigo_provincia"] == "09"


def test_validar_ruc_endpoint_invalido():
    """Verifica la validación rápida de RUC inválido."""
    payload = {"ruc": "1111111111001"}
    response = client.post("/api/perfil/validar-ruc", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["valido"] is False
    assert data["noveno_digito"] is None


def test_listar_feriados_endpoint():
    """Verifica que se devuelva la lista de feriados nacionales 2026."""
    response = client.get("/api/calendario/feriados")
    assert response.status_code == 200
    feriados = response.json()
    assert isinstance(feriados, list)
    assert len(feriados) > 0

    nombres = [f["nombre"] for f in feriados]
    assert any("Batalla de Pichincha" in n for n in nombres)
