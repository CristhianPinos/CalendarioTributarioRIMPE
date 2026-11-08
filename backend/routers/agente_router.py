"""
Router de Operaciones del Agente Tributario RIMPE.
Asignatura: Ingeniería de Software con IA Generativa
Caso N.º 11 – Grupo 11: Calendario Tributario RIMPE

Expone endpoints para la invocación del agente, llamada individual
a sus 4 herramientas formales y compuerta de confirmación humana (HITL).
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from backend.operator_auth import optional_operator, require_dispatch_operator
from backend.services.scheduler import _STORE_GLOBAL

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
def ejecutar_agente(payload: InvocacionAgenteRequest, operator: Optional[str] = Depends(optional_operator)):
    """
    Ejecuta el ciclo de razonamiento y herramientas del Agente Tributario
    respetando el límite de 5 iteraciones y la compuerta de confirmación humana.
    """
    if payload.confirmacion_envio:
        require_dispatch_operator(operator)
        perfil = payload.perfil
        if not _STORE_GLOBAL.has_consent(str(perfil.get("ruc", "")), str(perfil.get("email", ""))):
            raise HTTPException(status_code=403, detail="El perfil no autoriza recordatorios para el destinatario actual.")
    agente = AgenteTributarioRIMPE()
    resultado = agente.ejecutar(
        instruccion=payload.instruccion,
        perfil=payload.perfil,
        base_imponible_iva=payload.base_imponible_iva,
        confirmacion_envio=payload.confirmacion_envio
    )
    if payload.confirmacion_envio:
        resultado = resultado.model_copy(update={"usuario_confirmador": operator})
    return resultado


@router.post("/herramientas/calcular-vencimientos", response_model=CalcularVencimientosOutput)
def endpoint_tool_calcular_vencimientos(params: CalcularVencimientosInput):
    """Herramienta 1: Cálculo determinista de fechas de vencimiento por noveno dígito de RUC."""
    try:
        return tool_calcular_vencimientos(params)
    except Exception:
        raise HTTPException(status_code=400, detail="No se pudieron calcular los vencimientos con los datos proporcionados.")


@router.post("/herramientas/calcular-iva", response_model=CalcularIVAOutput)
def endpoint_tool_calcular_iva(params: CalcularIVAInput):
    """Herramienta 2: Cálculo determinista de IVA usando tarifas oficiales de config/parametros.yaml."""
    try:
        return tool_calcular_iva(params)
    except Exception:
        raise HTTPException(status_code=400, detail="No se pudo calcular el IVA con los datos proporcionados.")


@router.post("/herramientas/redactar-recordatorio", response_model=RedactarRecordatorioOutput)
def endpoint_tool_redactar_recordatorio(params: RedactarRecordatorioInput):
    """Herramienta 3: Redacción del recordatorio con citas legales obligatorias del motor RAG."""
    try:
        return tool_redactar_recordatorio(params)
    except Exception:
        raise HTTPException(status_code=400, detail="No se pudo redactar el recordatorio.")


@router.post("/herramientas/enviar-recordatorio", response_model=EnviarRecordatorioOutput)
def endpoint_tool_enviar_recordatorio(params: EnviarRecordatorioInput, operator: Optional[str] = Depends(optional_operator)):
    """
    Herramienta 4: Despacho de recordatorio con compuerta estricta de confirmación humana (HITL).
    """
    if params.confirmacion_usuario:
        require_dispatch_operator(operator)
        if not _STORE_GLOBAL.has_consent_email(str(params.destinatario)):
            raise HTTPException(status_code=403, detail="El perfil no autoriza recordatorios para el destinatario actual.")
    try:
        result = tool_enviar_recordatorio(params)
        if params.confirmacion_usuario:
            result = result.model_copy(update={"usuario_confirmador": operator})
        return result
    except Exception:
        raise HTTPException(status_code=400, detail="No se pudo procesar el despacho del recordatorio.")
