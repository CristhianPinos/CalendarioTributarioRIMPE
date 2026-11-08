"""
Pruebas Unitarias para el Flujo Programado Diario y Confirmación Humana (test_scheduler.py).
Asignatura: Ingeniería de Software con IA Generativa
Caso N.º 11 – Grupo 11: Calendario Tributario RIMPE

Verifica:
1. Detección de vencimientos próximos dentro de la ventana de 5 días hábiles.
2. Generación de recordatorios con citas RAG en estado PENDIENTE_CONFIRMACION (Compuerta HITL).
3. Confirmación humana individual y en lote (despacho y cambio de estado a ENVIADO).
4. Idempotencia: re-ejecución de la tarea diaria no duplica recordatorios existentes.
5. Endpoints HTTP del router /api/flujo.
"""

import pytest
from datetime import date
from pathlib import Path
from backend.services.scheduler import (
    ejecutar_tarea_diaria_recordatorios,
    listar_recordatorios_pendientes,
    confirmar_y_despachar_recordatorio,
    confirmar_todos_los_pendientes,
    ColaRecordatoriosStore,
    CONTRIBUYENTES_REGISTRADOS_DEFAULT
)
from backend.services.storage import SQLiteStore
from backend.routers.flujo_router import (
    endpoint_ejecutar_tarea_diaria,
    endpoint_listar_recordatorios_pendientes,
    endpoint_confirmar_recordatorio,
    EjecutarFlujoRequest,
    ConfirmarRecordatorioRequest
)

TEST_DB_PATH = Path("data/processed/test_recordatorios_temp.json")


@pytest.fixture(autouse=True)
def clean_test_store(monkeypatch):
    """Limpia la base de datos temporal antes y después de cada prueba."""
    monkeypatch.setenv("SMTP_HOST", "smtp.test")
    monkeypatch.setenv("SMTP_USER", "operador@example.com")
    monkeypatch.setenv("SMTP_PASSWORD", "clave-de-prueba")

    class SMTPFake:
        def __init__(self, *args, **kwargs): pass
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def starttls(self): pass
        def login(self, *args): pass
        def sendmail(self, *args): return {}

    monkeypatch.setattr("backend.services.agent_service.smtplib.SMTP", SMTPFake)
    store = ColaRecordatoriosStore(TEST_DB_PATH)
    store.limpiar_cola()
    yield store
    store.limpiar_cola()
    if TEST_DB_PATH.exists():
        TEST_DB_PATH.unlink()


def test_flujo_diario_detecta_vencimientos_en_cinco_dias_habiles(clean_test_store):
    """
    Verifica que simulando el 20 de julio de 2026, la tarea detecte los vencimientos
    de IVA semestral de los dígitos 8 (vence 24 de julio) y 0 (vence 28 de julio).
    """
    store = clean_test_store
    # 20 de julio de 2026 es Lunes. El 24 de julio es Viernes (4 días hábiles).
    fecha_simulada = date(2026, 7, 20)
    
    resumen = ejecutar_tarea_diaria_recordatorios(
        fecha_referencia=fecha_simulada,
        contribuyentes=CONTRIBUYENTES_REGISTRADOS_DEFAULT,
        store=store
    )

    assert resumen.vencimientos_detectados >= 1
    assert resumen.recordatorios_nuevos_generados >= 1
    assert len(resumen.recordatorios_preparados) >= 1

    # Verificar que los recordatorios generados estén en estado PENDIENTE_CONFIRMACION
    for r in resumen.recordatorios_preparados:
        assert r.estado == "PENDIENTE_CONFIRMACION"
        assert len(r.citas_normativas) >= 1
        assert "IVA" in r.codigo_obligacion or "2026-07" in r.fecha_vencimiento
        assert r.id_auditoria_envio is None


def test_flujo_diario_idempotencia_no_duplica(clean_test_store):
    """Verifica que ejecutar la tarea diaria dos veces seguidas no genere duplicados."""
    store = clean_test_store
    fecha_simulada = date(2026, 7, 20)

    # Primera ejecución
    res1 = ejecutar_tarea_diaria_recordatorios(
        fecha_referencia=fecha_simulada,
        contribuyentes=CONTRIBUYENTES_REGISTRADOS_DEFAULT,
        store=store
    )
    nuevos_primera = res1.recordatorios_nuevos_generados
    assert nuevos_primera > 0

    # Segunda ejecución idéntica
    res2 = ejecutar_tarea_diaria_recordatorios(
        fecha_referencia=fecha_simulada,
        contribuyentes=CONTRIBUYENTES_REGISTRADOS_DEFAULT,
        store=store
    )
    assert res2.recordatorios_nuevos_generados == 0
    assert res2.recordatorios_existentes_omitidos == nuevos_primera


