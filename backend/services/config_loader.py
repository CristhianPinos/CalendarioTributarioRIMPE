"""
Módulo Cargador y Validador de Parámetros Tributarios Oficiales (SRI Ecuador).
Asignatura: Ingeniería de Software con IA Generativa
Caso N.º 11 – Grupo 11: Calendario Tributario RIMPE

Cumple con la restricción de diseño:
"Tarifas, umbrales, salario básico o calendarios: NUNCA en el código ni en el prompt."
"""

import os
from pathlib import Path
from typing import Dict, Any, List, Optional
import yaml
import json

CONFIG_DIR = Path(__file__).resolve().parent.parent.parent / "config"
YAML_PATH = CONFIG_DIR / "parametros.yaml"
JSON_PATH = CONFIG_DIR / "sri_rules_2026.json"

_CACHED_CONFIG: Optional[Dict[str, Any]] = None


def get_config_path() -> Path:
    """Retorna la ruta al archivo de parámetros preferente (YAML si existe, sino JSON)."""
    env_path = os.getenv("SRI_CONFIG_PATH")
    if env_path and Path(env_path).exists():
        return Path(env_path)
    if YAML_PATH.exists():
        return YAML_PATH
    if JSON_PATH.exists():
        return JSON_PATH
    raise FileNotFoundError("No se encontró archivo de parámetros en config/ (parametros.yaml o sri_rules_2026.json).")


def load_parametros(reload: bool = False) -> Dict[str, Any]:
    """Carga y parsea la configuración de parámetros oficiales con caché en memoria."""
    global _CACHED_CONFIG
    if _CACHED_CONFIG is not None and not reload:
        return _CACHED_CONFIG

    path = get_config_path()
    with open(path, "r", encoding="utf-8") as f:
        if path.suffix in [".yaml", ".yml"]:
            data = yaml.safe_load(f)
        else:
            data = json.load(f)

    _CACHED_CONFIG = data
    return _CACHED_CONFIG


def get_salario_basico_unificado() -> float:
    """Retorna el Salario Básico Unificado (SBU) vigente configurado."""
    cfg = load_parametros()
    econ = cfg.get("parametros_economicos", {})
    return float(econ.get("salario_basico_unificado_usd", 460.00))


def get_tarifas_iva() -> Dict[str, float]:
    """Retorna el diccionario de tarifas de IVA vigentes configuradas."""
    cfg = load_parametros()
    return cfg.get("tarifas_iva", {
        "general": 0.15,
        "materiales_construccion": 0.05,
        "turismo_feriados": 0.08,
        "tarifa_cero": 0.00,
        "tarifa_vigente_defecto": 0.15
    })


def get_tarifa_iva_vigente(tipo: str = "general") -> float:
    """Obtiene una tarifa específica de IVA según tipo (general, reducida, materiales, cero)."""
    tarifas = get_tarifas_iva()
    if tipo in tarifas:
        return float(tarifas[tipo])
    return float(tarifas.get("tarifa_vigente_defecto", 0.15))


def get_umbrales_rimpe() -> Dict[str, float]:
    """Retorna los límites de ingreso para categorización RIMPE según la LRTI."""
    cfg = load_parametros()
    u = cfg.get("umbrales_rimpe", {})
    # Soportar estructura plana o estructurada de YAML/JSON
    if "negocio_popular" in u and isinstance(u["negocio_popular"], dict):
        return {
            "negocio_popular_max": float(u["negocio_popular"]["ingreso_maximo_usd"]),
            "emprendedor_max": float(u["emprendedor"]["ingreso_maximo_usd"]),
            "regimen_general_min": float(u["regimen_general_exclusion"]["ingreso_minimo_usd"]),
        }
    return {
        "negocio_popular_max": float(u.get("negocio_popular_max_usd", 20000.00)),
        "emprendedor_max": float(u.get("emprendedor_max_usd", 300000.00)),
        "regimen_general_min": float(u.get("excluido_min_usd", 300000.01)),
    }


def get_dias_vencimiento() -> Dict[str, int]:
    """Retorna el mapeo de noveno dígito de RUC al día límite base del mes."""
    cfg = load_parametros()
    return cfg.get("calendario_noveno_digito", {
        "1": 10, "2": 12, "3": 14, "4": 16, "5": 18,
        "6": 20, "7": 22, "8": 24, "9": 26, "0": 28
    })


def get_feriados_2026() -> List[Dict[str, Any]]:
    """Retorna la lista oficial de feriados nacionales del Ecuador para el ejercicio fiscal."""
    cfg = load_parametros()
    return cfg.get("feriados_nacionales_ecuador_2026") or cfg.get("feriados_nacionales_ecuador_fijos", [])


def get_parametros_agente_flujo() -> Dict[str, Any]:
    """Retorna los parámetros de operación del agente y de la cinta diaria."""
    cfg = load_parametros()
    return cfg.get("agente_y_flujo", {
        "umbral_confianza_clasificacion": 0.85,
        "dias_anticipacion_alerta_diaria": 5,
        "max_iteraciones_agente": 5,
        "requiere_confirmacion_humana": True
    })
