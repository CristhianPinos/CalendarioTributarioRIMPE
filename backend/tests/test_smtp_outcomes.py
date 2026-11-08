"""Resultados reales de SMTP y transiciones de la cola HITL."""

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


def _smtp_env(monkeypatch):
    monkeypatch.setenv("SMTP_HOST", "smtp.test")
    monkeypatch.setenv("SMTP_USER", "operador@example.com")
    monkeypatch.setenv("SMTP_PASSWORD", "clave-de-prueba")


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


def test_without_smtp_is_simulated_and_retryable(monkeypatch, tmp_path):
    for key in ("SMTP_HOST", "SMTP_USER", "SMTP_PASSWORD"):
        monkeypatch.setenv(key, "")
    store = _store(tmp_path)
    result = confirmar_y_despachar_recordatorio("REC-1", "operador", store)
    assert result.estado == "SIMULADO"
    assert "no se envió" in result.mensaje_accion
    item = store.obtener_todos()[0]
    assert item["estado"] == "SIMULADO"
    assert item["fecha_envio"] is None
    assert len(listar_recordatorios_pendientes(store)) == 1


def test_connection_failure_keeps_item_retryable(monkeypatch, tmp_path):
    _smtp_env(monkeypatch)

    def fail_connect(*args, **kwargs):
        raise ConnectionError("SMTP no disponible")

    monkeypatch.setattr("backend.services.agent_service.smtplib.SMTP", fail_connect)
    store = _store(tmp_path)
    first = confirmar_y_despachar_recordatorio("REC-1", "operador", store)
    assert first.estado == "ERROR_ENVIO"
    assert store.obtener_todos()[0]["fecha_envio"] is None
    assert len(listar_recordatorios_pendientes(store)) == 1

    calls = []

    class SMTPFake:
        def __init__(self, *args, **kwargs): pass
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def starttls(self): pass
        def login(self, *args): pass
        def sendmail(self, *args):
            calls.append(args)
            return {}

    monkeypatch.setattr("backend.services.agent_service.smtplib.SMTP", SMTPFake)
    second = confirmar_y_despachar_recordatorio("REC-1", "operador", store)
    third = confirmar_y_despachar_recordatorio("REC-1", "operador", store)
    assert second.estado == third.estado == "ENVIADO"
    assert len(calls) == 1
    assert store.obtener_todos()[0]["fecha_envio"] is not None
    assert listar_recordatorios_pendientes(store) == []


def test_sendmail_exception_is_uncertain_and_never_auto_retried(monkeypatch, tmp_path):
    _smtp_env(monkeypatch)

    class SMTPFake:
        def __init__(self, *args, **kwargs): pass
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def starttls(self): pass
        def login(self, *args): pass
        def sendmail(self, *args): raise TimeoutError("respuesta SMTP perdida")

    monkeypatch.setattr("backend.services.agent_service.smtplib.SMTP", SMTPFake)
    store = _store(tmp_path)
    result = confirmar_y_despachar_recordatorio("REC-1", "operador", store)
    assert result.estado == "ESTADO_INCIERTO"
    assert store.obtener_todos()[0]["estado"] == "ESTADO_INCIERTO"
    assert store.obtener_todos()[0]["fecha_envio"] is None
    assert listar_recordatorios_pendientes(store) == []
    assert len(listar_recordatorios_en_revision(store)) == 1
    with pytest.raises(EnvioInciertoError, match="incierto"):
        confirmar_y_despachar_recordatorio("REC-1", "operador", store)


def test_smtp_acceptance_survives_quit_failure(monkeypatch):
    _smtp_env(monkeypatch)

    class SMTPFake:
        def __init__(self, *args, **kwargs): pass
        def __enter__(self): return self
        def __exit__(self, *args): raise ConnectionError("QUIT falló")
        def starttls(self): pass
        def login(self, *args): pass
        def sendmail(self, *args): return {}

    monkeypatch.setattr("backend.services.agent_service.smtplib.SMTP", SMTPFake)
    assert tool_enviar_recordatorio(_input()).estado == "ENVIADO"