def test_lista_vacia_no_se_sustituye_por_perfiles_de_demo(clean_test_store):
    resumen = ejecutar_tarea_diaria_recordatorios(
        fecha_referencia=date(2026, 7, 20), contribuyentes=[], store=clean_test_store,
    )
    assert resumen.contribuyentes_evaluados == 0
    assert resumen.recordatorios_nuevos_generados == 0


def test_compuerta_humana_confirmacion_despacho(clean_test_store):
    """
    Verifica el flujo HITL completo:
    1. La tarea genera recordatorios pendientes.
    2. El operador humano confirma un recordatorio específico.
    3. El estado cambia a ENVIADO y se genera id de auditoría LOPDP.
    """
    store = clean_test_store
    fecha_simulada = date(2026, 7, 20)

    resumen = ejecutar_tarea_diaria_recordatorios(
        fecha_referencia=fecha_simulada,
        contribuyentes=CONTRIBUYENTES_REGISTRADOS_DEFAULT,
        store=store
    )
    assert len(resumen.recordatorios_preparados) > 0
    recordatorio_target = resumen.recordatorios_preparados[0]

    # Antes de confirmar: está en pendientes
    pendientes_antes = listar_recordatorios_pendientes(store=store)
    ids_antes = [p.id_recordatorio for p in pendientes_antes]
    assert recordatorio_target.id_recordatorio in ids_antes

    # Acción humana de confirmación
    despacho = confirmar_y_despachar_recordatorio(
        id_recordatorio=recordatorio_target.id_recordatorio,
        usuario_confirmador="contador_juan_perez",
        store=store
    )

    assert despacho.estado == "ENVIADO"
    assert despacho.confirmado is True
    assert despacho.id_registro_auditoria is not None
    assert despacho.usuario_confirmador == "contador_juan_perez"
    stored = next(item for item in store.obtener_todos() if item["id_recordatorio"] == recordatorio_target.id_recordatorio)
    assert stored["usuario_confirmador"] == "contador_juan_perez"

    # Después de confirmar: ya no figura en la lista de pendientes
    pendientes_despues = listar_recordatorios_pendientes(store=store)
    ids_despues = [p.id_recordatorio for p in pendientes_despues]
    assert recordatorio_target.id_recordatorio not in ids_despues


def test_confirmacion_todos_los_pendientes_en_lote(clean_test_store):
    """Verifica la aprobación masiva de la cola de recordatorios pendientes."""
    store = clean_test_store
    fecha_simulada = date(2026, 7, 20)

    ejecutar_tarea_diaria_recordatorios(
        fecha_referencia=fecha_simulada,
        contribuyentes=CONTRIBUYENTES_REGISTRADOS_DEFAULT,
        store=store
    )

    despachos = confirmar_todos_los_pendientes(
        usuario_confirmador="supervisora_tributaria",
        store=store
    )
    assert len(despachos) >= 1
    assert all(d.estado == "ENVIADO" and d.confirmado is True for d in despachos)

    # La cola debe quedar vacía
    assert len(listar_recordatorios_pendientes(store=store)) == 0


def test_router_endpoints_flujo(tmp_path, monkeypatch):
    """Verifica que las funciones del router /api/flujo respondan con sus esquemas tipados."""
    monkeypatch.setattr("backend.services.scheduler._STORE_GLOBAL", SQLiteStore(tmp_path / "rimpe.sqlite3", None))
    # 1. Disparar tarea diaria
    res_tarea = endpoint_ejecutar_tarea_diaria(EjecutarFlujoRequest(fecha_simulada="2026-07-20"))
    assert res_tarea.contribuyentes_evaluados == 0

    # 2. Listar pendientes
    pendientes = endpoint_listar_recordatorios_pendientes()
    assert isinstance(pendientes, list)

    assert pendientes == []
