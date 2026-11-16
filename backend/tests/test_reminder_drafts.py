"""Contrato de revisión previa y envío puntual, sin llamadas externas."""

import pytest
from types import SimpleNamespace

from backend.routers import correo_router
from backend.schemas import ExplicacionObligacionRequest, ExplicacionObligacionResponse, PerfilTributarioCreate
from backend.services import mailjet_service
from backend.services.calculator import calcular_vencimientos
from backend.services.llm import obtener_fallback_determinista
from backend.services.reminder_drafts import remember_explanation, prepare_draft


def _case(email="prueba@example.com", zero=False):
    profile = PerfilTributarioCreate(
        ruc="0923456784001", razon_social="Contribuyente sintético",
        tipo_regimen="RIMPE_EMPRENDEDOR", email=email,
    )
    event = next(item for item in calcular_vencimientos(profile.ruc, profile.tipo_regimen.value, 2026)["eventos"]
                 if item["codigo_obligacion"] == "IVA_SEMESTRAL_1")
    request = ExplicacionObligacionRequest(
        codigo_obligacion=event["codigo_obligacion"], tipo_regimen=profile.tipo_regimen,
        fecha_vencimiento=event["fecha_vencimiento"], es_declaracion_en_cero=zero,
    )
    response = ExplicacionObligacionResponse(
        obligacion=obtener_fallback_determinista(
            request.codigo_obligacion, request.fecha_vencimiento, profile.tipo_regimen, zero,
        ),
        fuentes_rag=["[LRTI, Art. 97.8]"], modelo_utilizado="fallback-determinista-sri",
    )
    return profile, event, remember_explanation(request, response)


def test_borrador_reutiliza_explicacion_y_fecha_python():
    profile, event, explanation_id = _case(zero=True)
    draft = prepare_draft(explanation_id, profile, str(profile.email), 2026, event["codigo_obligacion"])
    assert event["fecha_vencimiento"] in draft["asunto"]
    assert event["fecha_vencimiento"] in draft["cuerpo"]
    assert "Resumen explicativo:" in draft["cuerpo"]
    assert "declar" in draft["cuerpo"].lower()
    assert "[LRTI, Art. 97.8]" in draft["cuerpo"]
    assert profile.ruc not in draft["cuerpo"]


def test_borrador_rechaza_cambio_de_destinatario_o_fecha():
    profile, event, explanation_id = _case()
    with pytest.raises(ValueError):
        prepare_draft(explanation_id, profile, str(profile.email), 2027, event["codigo_obligacion"])
    draft = prepare_draft(explanation_id, profile, str(profile.email), 2026, event["codigo_obligacion"])
    data = correo_router.EnviarRecordatorioVerificado(
        email="otro@example.com", codigo="123456", perfil=profile, anio=2026,
        codigo_obligacion=event["codigo_obligacion"], borrador_id=draft["borrador_id"],
        confirmacion_envio=True,
    )
    with pytest.raises(Exception) as error:
        correo_router.enviar_recordatorio(data)
    assert error.value.status_code == 403


def test_envio_verificado_conserva_exactamente_el_texto_revisado(monkeypatch):
    correo_router._pending.clear()
    correo_router._sent.clear()
    correo_router._requests.clear()
    correo_router._global_requests.clear()
    profile, event, explanation_id = _case()
    draft = prepare_draft(explanation_id, profile, str(profile.email), 2026, event["codigo_obligacion"])
    codes = []
    sent = []
    monkeypatch.setattr(correo_router, "_mail_ready", lambda: None)
    monkeypatch.setattr(correo_router, "_send_code", lambda _email, code: codes.append(code))
    monkeypatch.setattr(mailjet_service, "configurado", lambda: True)
    monkeypatch.setattr(mailjet_service, "enviar_correo", lambda *args: sent.append(args) or "synthetic-id")
    correo_router.solicitar_codigo(correo_router.SolicitarCodigo(email=profile.email))
    data = dict(email=profile.email, codigo=codes[0], perfil=profile,
                anio=2026, codigo_obligacion=event["codigo_obligacion"],
                borrador_id=draft["borrador_id"], confirmacion_envio=True)
    result = correo_router.enviar_recordatorio(correo_router.EnviarRecordatorioVerificado(**data))
    assert result.estado_envio == "ENVIADO"
    assert len(sent) == 1
    assert sent[0][1] == draft["asunto"]
    assert sent[0][2] == draft["cuerpo"]
    assert "Contribuyente sintético" not in str(result.trazas_herramientas)
    with pytest.raises(Exception) as error:
        correo_router.enviar_recordatorio(correo_router.EnviarRecordatorioVerificado(**data))
    assert error.value.status_code == 422


def test_sin_fuente_rag_no_se_presenta_texto_como_generado_por_gemini(monkeypatch):
    from backend.services import llm
    profile, event, _ = _case()
    request = ExplicacionObligacionRequest(
        codigo_obligacion=event["codigo_obligacion"], tipo_regimen=profile.tipo_regimen,
        fecha_vencimiento=event["fecha_vencimiento"],
    )
    monkeypatch.setattr(llm, "responder_con_rag", lambda *_args, **_kwargs: SimpleNamespace(citas=[], se_abstuvo=True))
    monkeypatch.setattr(llm, "_invocar_gemini_raw", lambda **_kwargs: pytest.fail("No debe invocarse Gemini sin fuente"))
    answer = llm.generar_explicacion_obligacion(request, api_key="test-key")
    assert answer.modelo_utilizado == "fallback-determinista-sri"
    assert answer.fuentes_rag == []


def test_fecha_inventada_en_narrativa_activa_contingencia(monkeypatch):
    from backend.services import llm
    profile, event, _ = _case()
    request = ExplicacionObligacionRequest(
        codigo_obligacion=event["codigo_obligacion"], tipo_regimen=profile.tipo_regimen,
        fecha_vencimiento=event["fecha_vencimiento"],
    )
    monkeypatch.setattr(llm, "responder_con_rag", lambda *_args, **_kwargs: SimpleNamespace(
        citas=[SimpleNamespace(cita_oficial="[LRTI, Art. 97.8]")], se_abstuvo=False,
        respuesta="LRTI, Art. 97.8: IVA semestral.",
    ))
    generated = obtener_fallback_determinista(request.codigo_obligacion, request.fecha_vencimiento,
                                               profile.tipo_regimen, False).model_dump()
    generated["explicacion_sencilla"] = "Presenta el formulario el 2026-07-01."
    monkeypatch.setattr(llm, "_invocar_gemini_raw", lambda **_kwargs: (generated, 100))
    answer = llm.generar_explicacion_obligacion(request, api_key="test-key")
    assert answer.modelo_utilizado == "fallback-determinista-sri"
    assert "2026-07-01" not in answer.obligacion.explicacion_sencilla
