"""Calendario diario y activación conservadora del escaneo periódico."""

from datetime import datetime
from types import SimpleNamespace
from zoneinfo import ZoneInfo

import pytest

from backend.services.periodic_scan import PeriodicScanRunner, next_scan_at


ZONE = ZoneInfo("America/Guayaquil")


def test_next_scan_uses_local_day_and_skips_elapsed_time():
    before = datetime(2026, 11, 7, 6, 59, tzinfo=ZONE)
    at_time = datetime(2026, 11, 7, 7, 0, tzinfo=ZONE)
    assert next_scan_at(before, 7, 0) == at_time
    assert next_scan_at(at_time, 7, 0) == datetime(2026, 11, 8, 7, 0, tzinfo=ZONE)


def test_invalid_schedule_is_rejected(monkeypatch):
    monkeypatch.setenv("SCHEDULER_CRON_HOUR", "25")
    with pytest.raises(ValueError, match="hora programada"):
        PeriodicScanRunner()


def test_disabled_runner_never_starts(monkeypatch):
    monkeypatch.setenv("SCHEDULER_ENABLED", "false")
    runner = PeriodicScanRunner()
    runner.start()
    assert runner._thread is None


def test_runner_uses_explicit_empty_profiles_and_local_date(monkeypatch):
    monkeypatch.setenv("SCHEDULER_ENABLED", "true")
    monkeypatch.setenv("SCHEDULER_ALLOW_DEMO_PROFILES", "false")
    monkeypatch.setattr("backend.services.periodic_scan._STORE_GLOBAL", SimpleNamespace(listar_perfiles_consentidos=lambda: []))
    captured = {}

    def fake_scan(**kwargs):
        captured.update(kwargs)
        return SimpleNamespace(
            contribuyentes_evaluados=len(kwargs["contribuyentes"]),
            recordatorios_nuevos_generados=0,
            recordatorios_existentes_omitidos=0,
        )

    monkeypatch.setattr("backend.services.periodic_scan.ejecutar_tarea_diaria_recordatorios", fake_scan)
    runner = PeriodicScanRunner()
    runner.run_once(datetime(2026, 11, 7, 7, 0, tzinfo=ZONE))
    assert captured["contribuyentes"] == []
    assert captured["fecha_referencia"].isoformat() == "2026-11-07"
    assert runner.last_result == "ok"


def test_demo_profiles_require_explicit_opt_in(monkeypatch):
    monkeypatch.setenv("SCHEDULER_ALLOW_DEMO_PROFILES", "false")
    monkeypatch.setattr("backend.services.periodic_scan._STORE_GLOBAL", SimpleNamespace(listar_perfiles_consentidos=lambda: []))
    assert PeriodicScanRunner()._default_contributors() == []
    monkeypatch.setenv("SCHEDULER_ALLOW_DEMO_PROFILES", "true")
    assert len(PeriodicScanRunner()._default_contributors()) > 0


def test_enabled_runner_starts_once_and_stops(monkeypatch):
    monkeypatch.setenv("SCHEDULER_ENABLED", "true")
    runner = PeriodicScanRunner(contributor_provider=lambda: [])
    runner.start()
    first_thread = runner._thread
    assert first_thread is not None and first_thread.is_alive()
    runner.start()
    assert runner._thread is first_thread
    runner.stop()
    assert not first_thread.is_alive()
