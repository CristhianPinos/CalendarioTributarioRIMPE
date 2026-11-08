"""
Router del Flujo Diario Programado y Gestión de Recordatorios con Confirmación Humana.
Asignatura: Ingeniería de Software con IA Generativa
Caso N.º 11 – Grupo 11: Calendario Tributario RIMPE

Provee endpoints para:
1. Disparar la tarea programada diaria de detección de vencimientos.
2. Listar la cola de recordatorios en espera de revisión humana (HITL).
3. Confirmar y enviar recordatorios de forma individual o en lote.
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from datetime import date
from pydantic import BaseModel, Field
from backend.operator_auth import require_operator

from backend.services.scheduler import (
    ejecutar_tarea_diaria_recordatorios,
    listar_recordatorios_pendientes,
    listar_recordatorios_en_revision,
    confirmar_y_despachar_recordatorio,
    EnvioInciertoError,
    ConsentimientoRequeridoError,
    confirmar_todos_los_pendientes,
    RecordatorioColaItem,
    ResumenTareaDiaria
)
from backend.services.agent_service import EnviarRecordatorioOutput

router = APIRouter(
    prefix="/api/flujo",
    tags=["Flujo Programado y Recordatorios HITL"],
    dependencies=[Depends(require_operator)],
)


class EjecutarFlujoRequest(BaseModel):
    fecha_simulada: Optional[str] = Field(
        default=None,
        description="Fecha simulada en formato YYYY-MM-DD para pruebas. Si es None, usa la fecha actual."
    )


class ConfirmarRecordatorioRequest(BaseModel):
    usuario_confirmador: str = Field(
        default="contador_autorizado",
        description="Campo legado ignorado: la identidad se obtiene de la autenticación del operador."
    )


@router.post("/ejecutar-tarea-diaria", response_model=ResumenTareaDiaria)
def endpoint_ejecutar_tarea_diaria(payload: Optional[EjecutarFlujoRequest] = None):
    """
    Dispara la cinta de automatización diaria:
    Escanea contribuyentes, detecta vencimientos próximos (próximos 5 días hábiles),
    redacta los recordatorios con citas normativas y los deja en estado PENDIENTE_CONFIRMACION.
    """
    try:
        f_ref = None
        if payload and payload.fecha_simulada:
            f_ref = date.fromisoformat(payload.fecha_simulada)
        return ejecutar_tarea_diaria_recordatorios(fecha_referencia=f_ref)
    except Exception:
        raise HTTPException(status_code=500, detail="No se pudo ejecutar la tarea diaria.")


@router.get("/recordatorios-pendientes", response_model=List[RecordatorioColaItem])
def endpoint_listar_recordatorios_pendientes():
    """
    Lista todos los recordatorios preparados por la tarea diaria
    que están detenidos en la compuerta humana en espera de aprobación.
    """
    try:
        return listar_recordatorios_pendientes()
    except Exception:
        raise HTTPException(status_code=500, detail="No se pudo consultar la cola de recordatorios.")


@router.get("/recordatorios-en-revision", response_model=List[RecordatorioColaItem])
def endpoint_listar_recordatorios_en_revision():
    """Lista envíos inciertos para verificación manual, sin habilitar el reintento."""
    return listar_recordatorios_en_revision()


@router.post("/confirmar-recordatorio/{id_recordatorio}", response_model=EnviarRecordatorioOutput)
def endpoint_confirmar_recordatorio(
    id_recordatorio: str,
    payload: Optional[ConfirmarRecordatorioRequest] = None,
    operator: str = Depends(require_operator),
):
    """
    Compuerta Humana (HITL): Aprueba y ejecuta el envío del recordatorio indicado.
    Genera un registro de auditoría y cambia el estado a ENVIADO.
    """
    try:
        return confirmar_y_despachar_recordatorio(
            id_recordatorio=id_recordatorio,
            usuario_confirmador=operator
        )
    except EnvioInciertoError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    except ConsentimientoRequeridoError as exc:
        raise HTTPException(status_code=403, detail=str(exc))
    except ValueError:
        raise HTTPException(status_code=404, detail="No se encontró el recordatorio solicitado.")
    except Exception:
        raise HTTPException(status_code=500, detail="No se pudo confirmar el recordatorio.")


@router.post("/confirmar-todos", response_model=List[EnviarRecordatorioOutput])
def endpoint_confirmar_todos(
    payload: Optional[ConfirmarRecordatorioRequest] = None,
    operator: str = Depends(require_operator),
):
    """
    Compuerta Humana (HITL): Aprueba y despacha en lote todos los recordatorios pendientes.
    """
    try:
        return confirmar_todos_los_pendientes(usuario_confirmador=operator)
    except Exception:
        raise HTTPException(status_code=500, detail="No se pudo confirmar la cola de recordatorios.")
