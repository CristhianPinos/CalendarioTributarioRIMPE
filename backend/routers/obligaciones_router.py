"""
Router de Obligaciones Tributarias, IA Generativa y Simulación RIMPE.
Expone los endpoints para:
1. Generación de explicaciones pedagógicas con Google Gemini Flash (POST /api/obligaciones/explicar).
2. Simulación determinista de cuotas de impuesto a la renta (POST /api/simulador/renta).
3. Simulación de errores de cuota HTTP 429 para pruebas de resiliencia (POST /api/test/simular-error-429).
4. Catálogo oficial de obligaciones SRI disponibles (GET /api/obligaciones/catalogo).
"""

from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, status, Response
from backend.schemas import (
    ExplicacionObligacionRequest,
    ExplicacionObligacionResponse,
    SimulacionRentaRequest,
    SimulacionRentaResponse
)
from backend.services.llm import generar_explicacion_obligacion, FALLBACK_OBLIGACIONES
from backend.services.calculator import simular_cuota_renta

router = APIRouter(prefix="/api", tags=["Obligaciones & IA"])


@router.post(
    "/obligaciones/explicar",
    response_model=ExplicacionObligacionResponse,
    status_code=status.HTTP_200_OK,
    summary="Genera una explicación pedagógica y fundamentada de una obligación tributaria con IA",
    description=(
        "Recibe los parámetros de una obligación calculada por el motor determinista "
        "y genera una explicación pedagógica con Google Gemini Flash (o fallback oficial SRI ante fallas de red), "
        "validada estrictamente contra el esquema RecordatorioEstructurado."
    )
)
def explicar_obligacion(request: ExplicacionObligacionRequest) -> ExplicacionObligacionResponse:
    """Endpoint que genera la explicación con el modelo generativo."""
    try:
        return generar_explicacion_obligacion(request=request)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error inesperado al procesar la explicación tributaria: {str(exc)}"
        )


@router.post(
    "/simulador/renta",
    response_model=SimulacionRentaResponse,
    status_code=status.HTTP_200_OK,
    summary="Simula la cuota de Impuesto a la Renta según la Ley de Eficiencia Económica",
    description=(
        "Calcula con exactitud matemática el impuesto causado aplicando la tabla del Art. 23 "
        "de la Ley de Eficiencia Económica (R.O. 461) para Negocio Popular o Emprendedor."
    )
)
def calcular_simulacion_renta(request: SimulacionRentaRequest) -> SimulacionRentaResponse:
    """Endpoint para la simulación determinista de cuotas de renta."""
    try:
        resultado = simular_cuota_renta(
            ingresos_brutos=request.ingresos_brutos,
            tipo_regimen=request.tipo_regimen.value
        )
        return SimulacionRentaResponse(**resultado)
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(val_err)
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al calcular la simulación de renta: {str(exc)}"
        )


@router.get(
    "/obligaciones/catalogo",
    status_code=status.HTTP_200_OK,
    summary="Lista el catálogo oficial de códigos de obligaciones tributarias RIMPE",
    description="Devuelve los códigos y títulos de obligaciones normalizados soportados por el sistema."
)
def listar_catalogo_obligaciones() -> Dict[str, Any]:
    """Retorna las obligaciones registradas en el catálogo oficial de contingencia."""
    catalogo = [
        {
            "codigo": k,
            "titulo": v["titulo_pedagogico"],
            "base_legal": v["base_legal_oficial"]
        }
        for k, v in FALLBACK_OBLIGACIONES.items()
    ]
    return {
        "total_obligaciones": len(catalogo),
        "obligaciones": catalogo
    }


@router.post(
    "/test/simular-error-429",
    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
    summary="Simula un error HTTP 429 de límite de tasa para pruebas de resiliencia",
    description=(
        "Endpoint de pruebas para verificar que el cliente web o las herramientas de integración "
        "reaccionen adecuadamente ante saturación de cuota o rate limiting del proveedor de IA."
    )
)
def simular_error_429():
    """Genera deliberadamente una respuesta HTTP 429 Rate Limit Exceeded."""
    raise HTTPException(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        detail={
            "codigo_error": "RATE_LIMIT_EXCEEDED",
            "mensaje": "Simulación forzada: Límite de tasa de solicitudes excedido en el proveedor de IA.",
            "reintento_sugerido_segundos": 4,
            "politica_resiliencia": "Activar fallback determinista SRI de alta disponibilidad."
        }
    )
