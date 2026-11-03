"""
Router del Flujo Diario Programado y Gestión de Recordatorios con Confirmación Humana.
Asignatura: Ingeniería de Software con IA Generativa
Caso N.º 11 – Grupo 11: Calendario Tributario RIMPE

Provee endpoints para:
1. Disparar la tarea programada diaria de detección de vencimientos.
2. Listar la cola de recordatorios en espera de revisión humana (HITL).
3. Confirmar y enviar recordatorios de forma individual o en lote.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from datetime import date
from pydantic import BaseModel, Field

from backend.services.scheduler import (
    ejecutar_tarea_diaria_recordatorios,
    listar_recordatorios_pendientes,
    confirmar_y_despachar_recordatorio,
    confirmar_todos_los_pendientes,
    RecordatorioColaItem,
    ResumenTareaDiaria
)
from backend.services.agent_service import EnviarRecordatorioOutput

router = APIRouter(
    prefix="/api/flujo",
    tags=["Flujo Programado y Recordatorios HITL"]
)


class EjecutarFlujoRequest(BaseModel):
    fecha_simulada: Optional[str] = Field(
        default=None,
        description="Fecha simulada en formato YYYY-MM-DD para pruebas. Si es None, usa la fecha actual."
    )


class ConfirmarRecordatorioRequest(BaseModel):
    usuario_confirmador: str = Field(
        default="contador_autorizado",
        description="Identificador del operador, contador o contribuyente que autoriza el despacho"
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en la ejecución de la tarea diaria: {str(e)}")


@router.get("/recordatorios-pendientes", response_model=List[RecordatorioColaItem])
def endpoint_listar_recordatorios_pendientes():
    """
    Lista todos los recordatorios preparados por la tarea diaria
    que están detenidos en la compuerta humana en espera de aprobación.
    """
    try:
        return listar_recordatorios_pendientes()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/confirmar-recordatorio/{id_recordatorio}", response_model=EnviarRecordatorioOutput)
def endpoint_confirmar_recordatorio(
    id_recordatorio: str,
    payload: Optional[ConfirmarRecordatorioRequest] = None
):
    """
    Compuerta Humana (HITL): Aprueba y ejecuta el envío del recordatorio indicado.
    Genera un registro de auditoría y cambia el estado a ENVIADO.
    """
    try:
        usuario = payload.usuario_confirmador if payload else "contador_autorizado"
        return confirmar_y_despachar_recordatorio(
            id_recordatorio=id_recordatorio,
            usuario_confirmador=usuario
        )
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/confirmar-todos", response_model=List[EnviarRecordatorioOutput])
def endpoint_confirmar_todos(payload: Optional[ConfirmarRecordatorioRequest] = None):
    """
    Compuerta Humana (HITL): Aprueba y despacha en lote todos los recordatorios pendientes.
    """
    try:
        usuario = payload.usuario_confirmador if payload else "contador_autorizado"
        return confirmar_todos_los_pendientes(usuario_confirmador=usuario)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
