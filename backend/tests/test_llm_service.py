"""
Pruebas Unitarias para el Servicio de Integración con LLM y Resiliencia Tenacity.
Valida:
1. Activación del fallback determinista oficial sin clave o ante fallas externas.
2. Contrato de RecordatorioEstructurado servido desde el fallback para las 5 obligaciones clave.
3. Comportamiento de reintento exponencial con Tenacity ante errores HTTP 429 y 503.
4. Parsing y construcción exitosa de la respuesta estructurada sin dependencias de red en tests (Mocking).
"""

import pytest
from unittest.mock import patch, MagicMock
import httpx
from backend.schemas import (
    TipoRegimen,
    ExplicacionObligacionRequest,
    RecordatorioEstructurado
)
from backend.services.llm import (
    generar_explicacion_obligacion,
    obtener_fallback_determinista,
    GeminiRateLimitException,
    GeminiServiceUnavailableException,
    _invocar_gemini_raw,
    FALLBACK_OBLIGACIONES
)


class TestFallbackDeterminista:
    """Verifica que el catálogo determinista garantice alta disponibilidad sin IA."""

    @pytest.mark.parametrize("codigo", [
        "IVA_SEMESTRAL_1",
        "IVA_SEMESTRAL_2",
        "RENTA_ANUAL_EMPRENDEDOR",
        "RENTA_ANUAL_NEGOCIO_POPULAR",
        "IVA_REGIMEN_GENERAL_MIXTO"
    ])
    def test_catalogo_fallback_cubre_obligaciones_principales(self, codigo):
        assert codigo in FALLBACK_OBLIGACIONES
        plantilla = FALLBACK_OBLIGACIONES[codigo]
        assert "LRTI" in plantilla["base_legal_oficial"] or "Ley" in plantilla["base_legal_oficial"]
        assert len(plantilla["explicacion_sencilla"]) > 50

    def test_obtener_fallback_retorna_recordatorio_valido(self):
        rec = obtener_fallback_determinista(
            codigo_obligacion="IVA_SEMESTRAL_1",
            fecha_vencimiento="2026-07-20",
            tipo_regimen=TipoRegimen.RIMPE_EMPRENDEDOR
        )
        assert isinstance(rec, RecordatorioEstructurado)
        assert rec.codigo_obligacion == "IVA_SEMESTRAL_1"
        assert "2026-07-20" in rec.fecha_limite_formateada
        assert "Formulario 104" in rec.sugerencia_accion or "Formulario 104" in rec.canal_recomendado

    def test_servicio_usa_fallback_si_no_hay_api_key(self):
        req = ExplicacionObligacionRequest(
            codigo_obligacion="RENTA_ANUAL_NEGOCIO_POPULAR",
            tipo_regimen=TipoRegimen.RIMPE_NEGOCIO_POPULAR,
            fecha_vencimiento="2027-05-25"
        )
        # Pasamos api_key vacía explícitamente
        resp = generar_explicacion_obligacion(request=req, api_key="")
        assert resp.modelo_utilizado == "fallback-determinista-sri"
        assert resp.obligacion.codigo_obligacion == "RENTA_ANUAL_NEGOCIO_POPULAR"
        assert resp.tokens_utilizados == 0


class TestTenacityResilience:
    """Verifica la lógica de backoff y tolerancia a fallos de Tenacity."""

    @patch("backend.services.llm._enviar_http_gemini")
    def test_reintento_ante_error_429_y_fallback_final(self, mock_post):
        # Simulamos que Gemini siempre devuelve HTTP 429
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.text = '{"error": {"code": 429, "message": "Rate limit exceeded"}}'
        mock_post.return_value = mock_response

        req = ExplicacionObligacionRequest(
            codigo_obligacion="IVA_SEMESTRAL_1",
            tipo_regimen=TipoRegimen.RIMPE_EMPRENDEDOR,
            fecha_vencimiento="2026-07-20"
        )

        # Debe reintentar 3 veces y luego entregar el fallback determinista
        resp = generar_explicacion_obligacion(request=req, api_key="fake-key-for-test")

        assert mock_post.call_count == 3
        assert resp.modelo_utilizado == "fallback-determinista-sri"
        assert resp.obligacion.codigo_obligacion == "IVA_SEMESTRAL_1"

    @patch("backend.services.llm._enviar_http_gemini")
    def test_reintento_ante_error_503_y_recuperacion(self, mock_post):
        # 1er llamado: 503, 2do llamado: 200 OK
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
                            '{"codigo_obligacion": "IVA_SEMESTRAL_1", '
                            '"titulo_pedagogico": "Declaración IVA Semestre 1", '
                            '"fecha_limite_formateada": "20 de Julio 2026", '
                            '"base_legal_oficial": "Art. 97.8 LRTI", '
                            '"explicacion_sencilla": "Reporte de ventas de enero a junio.", '
                            '"consecuencia_incumplimiento": "Multa formal.", '
                            '"sugerencia_accion": "Declarar en formulario 104.", '
                            '"canal_recomendado": "SRI en Línea"}'
                        )
                    }]
                }
            }],
            "usageMetadata": {"totalTokenCount": 240}
        }

        mock_post.side_effect = [resp_503, resp_200]

        req = ExplicacionObligacionRequest(
            codigo_obligacion="IVA_SEMESTRAL_1",
            tipo_regimen=TipoRegimen.RIMPE_EMPRENDEDOR,
            fecha_vencimiento="2026-07-20"
        )

        resp = generar_explicacion_obligacion(request=req, api_key="fake-key-for-test")

        # Tuvo que llamar 2 veces (falló 1ra, recuperó 2da)
        assert mock_post.call_count == 2
        assert resp.modelo_utilizado != "fallback-determinista-sri"
        assert resp.tokens_utilizados == 240
        assert resp.obligacion.titulo_pedagogico == "Declaración IVA Semestre 1"


class TestInvocacionExitosa:
    """Verifica el flujo feliz cuando Gemini responde correctamente."""

    @patch("backend.services.llm._enviar_http_gemini")
    def test_flujo_feliz_con_parsing_estructurado(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "candidates": [{
                "content": {
                    "parts": [{
                        "text": (
                            '{"codigo_obligacion": "RENTA_ANUAL_EMPRENDEDOR", '
                            '"titulo_pedagogico": "Impuesto a la Renta Ejercicio Fiscal", '
                            '"fecha_limite_formateada": "24 de Marzo 2027", '
                            '"base_legal_oficial": "Ley de Eficiencia Económica y LRTI", '
                            '"explicacion_sencilla": "Liquidación anual obligatoria con tabla progresiva.", '
                            '"consecuencia_incumplimiento": "Recargo del 20% más intereses de mora.", '
                            '"sugerencia_accion": "Ingresa al Formulario de Renta.", '
                            '"canal_recomendado": "Portal SRI en Línea"}'
                        )
                    }]
                }
            }],
            "usageMetadata": {"totalTokenCount": 512}
        }
        mock_post.return_value = mock_response

        req = ExplicacionObligacionRequest(
            codigo_obligacion="RENTA_ANUAL_EMPRENDEDOR",
            tipo_regimen=TipoRegimen.RIMPE_EMPRENDEDOR,
            fecha_vencimiento="2027-03-24",
            ingresos_estimados=35000.0
        )

        resp = generar_explicacion_obligacion(request=req, api_key="test-key")

        assert resp.obligacion.codigo_obligacion == "RENTA_ANUAL_EMPRENDEDOR"
        assert resp.tokens_utilizados == 512
        assert resp.tiempo_generacion_ms > 0
        assert isinstance(resp.obligacion, RecordatorioEstructurado)
