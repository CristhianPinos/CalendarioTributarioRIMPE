"""
Motor Determinista de Obligaciones y Calendario Tributario RIMPE (SRI Ecuador).
Calcula con exactitud matemática las fechas de vencimiento según el noveno dígito del RUC,
efectuando prórrogas automáticas por fines de semana y feriados nacionales oficiales de Ecuador.
"""

import json
import os
from datetime import date, timedelta
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional


DEFAULT_CONFIG_PATH = Path(__file__).resolve().parent.parent.parent / "config" / "sri_rules_2026.json"


def validar_ruc_persona_natural(ruc: str) -> bool:
    """
    Valida un RUC de persona natural ecuatoriana usando el algoritmo Módulo 10.
    Reglas oficiales del SRI:
    1. Debe tener 13 dígitos numéricos.
    2. Los primeros dos dígitos corresponden al código de provincia (01 a 24).
    3. El tercer dígito debe ser menor a 6 (0 a 5 para personas naturales).
    4. Los dígitos del 1 al 9 se multiplican por los coeficientes [2, 1, 2, 1, 2, 1, 2, 1, 2].
       Si el producto individual es >= 10, se le resta 9.
       Se suman todos los resultados. La decena superior menos la suma debe ser igual al décimo dígito (verificador).
       Si el residuo es 0, el dígito verificador debe ser 0.
    5. Los tres últimos dígitos deben ser 001 (establecimiento principal).
    """
    if not isinstance(ruc, str) or len(ruc) != 13 or not ruc.isdigit():
        return False

    provincia = int(ruc[:2])
    if provincia < 1 or provincia > 24:
        return False

    tercer_digito = int(ruc[2])
    if tercer_digito >= 6:
        return False

    if ruc[10:] != "001":
        return False

    coeficientes = [2, 1, 2, 1, 2, 1, 2, 1, 2]
    suma = 0
    for i in range(9):
        valor = int(ruc[i]) * coeficientes[i]
        if valor >= 10:
            valor -= 9
        suma += valor

    digito_verificador_calculado = (10 - (suma % 10)) % 10
    digito_verificador_real = int(ruc[9])

    return digito_verificador_calculado == digito_verificador_real


def cargar_reglas_sri(config_path: Optional[str] = None) -> Dict[str, Any]:
    """Carga y valida el archivo de parámetros tributarios desacoplado."""
    path = Path(config_path) if config_path else DEFAULT_CONFIG_PATH
    if not path.exists():
        raise FileNotFoundError(f"Archivo de reglas SRI no encontrado en: {path}")

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def es_dia_inhabil(fecha: date, feriados: List[Dict[str, Any]]) -> Tuple[bool, str]:
    """
    Determina si una fecha es día de descanso obligatorio (fin de semana o feriado).
    Conforme al Código Tributario ecuatoriano y normativas del SRI.
    """
    # 5 = Sábado, 6 = Domingo
    if fecha.weekday() == 5:
        return True, "Fin de semana (Sábado)"
    if fecha.weekday() == 6:
        return True, "Fin de semana (Domingo)"

    for feriado in feriados:
        if feriado.get("mes") == fecha.month and feriado.get("dia") == fecha.day:
            return True, f"Feriado nacional: {feriado.get('nombre', 'Descanso obligatorio')}"

    return False, ""


def trasladar_al_siguiente_dia_habil(fecha_nominal: date, feriados: List[Dict[str, Any]]) -> Tuple[date, bool, str]:
    """
    Traslada una fecha al primer día hábil siguiente si coincide con un día inhábil.
    Retorna (fecha_ajustada, fue_trasladada, motivo_traslado).
    """
    fecha_actual = fecha_nominal
    inhabil, primer_motivo = es_dia_inhabil(fecha_actual, feriados)

    if not inhabil:
        return fecha_nominal, False, "NINGUNO"

    # Si es inhábil, avanzamos día a día hasta encontrar un día hábil
    motivos_acumulados = [primer_motivo]
    while True:
        fecha_actual += timedelta(days=1)
        es_in, motivo = es_dia_inhabil(fecha_actual, feriados)
        if not es_in:
            break
        motivos_acumulados.append(motivo)

    motivo_str = " -> ".join(motivos_acumulados)
    return fecha_actual, True, motivo_str


