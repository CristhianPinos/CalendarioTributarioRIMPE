"""Resultados de Mailjet y transiciones de la cola HITL histórica."""

from datetime import datetime, timezone

import pytest

from backend.services.agent_service import EnviarRecordatorioInput, tool_enviar_recordatorio
from backend.services.scheduler import (
    ColaRecordatoriosStore, RecordatorioColaItem,
    EnvioInciertoError, confirmar_y_despachar_recordatorio,
    listar_recordatorios_pendientes, listar_recordatorios_en_revision,
)


def _input():
    return EnviarRecordatorioInput(
        destinatario="contribuyente@example.com", asunto="Recordatorio de IVA",
        texto="Presentar declaración [LRTI, Art. 97.6]", confirmacion_usuario=True,
    )


def _mail_env(monkeypatch):
    monkeypatch.setattr("backend.services.agent_service.mailjet_service.configurado", lambda: True)


def _store(tmp_path):
    store = ColaRecordatoriosStore(tmp_path / "cola.json")
    store.agregar_recordatorio(RecordatorioColaItem(
        id_recordatorio="REC-1", ruc="0923456784001", razon_social="Ejemplo",
        email="contribuyente@example.com", tipo_regimen="RIMPE_EMPRENDEDOR",
        codigo_obligacion="IVA_SEMESTRAL_1", titulo_obligacion="IVA",
        fecha_vencimiento="2026-07-24", dias_restantes=4,
        asunto="Recordatorio de IVA", cuerpo_recordatorio="Presentar declaración [LRTI, Art. 97.6]",
        citas_normativas=["[LRTI, Art. 97.6]"],
        fecha_generacion=datetime.now(timezone.utc).isoformat(),
    ))
    return store


def test_without_mailjet_is_simulated_and_retryable(monkeypatch, tmp_path):
    monkeypatch.setattr("backend.services.agent_service.mailjet_service.configurado", lambda: False)
    store = _store(tmp_path)
    result = confirmar_y_despachar_recordatorio("REC-1", "operador", store)
    assert result.estado == "SIMULADO"
    assert "no se envió" in result.mensaje_accion
    item = store.obtener_todos()[0]
    assert item["estado"] == "SIMULADO"
    assert item["fecha_envio"] is None
    assert len(listar_recordatorios_pendientes(store)) == 1


def test_connection_failure_keeps_item_retryable(monkeypatch, tmp_path):
    from backend.services.mailjet_service import MailjetError
    _mail_env(monkeypatch)

    def fail_connect(*args, **kwargs):
        raise MailjetError("Proveedor no disponible")

    monkeypatch.setattr("backend.services.agent_service.mailjet_service.enviar_correo", fail_connect)
    store = _store(tmp_path)
    first = confirmar_y_despachar_recordatorio("REC-1", "operador", store)
    assert first.estado == "ERROR_ENVIO"
    assert store.obtener_todos()[0]["fecha_envio"] is None
    assert len(listar_recordatorios_pendientes(store)) == 1

    calls = []

    def accepted(*args):
        calls.append(args)
        return "12345"
    monkeypatch.setattr("backend.services.agent_service.mailjet_service.enviar_correo", accepted)
    second = confirmar_y_despachar_recordatorio("REC-1", "operador", store)
    third = confirmar_y_despachar_recordatorio("REC-1", "operador", store)
    assert second.estado == third.estado == "ENVIADO"
    assert len(calls) == 1
    assert store.obtener_todos()[0]["fecha_envio"] is not None
    assert listar_recordatorios_pendientes(store) == []


def test_mailjet_timeout_is_uncertain_and_never_auto_retried(monkeypatch, tmp_path):
    from backend.services.mailjet_service import MailjetUncertainError
    _mail_env(monkeypatch)

    def uncertain(*args):
        raise MailjetUncertainError("Respuesta perdida")

    monkeypatch.setattr("backend.services.agent_service.mailjet_service.enviar_correo", uncertain)
    store = _store(tmp_path)
    result = confirmar_y_despachar_recordatorio("REC-1", "operador", store)
    assert result.estado == "ESTADO_INCIERTO"
    assert store.obtener_todos()[0]["estado"] == "ESTADO_INCIERTO"
    assert store.obtener_todos()[0]["fecha_envio"] is None
    assert listar_recordatorios_pendientes(store) == []
    assert len(listar_recordatorios_en_revision(store)) == 1
    with pytest.raises(EnvioInciertoError, match="incierto"):
        confirmar_y_despachar_recordatorio("REC-1", "operador", store)


def test_mailjet_acceptance_reports_sent(monkeypatch):
    _mail_env(monkeypatch)
    monkeypatch.setattr("backend.services.agent_service.mailjet_service.enviar_correo", lambda *args: "12345")
    assert tool_enviar_recordatorio(_input()).estado == "ENVIADO"
