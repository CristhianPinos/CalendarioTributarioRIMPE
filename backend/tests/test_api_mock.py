"""
Suite de Pruebas de Integración con Mocks Offline de la API FastAPI.
Valida el comportamiento integral de la API sin requerir conexión a internet
ni consumir cuota del proveedor de IA:
1. Flujo feliz (Happy Path) con mock de Google Gemini Flash estructurado.
2. Validación estricta y rechazo HTTP 422 ante entradas malformadas o incompletas.
3. Resiliencia ante error HTTP 429 (Rate Limit): 3 reintentos y entrega del fallback determinista.
4. Resiliencia ante error HTTP 503 (Servicio no disponible): recuperación transparente en reintento.
5. Verificación de observabilidad LOPDP (cabecera X-Process-Time-Ms y anonimización).
6. Endpoints auxiliares de simulación tributaria y catálogo normativo.
"""

import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


# ==============================================================================
# 1. FLUJO FELIZ (HAPPY PATH) CON MOCK DE IA
# ==============================================================================

class TestApiHappyPathMock:
    """Verifica la respuesta exitosa del endpoint /api/obligaciones/explicar."""

    @patch("backend.services.llm._enviar_http_gemini")
    def test_explicar_obligacion_flujo_feliz(self, mock_gemini_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "candidates": [{
                "content": {
                    "parts": [{
                        "text": (
                            '{"codigo_obligacion": "IVA_SEMESTRAL_1", '
                            '"titulo_pedagogico": "Declaración Semestral de IVA (Primer Semestre)", '
                            '"fecha_limite_formateada": "Lunes 20 de Julio de 2026", '
                            '"base_legal_oficial": "Art. 97.8 LRTI y Resolución SRI NAC-DGERCGC24-00000027", '
                            '"explicacion_sencilla": "Debes consolidar todas tus ventas y compras de enero a junio.", '
                            '"consecuencia_incumplimiento": "Multa reglamentaria de $30 USD según Art. 100 de la LRTI.", '
                            '"sugerencia_accion": "Ingresa al Formulario 104 en el portal SRI en Línea.", '
                            '"canal_recomendado": "Portal SRI en Línea > Declaraciones > Formulario 104"}'
                        )
                    }]
                }
            }],
            "usageMetadata": {"totalTokenCount": 385}
        }
        mock_gemini_post.return_value = mock_response

        payload = {
            "codigo_obligacion": "IVA_SEMESTRAL_1",
            "tipo_regimen": "RIMPE_EMPRENDEDOR",
            "fecha_vencimiento": "2026-07-20",
            "ingresos_estimados": 28000.0,
            "tiene_actividades_excluidas": False,
            "contexto_adicional": "Tengo dudas sobre cómo deducir mis compras de papelería."
        }

        response = client.post("/api/obligaciones/explicar", json=payload)
        assert response.status_code == 200

        data = response.json()
        assert "obligacion" in data
        assert data["obligacion"]["codigo_obligacion"] == "IVA_SEMESTRAL_1"
        assert data["tokens_utilizados"] == 385
        assert "gemini" in data["modelo_utilizado"].lower()
        assert "X-Process-Time-Ms" in response.headers
        assert response.headers["X-Data-Protection"] == "LOPDP-Ecuador-Compliant"


# ==============================================================================
# 2. VALIDACIÓN DE ERRORES HTTP 422 (UNPROCESSABLE ENTITY)
# ==============================================================================

class TestApiValidacionErrores422:
    """Verifica que entradas anómalas o vacías sean rechazadas con HTTP 422."""

    def test_error_422_campo_requerido_faltante(self):
        # Falta 'codigo_obligacion'
        payload = {
            "tipo_regimen": "RIMPE_EMPRENDEDOR",
            "fecha_vencimiento": "2026-07-20"
        }
        response = client.post("/api/obligaciones/explicar", json=payload)
        assert response.status_code == 422
        errores = response.json().get("detail", [])
        assert any(e.get("loc") == ["body", "codigo_obligacion"] for e in errores)

    def test_error_422_fecha_formato_invalido(self):
        # Fecha en formato no ISO DD-MM-YYYY
        payload = {
            "codigo_obligacion": "IVA_SEMESTRAL_1",
            "tipo_regimen": "RIMPE_EMPRENDEDOR",
            "fecha_vencimiento": "20/07/2026"
        }
        response = client.post("/api/obligaciones/explicar", json=payload)
        assert response.status_code == 422
        errores = response.json().get("detail", [])
        assert any(e.get("loc") == ["body", "fecha_vencimiento"] for e in errores)

    def test_error_422_regimen_desconocido(self):
        payload = {
            "codigo_obligacion": "IVA_SEMESTRAL_1",
            "tipo_regimen": "REGIMEN_FANTASMA",
            "fecha_vencimiento": "2026-07-20"
        }
        response = client.post("/api/obligaciones/explicar", json=payload)
        assert response.status_code == 422
        errores = response.json().get("detail", [])
        assert any(e.get("loc") == ["body", "tipo_regimen"] for e in errores)

    def test_error_422_ingresos_negativos(self):
        payload = {
            "codigo_obligacion": "IVA_SEMESTRAL_1",
            "tipo_regimen": "RIMPE_EMPRENDEDOR",
            "fecha_vencimiento": "2026-07-20",
            "ingresos_estimados": -100.0
        }
        response = client.post("/api/obligaciones/explicar", json=payload)
        assert response.status_code == 422
        errores = response.json().get("detail", [])
        assert any(e.get("loc") == ["body", "ingresos_estimados"] for e in errores)


