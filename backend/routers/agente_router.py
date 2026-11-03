"""
Router de Operaciones del Agente Tributario RIMPE.
Asignatura: Ingeniería de Software con IA Generativa
Caso N.º 11 – Grupo 11: Calendario Tributario RIMPE

Expone endpoints para la invocación del agente, llamada individual
a sus 4 herramientas formales y compuerta de confirmación humana (HITL).
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

from backend.services.agent_service import (
    AgenteTributarioRIMPE,
    CalcularVencimientosInput,
    CalcularVencimientosOutput,
    CalcularIVAInput,
    CalcularIVAOutput,
    RedactarRecordatorioInput,
    RedactarRecordatorioOutput,
    EnviarRecordatorioInput,
    EnviarRecordatorioOutput,
    ResultadoAgente,
    tool_calcular_vencimientos,
    tool_calcular_iva,
    tool_redactar_recordatorio,
    tool_enviar_recordatorio
)

router = APIRouter(
    prefix="/api/agente",
    tags=["Agente Tributario"]
)


class InvocacionAgenteRequest(BaseModel):
    instruccion: str = Field(..., description="Instrucción en lenguaje natural para el agente")
    perfil: Dict[str, Any] = Field(..., description="Datos del perfil del contribuyente (RUC, régimen, email)")
    base_imponible_iva: Optional[float] = Field(None, ge=0.0, description="Base imponible para cálculo de IVA opcional")
    confirmacion_envio: bool = Field(default=False, description="True si el usuario autoriza explícitamente el envío")


@router.post("/ejecutar", response_model=ResultadoAgente)
def ejecutar_agente(payload: InvocacionAgenteRequest):
    """
    Ejecuta el ciclo de razonamiento y herramientas del Agente Tributario
    respetando el límite de 5 iteraciones y la compuerta de confirmación humana.
    """
    agente = AgenteTributarioRIMPE()
    resultado = agente.ejecutar(
        instruccion=payload.instruccion,
        perfil=payload.perfil,
        base_imponible_iva=payload.base_imponible_iva,
        confirmacion_envio=payload.confirmacion_envio
    )
    return resultado


@router.post("/herramientas/calcular-vencimientos", response_model=CalcularVencimientosOutput)
def endpoint_tool_calcular_vencimientos(params: CalcularVencimientosInput):
    """Herramienta 1: Cálculo determinista de fechas de vencimiento por noveno dígito de RUC."""
    try:
        return tool_calcular_vencimientos(params)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/herramientas/calcular-iva", response_model=CalcularIVAOutput)
def endpoint_tool_calcular_iva(params: CalcularIVAInput):
    """Herramienta 2: Cálculo determinista de IVA usando tarifas oficiales de config/parametros.yaml."""
    try:
        return tool_calcular_iva(params)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/herramientas/redactar-recordatorio", response_model=RedactarRecordatorioOutput)
def endpoint_tool_redactar_recordatorio(params: RedactarRecordatorioInput):
    """Herramienta 3: Redacción del recordatorio con citas legales obligatorias del motor RAG."""
    try:
        return tool_redactar_recordatorio(params)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/herramientas/enviar-recordatorio", response_model=EnviarRecordatorioOutput)
def endpoint_tool_enviar_recordatorio(params: EnviarRecordatorioInput):
    """
    Herramienta 4: Despacho de recordatorio con compuerta estricta de confirmación humana (HITL).
    """
    try:
        return tool_enviar_recordatorio(params)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