def calcular_vencimientos(
    ruc: str,
    tipo_regimen: str,
    anio: int,
    tiene_actividades_excluidas: bool = False,
    config_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Función central del motor determinista exigida por el caso de estudio.
    Calcula todas las obligaciones tributarias anuales y semestrales del contribuyente
    en base a su noveno dígito de RUC y régimen RIMPE.
    """
    if not validar_ruc_persona_natural(ruc):
        raise ValueError("El RUC ingresado no cumple con el algoritmo Módulo 10 para personas naturales del SRI.")

    regimenes_validos = ["RIMPE_NEGOCIO_POPULAR", "RIMPE_EMPRENDEDOR"]
    if tipo_regimen not in regimenes_validos:
        raise ValueError(f"Tipo de régimen inválido. Debe ser uno de: {regimenes_validos}")

    reglas = cargar_reglas_sri(config_path)
    noveno_digito_str = ruc[8]
    noveno_digito_int = int(noveno_digito_str)

    calendario_digito = reglas.get("calendario_noveno_digito", {})
    dia_base = calendario_digito.get(noveno_digito_str)
    if dia_base is None:
        raise ValueError(f"No existe día base configurado para el noveno dígito '{noveno_digito_str}'")

    feriados = reglas.get("feriados_nacionales_ecuador_fijos", [])
    eventos: List[Dict[str, Any]] = []

    # ==========================================
    # CASO 1: RIMPE EMPRENDEDOR
    # ==========================================
    if tipo_regimen == "RIMPE_EMPRENDEDOR":
        # 1. IVA Semestre 1 (Enero - Junio): Vence en Julio del año en curso
        fecha_nominal_iva1 = date(anio, 7, dia_base)
        fecha_ajustada_iva1, fue_trasladada_iva1, motivo_iva1 = trasladar_al_siguiente_dia_habil(
            fecha_nominal_iva1, feriados
        )
        eventos.append({
            "id": f"evt-iva-sem1-{anio}",
            "codigo_obligacion": "IVA_SEMESTRAL_1",
            "titulo": "Declaración Semestral de IVA (Semestre 1: Ene - Jun)",
            "fecha_vencimiento": fecha_ajustada_iva1.isoformat(),
            "fecha_nominal": fecha_nominal_iva1.isoformat(),
            "fue_trasladada": fue_trasladada_iva1,
            "motivo_traslado": motivo_iva1,
            "categoria": "RIMPE",
            "color_identificador": "#2563eb",
            "formulario_sri": "Formulario 104",
            "descripcion": (
                "Declaración semestral de IVA para RIMPE Emprendedor. Recuerda que si no tuviste "
                "ventas ni compras gravadas, debes presentar la declaración informativa con valores en cero."
            )
        })

        # 2. IVA Semestre 2 (Julio - Diciembre): Vence en Enero del año fiscal siguiente
        fecha_nominal_iva2 = date(anio + 1, 1, dia_base)
        fecha_ajustada_iva2, fue_trasladada_iva2, motivo_iva2 = trasladar_al_siguiente_dia_habil(
            fecha_nominal_iva2, feriados
        )
        eventos.append({
            "id": f"evt-iva-sem2-{anio}",
            "codigo_obligacion": "IVA_SEMESTRAL_2",
            "titulo": "Declaración Semestral de IVA (Semestre 2: Jul - Dic)",
            "fecha_vencimiento": fecha_ajustada_iva2.isoformat(),
            "fecha_nominal": fecha_nominal_iva2.isoformat(),
            "fue_trasladada": fue_trasladada_iva2,
            "motivo_traslado": motivo_iva2,
            "categoria": "RIMPE",
            "color_identificador": "#2563eb",
            "formulario_sri": "Formulario 104",
            "descripcion": "Declaración del segundo semestre de IVA ante el SRI para RIMPE Emprendedor."
        })

        # 3. Impuesto a la Renta Anual Emprendedor (Personas Naturales): Vence en Marzo del año fiscal siguiente
        fecha_nominal_renta = date(anio + 1, 3, dia_base)
        fecha_ajustada_renta, fue_trasladada_renta, motivo_renta = trasladar_al_siguiente_dia_habil(
            fecha_nominal_renta, feriados
        )
        eventos.append({
            "id": f"evt-renta-emp-{anio}",
            "codigo_obligacion": "RENTA_ANUAL_EMPRENDEDOR",
            "titulo": f"Declaración Anual de Impuesto a la Renta (Ejercicio Fiscal {anio})",
            "fecha_vencimiento": fecha_ajustada_renta.isoformat(),
            "fecha_nominal": fecha_nominal_renta.isoformat(),
            "fue_trasladada": fue_trasladada_renta,
            "motivo_traslado": motivo_renta,
            "categoria": "RIMPE",
            "color_identificador": "#1d4ed8",
            "formulario_sri": "Formulario Renta Personas Naturales",
            "descripcion": (
                "Declaración anual y liquidación sobre la base de ingresos brutos gravados "
                "aplicando la tabla progresiva de RIMPE Emprendedor."
            )
        })

    # ==========================================
    # CASO 2: RIMPE NEGOCIO POPULAR
    # ==========================================
    elif tipo_regimen == "RIMPE_NEGOCIO_POPULAR":
        # Los Negocios Populares NO declaran IVA periódico (el IVA está consolidado en la cuota).
        # Declaran únicamente Impuesto a la Renta anual en Mayo del año fiscal siguiente.
        fecha_nominal_renta_np = date(anio + 1, 5, dia_base)
        fecha_ajustada_renta_np, fue_trasladada_renta_np, motivo_renta_np = trasladar_al_siguiente_dia_habil(
            fecha_nominal_renta_np, feriados
        )
        eventos.append({
            "id": f"evt-renta-np-{anio}",
            "codigo_obligacion": "RENTA_ANUAL_NEGOCIO_POPULAR",
            "titulo": f"Declaración Anual Simplificada de Renta (Ejercicio Fiscal {anio})",
            "fecha_vencimiento": fecha_ajustada_renta_np.isoformat(),
            "fecha_nominal": fecha_nominal_renta_np.isoformat(),
            "fue_trasladada": fue_trasladada_renta_np,
            "motivo_traslado": motivo_renta_np,
            "categoria": "RIMPE",
            "color_identificador": "#16a34a",
            "formulario_sri": "Formulario Renta Simplificado RIMPE",
            "descripcion": (
                "Declaración y pago de la cuota anual progresiva ($0 a $60 USD) según la Ley de Eficiencia Económica. "
                "No requiere declaraciones semestrales de IVA."
            )
        })

    # ==========================================
    # CONDICIÓN MIXTA: ACTIVIDADES EXCLUIDAS
    # ==========================================
    if tiene_actividades_excluidas:
        # Se genera advertencia y obligación adicional de IVA semestral bajo Régimen General
        eventos.append({
            "id": f"evt-regimen-general-iva-{anio}",
            "codigo_obligacion": "IVA_REGIMEN_GENERAL_MIXTO",
            "titulo": "Declaración de IVA - Actividades Excluidas (Régimen General)",
            "fecha_vencimiento": eventos[0]["fecha_vencimiento"],
            "fecha_nominal": eventos[0]["fecha_nominal"],
            "fue_trasladada": eventos[0]["fue_trasladada"],
            "motivo_traslado": eventos[0]["motivo_traslado"],
            "categoria": "REGIMEN_GENERAL",
            "color_identificador": "#ea580c",
            "formulario_sri": "Formulario 104 Régimen General",
            "descripcion": (
                "Obligación correspondiente a tus ingresos por actividades excluidas (servicios profesionales, "
                "arriendos, etc.). Debe emitir factura con IVA y declarar de forma diferenciada al RIMPE."
            )
        })

    # Ordenar cronológicamente los eventos
    eventos.sort(key=lambda x: x["fecha_vencimiento"])

    return {
        "ruc": ruc,
        "noveno_digito": noveno_digito_int,
        "tipo_regimen": tipo_regimen,
        "anio_fiscal": anio,
        "tiene_actividades_excluidas": tiene_actividades_excluidas,
        "total_obligaciones": len(eventos),
        "eventos": eventos
    }


def simular_cuota_renta(ingresos_brutos: float, tipo_regimen: str, config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Simula con precisión determinista el impuesto a la renta a pagar según la
    tabla oficial de la Ley Orgánica de Eficiencia Económica y Generación de Empleo (Art. 23).
    """
    if ingresos_brutos < 0:
        raise ValueError("Los ingresos brutos no pueden ser negativos.")

    reglas = cargar_reglas_sri(config_path)

    if tipo_regimen == "RIMPE_NEGOCIO_POPULAR":
        if ingresos_brutos > 20000.00:
            return {
                "tipo_regimen": tipo_regimen,
                "ingresos_brutos": ingresos_brutos,
                "impuesto_causado": 60.00,
                "alerta_transicion": (
                    "Tus ingresos superan los $20.000,00 USD. Para el siguiente ejercicio fiscal "
                    "pasarás automáticamente a RIMPE Emprendedor."
                )
            }

        tabla = reglas.get("tabla_negocio_popular_renta", [])
        for tramo in tabla:
            if tramo["limite_inferior"] <= ingresos_brutos <= tramo["limite_superior"]:
                return {
                    "tipo_regimen": tipo_regimen,
                    "ingresos_brutos": ingresos_brutos,
                    "cuota_fija_usd": tramo["cuota_fija_usd"],
                    "impuesto_causado": tramo["cuota_fija_usd"],
                    "tramo_aplicado": f"${tramo['limite_inferior']} - ${tramo['limite_superior']}"
                }

    elif tipo_regimen == "RIMPE_EMPRENDEDOR":
        if ingresos_brutos > 300000.00:
            raise ValueError(
                "Los ingresos superan el límite máximo de $300.000,00 USD para RIMPE. Corresponde al Régimen General."
            )
        if 0.0 <= ingresos_brutos <= 20000.00:
            return {
                "tipo_regimen": tipo_regimen,
                "ingresos_brutos": ingresos_brutos,
                "fraccion_basica": 60.00,
                "tipo_marginal": "0.0%",
                "impuesto_causado": 60.00,
                "nota": "Ingresos dentro del rango inicial de hasta $20.000,00 USD."
            }
        tabla = reglas.get("tabla_emprendedor_renta", [])
        for tramo in tabla:
            if tramo["limite_inferior"] <= ingresos_brutos <= tramo["limite_superior"]:
                excedente = ingresos_brutos - tramo["limite_inferior"]
                impuesto_marginal = excedente * (tramo["tipo_marginal_porcentaje"] / 100.0)
                impuesto_total = round(tramo["impuesto_fraccion_basica"] + impuesto_marginal, 2)
                return {
                    "tipo_regimen": tipo_regimen,
                    "ingresos_brutos": ingresos_brutos,
                    "fraccion_basica": tramo["impuesto_fraccion_basica"],
                    "tipo_marginal": f"{tramo['tipo_marginal_porcentaje']}%",
                    "impuesto_causado": impuesto_total
                }

    raise ValueError(f"No se pudo calcular la cuota para los ingresos {ingresos_brutos} y régimen {tipo_regimen}")
