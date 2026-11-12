"""Evita que datos recibidos aparezcan en logs o respuestas de error."""

import json

import pytest
from fastapi import HTTPException
from fastapi.exceptions import RequestValidationError

from backend.main import safe_validation_error
from backend.middleware.logging_lopdp import anonimizar_texto, anonimizar_traza
from backend.routers import flujo_router, rag_router
from backend.services.agent_service import AgenteTributarioRIMPE, EnviarRecordatorioInput, tool_enviar_recordatorio


RUC = "0923456784001"
EMAIL = "persona.privada@example.com"
CEDULA = "0923456784"


def test_anonimizar_ruc_cedula_y_correo():
    result = anonimizar_texto(f"RUC {RUC}; cédula {CEDULA}; correo {EMAIL}")
    assert RUC not in result
    assert CEDULA not in result
    assert EMAIL not in result
    assert "0923****001" in result
    assert "09******84" in result


def test_agent_trace_hides_identity_and_message_body():
    original = {"ruc": RUC, "razon_social": "Nombre Privado", "email": EMAIL,
                "cuerpo_recordatorio": "Estimado Nombre Privado", "monto_iva": 15.0}
    protected = anonimizar_traza(original)
    assert RUC not in str(protected)
    assert EMAIL not in str(protected)
    assert "Nombre Privado" not in str(protected)
    assert protected["monto_iva"] == 15.0


def test_mailjet_exception_never_logs_personal_data(monkeypatch, caplog):
    from backend.services.mailjet_service import MailjetError
    monkeypatch.setattr("backend.services.agent_service.mailjet_service.configurado", lambda: True)

    def fail_connect(*args, **kwargs):
        raise MailjetError(f"Falló {EMAIL} RUC {RUC}")

    monkeypatch.setattr("backend.services.agent_service.mailjet_service.enviar_correo", fail_connect)
    result = tool_enviar_recordatorio(EnviarRecordatorioInput(
        destinatario=EMAIL, asunto="Recordatorio tributario",
        texto=f"Texto privado del contribuyente {RUC}", confirmacion_usuario=True,
    ))
    assert result.estado == "ERROR_ENVIO"
    assert EMAIL not in caplog.text
    assert RUC not in caplog.text


def test_scheduler_exception_never_logs_ruc(monkeypatch, caplog, tmp_path):
    from backend.services.scheduler import ColaRecordatoriosStore, ejecutar_tarea_diaria_recordatorios

    def fail_calculation(*args, **kwargs):
        raise ValueError(f"Error con RUC {RUC} y correo {EMAIL}")

    monkeypatch.setattr("backend.services.scheduler.tool_calcular_vencimientos", fail_calculation)
    ejecutar_tarea_diaria_recordatorios(
        contribuyentes=[{"ruc": RUC, "tipo_regimen": "RIMPE_EMPRENDEDOR", "email": EMAIL}],
        store=ColaRecordatoriosStore(tmp_path / "cola.json"),
    )
    assert RUC not in caplog.text
    assert EMAIL not in caplog.text


def test_agent_exception_is_generic_in_response_and_log(monkeypatch, caplog):
    def fail_calculation(*args, **kwargs):
        raise ValueError(f"Datos privados {RUC} {EMAIL}")

    monkeypatch.setattr("backend.services.agent_service.tool_calcular_vencimientos", fail_calculation)
    result = AgenteTributarioRIMPE().ejecutar(
        "Preparar", {"ruc": RUC, "tipo_regimen": "RIMPE_EMPRENDEDOR", "email": EMAIL}
    )
    assert result.exito is False
    assert RUC not in result.respuesta_final + caplog.text
    assert EMAIL not in result.respuesta_final + caplog.text


def test_router_internal_error_does_not_echo_exception(monkeypatch):
    def fail(*args, **kwargs):
        raise RuntimeError(f"Datos privados {RUC} {EMAIL}")

    monkeypatch.setattr(flujo_router, "listar_recordatorios_pendientes", fail)
    with pytest.raises(HTTPException) as error:
        flujo_router.endpoint_listar_recordatorios_pendientes()
    assert error.value.status_code == 500
    assert RUC not in error.value.detail
    assert EMAIL not in error.value.detail

    monkeypatch.setattr(rag_router, "responder_con_rag", fail)
    with pytest.raises(HTTPException) as rag_error:
        rag_router.consultar_normativa_rag(type("Payload", (), {"pregunta": "X", "regimen": None, "top_k": 3})())
    assert RUC not in rag_error.value.detail
    assert EMAIL not in rag_error.value.detail


def test_422_response_omits_rejected_input():
    error = RequestValidationError([{
        "loc": ("body", "email"), "msg": f"Correo inválido: {EMAIL}",
        "type": "value_error", "input": EMAIL,
    }])
    with pytest.raises(StopIteration) as completed:
        safe_validation_error(None, error).send(None)
    response = completed.value.value
    body = json.loads(response.body)
    assert response.status_code == 422
    assert body["detail"][0]["loc"] == ["body", "email"]
    assert EMAIL not in response.body.decode()
