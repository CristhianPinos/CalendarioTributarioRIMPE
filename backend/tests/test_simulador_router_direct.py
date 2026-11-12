"""Comprueba el contrato del endpoint de renta sin depender del cliente ASGI local."""

import pytest
from fastapi import HTTPException

from backend.routers.obligaciones_router import calcular_simulacion_renta
from backend.schemas import SimulacionRentaRequest


def test_endpoint_aplica_tabla_emprendedor_a_negocio_popular_sobre_20k():
    solicitud = SimulacionRentaRequest(
        ingresos_brutos=25000,
        tipo_regimen="RIMPE_NEGOCIO_POPULAR",
    )
    resultado = calcular_simulacion_renta(solicitud)
    assert resultado.impuesto_causado == 110.00
    assert "tabla de Emprendedor" in resultado.alerta_transicion


def test_endpoint_informa_limite_de_regimen_general():
    solicitud = SimulacionRentaRequest(
        ingresos_brutos=300000.01,
        tipo_regimen="RIMPE_NEGOCIO_POPULAR",
    )
    with pytest.raises(HTTPException) as error:
        calcular_simulacion_renta(solicitud)
    assert error.value.status_code == 422
    assert "Régimen General" in error.value.detail
