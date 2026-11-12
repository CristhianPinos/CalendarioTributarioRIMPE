"""Persistencia, migración e idempotencia de la cola SQLite."""

import json
import sqlite3
from datetime import date

import pytest
from fastapi import HTTPException

from backend.services.storage import SQLiteStore
from backend.routers.perfiles_router import PerfilPersistenteRequest, guardar_perfil, obtener_perfil
from backend.services.scheduler import (
    ConsentimientoRequeridoError,
    confirmar_y_despachar_recordatorio,
    ejecutar_tarea_diaria_recordatorios,
)
from backend.routers.agente_router import endpoint_tool_enviar_recordatorio, EnviarRecordatorioInput


def _profile(consent=True):
    return {
        "ruc": "0923456784001", "razon_social": "Contribuyente de prueba",
        "email": "contacto@example.com", "tipo_regimen": "RIMPE_EMPRENDEDOR",
        "anio": 2026, "tiene_actividades_excluidas": False,
        "correo_notificaciones": consent,
    }


def _reminder(state="PENDIENTE_CONFIRMACION"):
    return {
        "id_recordatorio": "REC-PRUEBA", "ruc": "0923456784001",
        "codigo_obligacion": "IVA_SEMESTRAL_1", "fecha_vencimiento": "2026-07-24",
        "estado": state, "email": "contacto@example.com",
    }


def test_legacy_import_copies_source_once_and_keeps_state(tmp_path):
    source = tmp_path / "recordatorios.json"
    original = json.dumps([_reminder("ENVIADO")], ensure_ascii=False)
    source.write_text(original, encoding="utf-8")
    db_path = tmp_path / "rimpe.sqlite3"
    store = SQLiteStore(db_path, source)
    assert not db_path.exists()
    assert store.obtener_todos()[0]["estado"] == "ENVIADO"
    assert source.read_text(encoding="utf-8") == original
    assert source.with_name("recordatorios.json.bak").read_text(encoding="utf-8") == original

    source.write_text("[]", encoding="utf-8")
    restarted = SQLiteStore(db_path, source)
    assert len(restarted.obtener_todos()) == 1
    assert source.with_name("recordatorios.json.bak").read_text(encoding="utf-8") == original


def test_consent_is_opt_in_revocable_and_requires_matching_email(tmp_path):
    store = SQLiteStore(tmp_path / "rimpe.sqlite3", None)
    assert store.listar_perfiles_consentidos() == []
    store.upsert_profile(_profile(False))
    assert not store.has_consent("0923456784001", "contacto@example.com")
    approved = store.upsert_profile(_profile(True))
    assert approved["consent_at"]
    assert store.has_consent("0923456784001", "CONTACTO@example.com")
    assert not store.has_consent("0923456784001", "otro@example.com")
    assert len(SQLiteStore(store.db_path, None).listar_perfiles_consentidos()) == 1
    store.upsert_profile(_profile(False))
    assert store.listar_perfiles_consentidos() == []
    assert not store.has_consent_email("contacto@example.com")
    assert store.get_profile("0923456784001")["consent_at"] is None


def test_unique_reminder_and_atomic_claim_survive_restart(tmp_path):
    store = SQLiteStore(tmp_path / "rimpe.sqlite3", None)
    store.agregar_recordatorio(_reminder())
    store.agregar_recordatorio(_reminder())
    assert len(store.obtener_todos()) == 1
    assert store.reservar_envio("REC-PRUEBA")
    assert not SQLiteStore(store.db_path, None).reservar_envio("REC-PRUEBA")
    assert store.obtener_todos()[0]["estado"] == "EN_PROCESO"
    store.actualizar_estado_envio("REC-PRUEBA", "AUD-1", "operador", "ENVIADO")
    assert SQLiteStore(store.db_path, None).obtener_todos()[0]["estado"] == "ENVIADO"


def test_backup_is_consistent_and_restorable(tmp_path):
    store = SQLiteStore(tmp_path / "rimpe.sqlite3", None)
    store.upsert_profile(_profile())
    store.agregar_recordatorio(_reminder())
    backup = tmp_path / "respaldo.sqlite3"
    store.backup_to(backup)
    restored = SQLiteStore(backup, None)
    assert restored.has_consent("0923456784001", "contacto@example.com")
    assert len(restored.obtener_todos()) == 1
    with sqlite3.connect(backup) as db:
        assert db.execute("PRAGMA integrity_check").fetchone()[0] == "ok"


def test_scan_uses_saved_consent_and_revocation_blocks_dispatch(tmp_path, monkeypatch):
    store = SQLiteStore(tmp_path / "rimpe.sqlite3", None)
    profile = _profile(True)
    store.upsert_profile(profile)
    summary = ejecutar_tarea_diaria_recordatorios(date(2026, 7, 20), store=store)
    assert summary.contribuyentes_evaluados == 1
    assert summary.recordatorios_nuevos_generados > 0
    reminder = summary.recordatorios_preparados[0]

    def unexpected_send(_params):
        raise AssertionError("SMTP no debe ejecutarse sin consentimiento")

    monkeypatch.setattr("backend.services.scheduler.tool_enviar_recordatorio", unexpected_send)
    store.upsert_profile(_profile(False))
    with pytest.raises(ConsentimientoRequeridoError):
        confirmar_y_despachar_recordatorio(reminder.id_recordatorio, "operador", store)
    assert store.obtener_todos()[0]["estado"] == "PENDIENTE_CONFIRMACION"
    assert ejecutar_tarea_diaria_recordatorios(date(2026, 7, 20), store=store).contribuyentes_evaluados == 0


def test_profile_registration_defaults_to_no_mail_consent(tmp_path, monkeypatch):
    store = SQLiteStore(tmp_path / "rimpe.sqlite3", None)
    monkeypatch.setattr("backend.routers.perfiles_router._STORE_GLOBAL", store)
    payload = PerfilPersistenteRequest(**{k: v for k, v in _profile().items() if k != "correo_notificaciones"})
    saved = guardar_perfil(payload)
    assert saved["correo_notificaciones"] is False
    assert obtener_perfil(payload.ruc)["anio"] == 2026
    assert store.listar_perfiles_consentidos() == []


def test_direct_dispatch_requires_verified_email():
    params = EnviarRecordatorioInput(
        destinatario="contacto@example.com", asunto="Aviso tributario",
        texto="Recordatorio de prueba con cita normativa.", confirmacion_usuario=True,
    )
    with pytest.raises(HTTPException) as denied:
        endpoint_tool_enviar_recordatorio(params)
    assert denied.value.status_code == 403


def test_public_demo_rejects_profile_registration(monkeypatch):
    monkeypatch.setenv("RIMPE_DEMO_READONLY", "true")
    payload = PerfilPersistenteRequest(**_profile(True))
    with pytest.raises(HTTPException) as denied:
        guardar_perfil(payload)
    assert denied.value.status_code == 503