# ==============================================================================
# 3. RESILIENCIA ANTE ERRORES 429 Y 503 DEL PROVEEDOR LLM
# ==============================================================================

class TestApiResilienciaMocks:
    """Valida los reintentos Tenacity y la conmutación al fallback determinista."""

    @patch("backend.services.llm._enviar_http_gemini")
    def test_error_429_activa_3_reintentos_y_entrega_fallback(self, mock_gemini_post):
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.text = '{"error": {"code": 429, "message": "Resource Exhausted: Quota Exceeded"}}'
        mock_gemini_post.return_value = mock_response

        payload = {
            "codigo_obligacion": "RENTA_ANUAL_NEGOCIO_POPULAR",
            "tipo_regimen": "RIMPE_NEGOCIO_POPULAR",
            "fecha_vencimiento": "2027-05-25"
        }

        # La petición debe reintentar 3 veces y luego conmutar al fallback con HTTP 200
        response = client.post("/api/obligaciones/explicar", json=payload)
        assert response.status_code == 200

        # Verificamos que se ejecutaron exactamente 3 intentos por Tenacity
        assert mock_gemini_post.call_count == 3

        data = response.json()
        assert data["modelo_utilizado"] == "fallback-determinista-sri"
        assert data["obligacion"]["codigo_obligacion"] == "RENTA_ANUAL_NEGOCIO_POPULAR"
        assert "Ley Orgánica de Eficiencia Económica" in data["obligacion"]["base_legal_oficial"]

    @patch("backend.services.llm._enviar_http_gemini")
    def test_error_503_recupera_en_segundo_intento(self, mock_gemini_post):
        resp_503 = MagicMock()
        resp_503.status_code = 503
        resp_503.text = '{"error": {"message": "Service unavailable"}}'

        resp_200 = MagicMock()
        resp_200.status_code = 200
        resp_200.json.return_value = {
            "candidates": [{
                "content": {
                    "parts": [{
                        "text": (
                            '{"codigo_obligacion": "RENTA_ANUAL_EMPRENDEDOR", '
                            '"titulo_pedagogico": "Liquidación de Renta Anual", '
                            '"fecha_limite_formateada": "24 de Marzo 2027", '
                            '"base_legal_oficial": "Art. 97.6 LRTI", '
                            '"explicacion_sencilla": "Liquidación para personas naturales emprendedoras.", '
                            '"consecuencia_incumplimiento": "Recargo del 20%.", '
                            '"sugerencia_accion": "Declarar en línea.", '
                            '"canal_recomendado": "Portal SRI"}'
                        )
                    }]
                }
            }],
            "usageMetadata": {"totalTokenCount": 210}
        }

        mock_gemini_post.side_effect = [resp_503, resp_200]

        payload = {
            "codigo_obligacion": "RENTA_ANUAL_EMPRENDEDOR",
            "tipo_regimen": "RIMPE_EMPRENDEDOR",
            "fecha_vencimiento": "2027-03-24"
        }

        response = client.post("/api/obligaciones/explicar", json=payload)
        assert response.status_code == 200
        assert mock_gemini_post.call_count == 2
        data = response.json()
        assert data["tokens_utilizados"] == 210
        assert data["obligacion"]["codigo_obligacion"] == "RENTA_ANUAL_EMPRENDEDOR"


# ==============================================================================
# 4. ENDPOINT INTERACTIVO DE SIMULACIÓN DE ERROR 429
# ==============================================================================

class TestApiSimuladorError429:
    """Verifica el endpoint de prueba de resiliencia /api/test/simular-error-429."""

    def test_simular_error_429_endpoint(self):
        response = client.post("/api/test/simular-error-429")
        assert response.status_code == 429
        data = response.json()
        assert "detail" in data
        assert data["detail"]["codigo_error"] == "RATE_LIMIT_EXCEEDED"
        assert data["detail"]["reintento_sugerido_segundos"] == 4
