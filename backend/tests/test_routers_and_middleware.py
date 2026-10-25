"""
Pruebas Unitarias para los Routers FastAPI y el Middleware de Observabilidad LOPDP.
Valida:
1. Funciones de anonimización y enmascaramiento de PII conforme a la LOPDP ecuatoriana.
2. Inyección de cabeceras de auditoría y métricas de latencia (X-Process-Time-Ms).
3. Endpoints de catálogo oficial, simulación de renta y testing 429.
4. Generación pedagógica y validación HTTP 422 ante parámetros incorrectos.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from backend.main import app
from backend.middleware.logging_lopdp import enmascarar_ruc, enmascarar_email, anonimizar_texto


client = TestClient(app)


# ==============================================================================
# 1. PRUEBAS DE ANONIMIZACIÓN LOPDP
# ==============================================================================

class TestAnonimizacionLOPDP:
    """Verifica que el enmascaramiento proteja datos de personas naturales."""

    def test_enmascarar_ruc_valido(self):
        assert enmascarar_ruc("0923456784001") == "0923****001"

    def test_enmascarar_ruc_no_valido(self):
        assert enmascarar_ruc("123") == "***RUC_PROTEGIDO***"
        assert enmascarar_ruc(None) == "***RUC_PROTEGIDO***"

    def test_enmascarar_email(self):
        assert enmascarar_email("juan.perez@empresa.ec") == "j***z@empresa.ec"
        assert enmascarar_email("a@b.com") == "a*@b.com"
        assert enmascarar_email("invalido") == "***EMAIL_PROTEGIDO***"

    def test_anonimizar_texto_complejo(self):
        texto = "El contribuyente con RUC 0923456784001 y correo carlos@test.ec realizó la consulta."
        anonimizado = anonimizar_texto(texto)
        assert "0923****001" in anonimizado
        assert "0923456784001" not in anonimizado
        assert "c***@test.ec" in anonimizado


# ==============================================================================
# 2. PRUEBAS DE MIDDLEWARE Y CABECERAS HTTP
# ==============================================================================

class TestMiddlewareObservabilidad:
    """Verifica que las respuestas incorporen métricas sin alterar el payload."""

    def test_cabeceras_de_auditoria_presentes(self):
        response = client.get("/health")
        assert response.status_code == 200
        assert "X-Process-Time-Ms" in response.headers
        assert response.headers["X-Data-Protection"] == "LOPDP-Ecuador-Compliant"
        latencia = float(response.headers["X-Process-Time-Ms"])
        assert latencia >= 0.0

    def test_health_check_payload(self):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["config_loaded"] is True
        assert "gemini" in data["llm_provider"].lower()


# ==============================================================================
# 3. PRUEBAS DE LOS ENDPOINTS DEL OBLIGACIONES_ROUTER
# ==============================================================================

class TestObligacionesRouter:
    """Verifica los endpoints de negocio expuestos en la API."""

    def test_listar_catalogo_obligaciones(self):
        response = client.get("/api/obligaciones/catalogo")
        assert response.status_code == 200
        data = response.json()
        assert data["total_obligaciones"] >= 5
        codigos = [item["codigo"] for item in data["obligaciones"]]
        assert "IVA_SEMESTRAL_1" in codigos
        assert "RENTA_ANUAL_EMPRENDEDOR" in codigos

    def test_simulador_renta_negocio_popular_exitoso(self):
        payload = {
            "ingresos_brutos": 12000.0,
            "tipo_regimen": "RIMPE_NEGOCIO_POPULAR"
        }
        response = client.post("/api/simulador/renta", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["impuesto_causado"] == 35.0
        assert data["tipo_regimen"] == "RIMPE_NEGOCIO_POPULAR"

    def test_simulador_renta_emprendedor_exitoso(self):
        payload = {
            "ingresos_brutos": 30000.0,
            "tipo_regimen": "RIMPE_EMPRENDEDOR"
        }
        response = client.post("/api/simulador/renta", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["impuesto_causado"] == 160.0
        assert data["fraccion_basica"] == 60.0

    def test_simulador_renta_error_ingresos_negativos(self):
        payload = {
            "ingresos_brutos": -50.0,
            "tipo_regimen": "RIMPE_EMPRENDEDOR"
        }
        response = client.post("/api/simulador/renta", json=payload)
        # Pydantic v2 ge=0.0 valida antes y retorna HTTP 422
        assert response.status_code == 422

    def test_endpoint_simulacion_error_429(self):
        response = client.post("/api/test/simular-error-429")
        assert response.status_code == 429
        data = response.json()
        assert "RATE_LIMIT_EXCEEDED" in str(data)

    def test_explicar_obligacion_exitoso_fallback_o_llm(self):
        payload = {
            "codigo_obligacion": "IVA_SEMESTRAL_1",
            "tipo_regimen": "RIMPE_EMPRENDEDOR",
            "fecha_vencimiento": "2026-07-20",
            "ingresos_estimados": 25000.0,
            "tiene_actividades_excluidas": False
        }
        response = client.post("/api/obligaciones/explicar", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "obligacion" in data
        assert data["obligacion"]["codigo_obligacion"] == "IVA_SEMESTRAL_1"
        assert len(data["obligacion"]["base_legal_oficial"]) > 0

    def test_explicar_obligacion_error_422_fecha_malformada(self):
        payload = {
            "codigo_obligacion": "IVA_SEMESTRAL_1",
            "tipo_regimen": "RIMPE_EMPRENDEDOR",
            "fecha_vencimiento": "fecha-invalida"
        }
        response = client.post("/api/obligaciones/explicar", json=payload)
        assert response.status_code == 422
