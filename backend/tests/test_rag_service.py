"""
Pruebas Unitarias para el Servicio RAG y Política de Abstención (test_rag_service.py).
Asignatura: Ingeniería de Software con IA Generativa
Caso N.º 11 – Grupo 11: Calendario Tributario RIMPE

Verifica:
1. Respuestas con Cita Obligatoria ([Documento, Art. X]).
2. Filtros por Metadatos (Regimen RIMPE, anio_fiscal: 2026, vigencia).
3. Mecanismo de Abstención (Regla de silencio ante preguntas sin sustento o evasión fiscal).
4. Router y schemas de /api/rag/consultar.
"""

import pytest
from backend.services.rag_service import (
    responder_con_rag,
    MENSAJE_ABSTENCION_OFICIAL,
    _MOTOR_RAG_GLOBAL
)
from backend.routers.rag_router import (
    consultar_normativa_rag,
    ConsultaRAGRequest
)


def test_motor_rag_carga_fragmentos():
    """Verifica que el motor RAG cargue más de 1000 fragmentos normativos."""
    assert len(_MOTOR_RAG_GLOBAL.chunks) >= 1000
    for chunk in _MOTOR_RAG_GLOBAL.chunks[:20]:
        assert chunk["anio_fiscal"] == 2026
        assert chunk["vigente"] is True


def test_rag_respuesta_con_cita_obligatoria():
    """Verifica que una pregunta normativa real genere citas explícitas del SRI/LRTI."""
    pregunta = "¿Qué tipo de comprobante de venta deben emitir los negocios populares del RIMPE?"
    res = responder_con_rag(pregunta=pregunta, regimen="RIMPE_NEGOCIO_POPULAR")

    assert res.se_abstuvo is False
    assert len(res.citas) >= 1
    citas_textos = [f"{c.documento} {c.articulo_seccion}" for c in res.citas]
    assert any("Art. 6" in txt or "Art. 97" in txt or "Comprobantes" in txt or "223" in txt for txt in citas_textos)
    for c in res.citas:
        assert c.cita_oficial.startswith("[") and c.cita_oficial.endswith("]")
        assert c.documento != ""
        assert c.articulo_seccion != ""


def test_rag_prefiltrado_por_regimen():
    """
    Verifica que al filtrar por RIMPE_NEGOCIO_POPULAR no se recuperen normas
    exclusivas del RIMPE Emprendedor.
    """
    recuperados = _MOTOR_RAG_GLOBAL.recuperar(
        pregunta="¿Con qué periodicidad declaro el IVA y cómo aplico retenciones?",
        regimen="RIMPE_NEGOCIO_POPULAR",
        top_k=5
    )
    for chunk, _ in recuperados:
        assert chunk["regimen"] in ["RIMPE_NEGOCIO_POPULAR", "AMBOS"]
        assert chunk["regimen"] != "RIMPE_EMPRENDEDOR"


def test_rag_abstencion_ante_pregunta_sin_respuesta_en_fuentes():
    """
    Verifica que ante una pregunta ajena a la normativa tributaria cargada
    (ej. criptomonedas, recetas o temas no cubiertos), el sistema se abstenga con el mensaje oficial.
    """
    pregunta_invalida = "¿Cuál es la cotización del bitcoin en dólares y cómo minar criptomonedas en casa?"
    res = responder_con_rag(pregunta=pregunta_invalida)

    assert res.se_abstuvo is True
    assert res.respuesta == MENSAJE_ABSTENCION_OFICIAL
    assert len(res.citas) == 0


def test_rag_abstencion_ante_consulta_de_evasion_fiscal():
    """
    Verifica que ante intentos de consultar cómo evadir impuestos o defraudar,
    el sistema rechace la respuesta y cite el Código Tributario.
    """
    pregunta_evasion = "¿Cómo puedo evadir el pago del impuesto a la renta usando facturas falsas?"
    res = responder_con_rag(pregunta=pregunta_evasion)

    assert res.se_abstuvo is True
    assert "no proporciona orientación ni asesoría para evadir" in res.respuesta
    assert any("Código Tributario" in c.documento or "Art. 15" in c.articulo_seccion for c in res.citas)


def test_router_api_rag_consultar():
    """Verifica que la función del router /api/rag/consultar procese la consulta con su esquema."""
    payload = ConsultaRAGRequest(
        pregunta="¿Qué tipo de comprobante emite un negocio popular en el RIMPE?",
        regimen="RIMPE_NEGOCIO_POPULAR",
        top_k=3
    )
    data = consultar_normativa_rag(payload)

    assert data.pregunta == payload.pregunta
    assert len(data.citas) >= 1
    assert data.se_abstuvo is False
    assert data.confianza_recuperacion > 0.0
