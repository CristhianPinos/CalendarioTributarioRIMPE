"""Disparador diario del escaneo de vencimientos, sin despacho de correos."""

import logging
import os
import threading
from datetime import datetime, timedelta
from typing import Callable, Optional
from zoneinfo import ZoneInfo

from backend.services.scheduler import (
    CONTRIBUYENTES_REGISTRADOS_DEFAULT,
    _STORE_GLOBAL,
    ejecutar_tarea_diaria_recordatorios,
)

logger = logging.getLogger("rimpe.periodic_scan")


def _enabled(value: str) -> bool:
    return value.lower() in {"1", "true", "yes"}


def next_scan_at(now: datetime, hour: int, minute: int) -> datetime:
    """Calcula la siguiente hora local de ejecución a partir de un reloj con zona."""
    if now.tzinfo is None:
        raise ValueError("El reloj debe incluir zona horaria.")
    if not 0 <= hour <= 23 or not 0 <= minute <= 59:
        raise ValueError("La hora programada no es válida.")
    scheduled = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if scheduled <= now:
        scheduled += timedelta(days=1)
    return scheduled


class PeriodicScanRunner:
    """Ejecuta una vez por día el escaneo usando el calendario local configurado."""

    def __init__(self, contributor_provider: Optional[Callable[[], list]] = None):
        self.enabled = _enabled(os.getenv("SCHEDULER_ENABLED", "false"))
        self.allow_demo = _enabled(os.getenv("SCHEDULER_ALLOW_DEMO_PROFILES", "false"))
        self.hour = int(os.getenv("SCHEDULER_CRON_HOUR", "7"))
        self.minute = int(os.getenv("SCHEDULER_CRON_MINUTE", "0"))
        self.zone = ZoneInfo(os.getenv("TIMEZONE", "America/Guayaquil"))
        next_scan_at(datetime.now(self.zone), self.hour, self.minute)
        self.contributor_provider = contributor_provider or self._default_contributors
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self.last_run_at: Optional[str] = None
        self.last_result: Optional[str] = None

    def _default_contributors(self) -> list:
        return CONTRIBUYENTES_REGISTRADOS_DEFAULT if self.allow_demo else _STORE_GLOBAL.listar_perfiles_consentidos()

    def run_once(self, now: Optional[datetime] = None):
        """Escanea perfiles del proveedor sin aprobar ni enviar recordatorios."""
        local_now = now or datetime.now(self.zone)
        contributors = self.contributor_provider()
        if contributors is None:
            raise ValueError("El proveedor de contribuyentes no devolvió una lista.")
        result = ejecutar_tarea_diaria_recordatorios(
            fecha_referencia=local_now.date(), contribuyentes=contributors,
        )
        self.last_run_at = local_now.isoformat()
        self.last_result = "ok"
        logger.info(
            "Escaneo periódico completado. Evaluados: %s; preparados: %s; omitidos: %s",
            result.contribuyentes_evaluados,
            result.recordatorios_nuevos_generados,
            result.recordatorios_existentes_omitidos,
        )
        return result

    def _loop(self):
        while not self._stop.is_set():
            now = datetime.now(self.zone)
            wait_seconds = (next_scan_at(now, self.hour, self.minute) - now).total_seconds()
            if self._stop.wait(wait_seconds):
                break
            try:
                self.run_once()
            except Exception as exc:
                self.last_run_at = datetime.now(self.zone).isoformat()
                self.last_result = type(exc).__name__
                logger.error("Falló el escaneo periódico: %s", type(exc).__name__)

    def start(self):
        """Inicia un único hilo de escaneo cuando la función está habilitada."""
        if not self.enabled or (self._thread and self._thread.is_alive()):
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, name="rimpe-periodic-scan", daemon=True)
        self._thread.start()
        logger.info("Escaneo periódico habilitado a las %02d:%02d (%s).", self.hour, self.minute, self.zone)

    def stop(self):
        """Detiene el hilo al finalizar el ciclo de vida de FastAPI."""
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=5)
            self._thread = None
