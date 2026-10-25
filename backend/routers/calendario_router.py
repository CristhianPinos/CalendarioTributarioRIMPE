"""
Router de Calendario Tributario RIMPE
Asignatura: Ingeniería de Software con IA Generativa
Caso N.º 11 – Grupo 11

Expone los endpoints para:
- Cálculo determinista de vencimientos de obligaciones por noveno dígito y feriados de Ecuador.
- Validación de RUC de personas naturales bajo algoritmo Módulo 10 del SRI.
- Consulta de catálogo oficial de feriados nacionales.
"""

from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from backend.schemas import (
    CalculoVencimientosRequest,
    CalendarioTributarioResponse,
    TipoRegimen
)
from backend.services.calculator import (
    calcular_vencimientos,
    validar_ruc_persona_natural,
    cargar_reglas_sri
)

router = APIRouter(
    prefix="/api",
    tags=["Calendario"]
)


class ValidacionRucRequest(BaseModel):
    """Solicitud rápida para validar sintaxis de RUC."""
    ruc: str = Field(..., description="RUC de persona natural ecuatoriana (13 dígitos).", examples=["0923456784001"])


class ValidacionRucResponse(BaseModel):
    """Respuesta con el resultado de la validación sintáctica de RUC."""
    ruc: str
    valido: bool
    noveno_digito: int | None = None
    codigo_provincia: str | None = None
    mensaje: str


@router.post(
    "/perfil/calcular-vencimientos",
    response_model=CalendarioTributarioResponse,
    status_code=status.HTTP_200_OK,
    summary="Calcular calendario de obligaciones tributarias para contribuyente RIMPE",
    description=(
        "Calcula determinísticamente los vencimientos del ejercicio fiscal aplicando "
        "el noveno dígito del RUC y trasladando automáticamente las fechas que coincidan "
        "con fines de semana o feriados nacionales de Ecuador (LRTI y resoluciones SRI)."
    )
)
async def endpoint_calcular_vencimientos(request: CalculoVencimientosRequest) -> CalendarioTributarioResponse:
    """
    Endpoint principal para calcular el calendario tributario.
    El cálculo es 100% determinista mediante funciones puras de Python.
    """
    try:
        resultado = calcular_vencimientos(
            ruc=request.ruc,
            tipo_regimen=request.tipo_regimen.value if isinstance(request.tipo_regimen, TipoRegimen) else str(request.tipo_regimen),
            anio=request.anio,
            tiene_actividades_excluidas=request.tiene_actividades_excluidas
        )
        return CalendarioTributarioResponse(**resultado)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Error en validación tributaria: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error inesperado al calcular vencimientos: {str(e)}"
        )


@router.post(
    "/calendario/calcular",
    response_model=CalendarioTributarioResponse,
    status_code=status.HTTP_200_OK,
    summary="Alias para cálculo de calendario tributario",
    description="Ruta alternativa idéntica a /api/perfil/calcular-vencimientos para compatibilidad de frontend."
)
async def endpoint_calendario_calcular_alias(request: CalculoVencimientosRequest) -> CalendarioTributarioResponse:
    """Ruta alias para cálculo del calendario tributario."""
    return await endpoint_calcular_vencimientos(request)


@router.post(
    "/perfil/validar-ruc",
    response_model=ValidacionRucResponse,
    status_code=status.HTTP_200_OK,
    summary="Validar sintaxis y Módulo 10 de RUC de persona natural",
    description="Comprueba si un RUC es válido para personas naturales en Ecuador sin calcular calendario."
)
async def endpoint_validar_ruc(request: ValidacionRucRequest) -> ValidacionRucResponse:
    """Valida un RUC de persona natural y retorna metadatos inmediatos."""
    ruc = request.ruc.strip()
    es_valido = validar_ruc_persona_natural(ruc)

    if not es_valido:
        return ValidacionRucResponse(
            ruc=ruc,
            valido=False,
            noveno_digito=None,
            codigo_provincia=None,
            mensaje=(
                "El RUC no es válido. Debe tener 13 dígitos numéricos, provincia válida (01 a 24), "
                "tercer dígito menor a 6, cumplir el algoritmo Módulo 10 y terminar en 001."
            )
        )

    return ValidacionRucResponse(
        ruc=ruc,
        valido=True,
        noveno_digito=int(ruc[8]),
        codigo_provincia=ruc[:2],
        mensaje="RUC válido para persona natural en Ecuador."
    )


@router.get(
    "/calendario/feriados",
    response_model=List[Dict[str, Any]],
    status_code=status.HTTP_200_OK,
    summary="Listar feriados nacionales oficiales de Ecuador",
    description="Retorna el catálogo oficial de días inhábiles y feriados no recuperables configurados para el ejercicio fiscal."
)
async def endpoint_listar_feriados() -> List[Dict[str, Any]]:
    """Retorna la lista de feriados nacionales cargados desde el archivo de configuración desacoplado."""
    reglas = cargar_reglas_sri()
    return reglas.get("feriados_nacionales_ecuador_fijos", [])
