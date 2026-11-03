"""
Pruebas Unitarias para el Cargador de Parámetros Oficiales (config_loader.py)
Asignatura: Ingeniería de Software con IA Generativa
Caso N.º 11 – Grupo 11: Calendario Tributario RIMPE

Verifica el cumplimiento de la restricción:
"Tarifas, umbrales, salario básico o calendarios: nunca en el código ni en el prompt."
"""

import pytest
from pathlib import Path
from backend.services.config_loader import (
    load_parametros,
    get_salario_basico_unificado,
    get_tarifas_iva,
    get_tarifa_iva_vigente,
    get_umbrales_rimpe,
    get_dias_vencimiento,
    get_feriados_2026,
    get_parametros_agente_flujo,
    get_config_path
)


def test_archivo_configuracion_existe():
    """Verifica que el archivo de configuración preferente exista."""
    path = get_config_path()
    assert path.exists()
    assert path.suffix in [".yaml", ".yml", ".json"]


def test_carga_parametros_completa():
    """Verifica que la estructura de configuración contenga todas las secciones requeridas."""
    cfg = load_parametros(reload=True)
    assert "version" in cfg
    assert "fuentes" in cfg or "fuentes_legales" in cfg
    assert "calendario_noveno_digito" in cfg


def test_salario_basico_unificado():
    """Verifica que el SBU configurado sea exactamente 460.00 USD."""
    sbu = get_salario_basico_unificado()
    assert sbu == 460.00
    assert isinstance(sbu, float)


def test_tarifas_iva_oficiales():
    """Verifica las tarifas de IVA oficiales de Ecuador configuradas."""
    tarifas = get_tarifas_iva()
    assert tarifas["general"] == 0.15
    assert tarifas["materiales_construccion"] == 0.05
    assert tarifas["tarifa_cero"] == 0.00
    assert get_tarifa_iva_vigente("general") == 0.15
    assert get_tarifa_iva_vigente("materiales_construccion") == 0.05
    assert get_tarifa_iva_vigente("inexistente") == 0.15  # Fallback por defecto


def test_umbrales_rimpe():
    """Verifica los umbrales de categorización del RIMPE según Art. 97.3 LRTI."""
    umbrales = get_umbrales_rimpe()
    assert umbrales["negocio_popular_max"] == 20000.00
    assert umbrales["emprendedor_max"] == 300000.00
    assert umbrales["regimen_general_min"] == 300000.01


def test_calendario_noveno_digito():
    """Verifica el calendario oficial de días hábiles base por noveno dígito del SRI."""
    dias = get_dias_vencimiento()
    assert len(dias) == 10
    assert dias["1"] == 10
    assert dias["2"] == 12
    assert dias["8"] == 24
    assert dias["0"] == 28


def test_feriados_nacionales_2026():
    """Verifica que los feriados nacionales del Ecuador estén registrados."""
    feriados = get_feriados_2026()
    assert len(feriados) >= 8
    nombres = [f["nombre"] for f in feriados]
    assert any("Batalla de Pichincha" in n for n in nombres)
    assert any("Navidad" in n for n in nombres)


def test_parametros_agente_flujo():
    """Verifica los umbrales operativos del agente y de la tarea diaria programada."""
    params = get_parametros_agente_flujo()
    assert params["umbral_confianza_clasificacion"] == 0.85
    assert params["dias_anticipacion_alerta_diaria"] == 5
    assert params["max_iteraciones_agente"] == 5
    assert params["requiere_confirmacion_humana"] is True
