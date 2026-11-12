"""
Script Formal de Evaluación de Calidad, Agente y RAG (Semana 3)
Caso N.º 11 – Grupo 11: Calendario Tributario Personalizado para Emprendedores RIMPE
Asignatura: Ingeniería de Software con IA Generativa - UNIANDES (Octubre 2026)

Evalúa de forma reproducible:
1. 10 Perfiles de Referencia (Dígitos 0-9, Negocio Popular, Emprendedor, Actividades Excluidas)
   verificando precisión exacta de fechas de vencimiento con traslados de feriados y fines de semana.
2. 20 Preguntas Normativas (16 con sustento legal + 4 casos de abstención obligatoria)
   midiendo Hit@3, Citas Obligatorias y Matriz de Confusión de Abstención.
3. Exporta métricas consolidadas sin reemplazar la evidencia histórica de Render.
"""

import os
import sys
import json
import re
import unicodedata
import logging
import argparse
import time
import math
from statistics import median
from datetime import datetime, timezone
from typing import Dict, Any, List
from types import SimpleNamespace

import requests

# Asegurar path al backend
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.services.agent_service import tool_calcular_vencimientos, CalcularVencimientosInput
from backend.services.rag_service import responder_con_rag, ConsultaRAGResponse

logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")
logger = logging.getLogger("evaluacion_rimpe")

DATASET_PATH = os.path.join(os.path.dirname(__file__), "dataset_evaluacion.json")
RESULTADOS_PATH = os.path.join(os.path.dirname(__file__), "resultados_reproduccion_local.json")
BASE_URL = None
LATENCIES = {"calculo": [], "rag": []}


def latency_summary(values):
    ordered = sorted(values)
    if not ordered:
        return {"p50_ms": None, "p95_ms": None}
    return {
        "p50_ms": round(median(ordered), 2),
        "p95_ms": round(ordered[math.ceil(len(ordered) * 0.95) - 1], 2),
    }


def calcular_perfil(params):
    """Ejecuta el cálculo local o consulta la API desplegada."""
    started = time.perf_counter()
    try:
        if BASE_URL is None:
            return tool_calcular_vencimientos(params)
        response = requests.post(
            BASE_URL + "/api/perfil/calcular-vencimientos",
            json=params.model_dump(), timeout=90,
        )
        response.raise_for_status()
        return SimpleNamespace(**response.json())
    finally:
        LATENCIES["calculo"].append((time.perf_counter() - started) * 1000)


def consultar_rag(pregunta, regimen, top_k):
    """Consulta el RAG local o la API desplegada con el mismo dataset."""
    started = time.perf_counter()
    try:
        if BASE_URL is None:
            return responder_con_rag(pregunta=pregunta, regimen=regimen, top_k=top_k)
        response = requests.post(
            BASE_URL + "/api/rag/consultar",
            json={"pregunta": pregunta, "regimen": regimen, "top_k": top_k}, timeout=90,
        )
        response.raise_for_status()
        return ConsultaRAGResponse.model_validate(response.json())
    finally:
        LATENCIES["rag"].append((time.perf_counter() - started) * 1000)


def evaluar_perfiles_referencia(perfiles: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Evalúa la exactitud matemática y legal del cálculo de vencimientos
    sobre los 10 perfiles dorados del SRI para el año fiscal 2026.
    """
    total_perfiles = len(perfiles)
    aciertos_completos = 0
    total_fechas_esperadas = 0
    fechas_coincidentes = 0
    detalles = []

    for perfil in perfiles:
        p_id = perfil["id"]
        ruc = perfil["ruc"]
        digito = perfil["digito"]
        tipo_regimen = perfil["tipo_regimen"]
        anio = perfil["anio"]
        excluidas = perfil.get("tiene_actividades_excluidas", False)
        fechas_esperadas = perfil["fechas_esperadas"]

        params = CalcularVencimientosInput(
            ruc=ruc,
            tipo_regimen=tipo_regimen,
            anio=anio,
            tiene_actividades_excluidas=excluidas
        )
        res = calcular_perfil(params)
        fechas_calculadas = {ev["codigo_obligacion"]: ev["fecha_vencimiento"] for ev in res.eventos}

        # Comparar con esperadas
        discrepancias = {}
        perfil_ok = True
        for obligacion, f_esp in fechas_esperadas.items():
            total_fechas_esperadas += 1
            f_calc = fechas_calculadas.get(obligacion)
            if f_calc == f_esp:
                fechas_coincidentes += 1
            else:
                perfil_ok = False
                discrepancias[obligacion] = {
                    "esperada": f_esp,
                    "calculada": f_calc
                }

        for obligacion, f_calc in fechas_calculadas.items():
            if obligacion not in fechas_esperadas:
                perfil_ok = False
                discrepancias[obligacion] = {
                    "esperada": None,
                    "calculada": f_calc
                }

        if perfil_ok and len(discrepancias) == 0:
            aciertos_completos += 1

        detalles.append({
            "id": p_id,
            "razon_social": perfil["razon_social"],
            "digito": digito,
            "regimen": tipo_regimen,
            "excluidas": excluidas,
            "fechas_esperadas": fechas_esperadas,
            "fechas_calculadas": fechas_calculadas,
            "coincidencia_exacta": perfil_ok,
            "discrepancias": discrepancias,
            "motivo_traslado": perfil.get("motivo_esperado", "")
        })

    precision_perfiles = round((aciertos_completos / total_perfiles) * 100, 2)
    precision_fechas = round((fechas_coincidentes / total_fechas_esperadas) * 100, 2)

    return {
        "total_perfiles": total_perfiles,
        "aciertos_perfiles_completos": aciertos_completos,
        "precision_perfiles_pct": precision_perfiles,
        "total_fechas_esperadas": total_fechas_esperadas,
        "fechas_coincidentes": fechas_coincidentes,
        "precision_fechas_pct": precision_fechas,
        "detalles": detalles
    }


def _articulo_sin_parte(texto: str) -> str:
    return re.sub(r"\s*\(Parte\s+\d+\)$", "", texto, flags=re.IGNORECASE).strip()


def _articulo_base(texto: str) -> str:
    """Compara el artículo completo; Art. 3 no debe coincidir con Art. 30."""
    return _articulo_sin_parte(texto).casefold()


def _texto_normalizado(texto: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", texto.casefold())
                   if unicodedata.category(c) != "Mn")


def evaluar_preguntas_normativas(preguntas: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Evalúa el motor RAG sobre las 20 preguntas normativas:
    - 16 preguntas legítimas (Hit@3, cita de ley formal).
    - 4 preguntas de abstención (detección de fraude/evasión, fuera de dominio y derivación contable).
    """
    total_preguntas = len(preguntas)
    
    # Contadores de Confusión de Abstención
    tp = 0  # Debe abstenerse y se abstuvo
    tn = 0  # No debe abstenerse y respondió
    fp = 0  # No debía abstenerse y se abstuvo (falso rechazo)
    fn = 0  # Debía abstenerse y respondió (fuga peligrosa)

    hits_top3 = 0
    citas_validas = 0
    preguntas_legitimas = 0
    fuentes_auditadas = 0
    aciertos_fuente_articulo = 0
    respuestas_con_clave = 0

    detalles = []

    for q in preguntas:
        q_id = q["id"]
        texto = q["pregunta"]
        debe_abstenerse = q["debe_abstenerse"]
        tipo = q.get("tipo", "normativa")
        regimen = q.get("regimen", "AMBOS")
        art_esp = q.get("articulo_esperado")
        articulos_validos = q.get("articulos_validos", [art_esp] if art_esp else [])

        res_rag = consultar_rag(pregunta=texto, regimen=regimen, top_k=3)
        se_abstuvo = res_rag.se_abstuvo
        citas = [c.cita_oficial for c in res_rag.citas]
        docs = [c.documento for c in res_rag.citas]

        # 1. Evaluación de política de abstención
        if debe_abstenerse and se_abstuvo:
            tp += 1
            clasificacion_abstencion = "TP (Abstención Correcta)"
        elif not debe_abstenerse and not se_abstuvo:
            tn += 1
            clasificacion_abstencion = "TN (Respuesta Legítima Correcta)"
        elif not debe_abstenerse and se_abstuvo:
            fp += 1
            clasificacion_abstencion = "FP (Abstención Indebida / Falso Rechazo)"
        else:
            fn += 1
            clasificacion_abstencion = "FN (Fuga de Seguridad / Alucinación)"

        # 2. Evaluación de preguntas legítimas (no abstención)
        hit_normativo = False
        tiene_cita_formal = False
        fuente_articulo_correctos = None
        contiene_clave = None

        if not debe_abstenerse:
            preguntas_legitimas += 1
            
            # Coincidencia exacta de número de artículo; no certifica pertinencia jurídica.
            if articulos_validos:
                hit_normativo = any(
                    _articulo_base(c.articulo_seccion) == _articulo_base(a)
                    for c in res_rag.citas for a in articulos_validos
                )

            if hit_normativo:
                hits_top3 += 1

            # Formato y consistencia de la cita estructurada, no validez jurídica.
            tiene_cita_formal = bool(res_rag.citas) and all(
                c.cita_oficial == f"[{c.documento}, {_articulo_sin_parte(c.articulo_seccion)}]"
                for c in res_rag.citas
            )
            if tiene_cita_formal:
                citas_validas += 1

            fuentes_esperadas = q.get("fuentes_esperadas", [])
            if fuentes_esperadas:
                fuentes_auditadas += 1
                fuente_articulo_correctos = any(
                    c.documento.casefold() == fuente["documento"].casefold()
                    and _articulo_base(c.articulo_seccion) == _articulo_base(fuente["articulo"])
                    for c in res_rag.citas for fuente in fuentes_esperadas
                )
                if fuente_articulo_correctos:
                    aciertos_fuente_articulo += 1

            clave = q.get("cita_clave")
            if clave:
                contiene_clave = _texto_normalizado(clave) in _texto_normalizado(res_rag.respuesta)
                if contiene_clave:
                    respuestas_con_clave += 1

        detalles.append({
            "id": q_id,
            "pregunta": texto,
            "tipo": tipo,
            "debe_abstenerse": debe_abstenerse,
            "se_abstuvo": se_abstuvo,
            "clasificacion_abstencion": clasificacion_abstencion,
            "articulo_esperado": art_esp,
            "citas_obtenidas": citas,
            "documentos_consultados": docs,
            "hit_top3": hit_normativo if not debe_abstenerse else None,
            "tiene_cita_formal": tiene_cita_formal if not debe_abstenerse else None,
            "fuentes_esperadas": q.get("fuentes_esperadas", []),
            "fuente_articulo_correctos": fuente_articulo_correctos,
            "contiene_clave_indicativa": contiene_clave,
            "respuesta_fragmento": res_rag.respuesta[:180] + "..." if len(res_rag.respuesta) > 180 else res_rag.respuesta
        })

    # Métricas de Abstención
    total_debe_abstenerse = tp + fn
    total_no_debe_abstenerse = tn + fp
    accuracy_abstencion = round(((tp + tn) / total_preguntas) * 100, 2)
    precision_abstencion = round((tp / (tp + fp)) * 100, 2) if (tp + fp) > 0 else 100.0
    recall_abstencion = round((tp / (tp + fn)) * 100, 2) if (tp + fn) > 0 else 100.0
    f1_abstencion = round(2 * (precision_abstencion * recall_abstencion) / (precision_abstencion + recall_abstencion), 2) if (precision_abstencion + recall_abstencion) > 0 else 100.0

    # Métricas de Recuperación RAG
    hit_rate_top3 = round((hits_top3 / preguntas_legitimas) * 100, 2) if preguntas_legitimas > 0 else 100.0
    tasa_citas_pct = round((citas_validas / preguntas_legitimas) * 100, 2) if preguntas_legitimas > 0 else 100.0

    return {
        "total_preguntas": total_preguntas,
        "preguntas_legitimas": preguntas_legitimas,
        "preguntas_abstencion": total_debe_abstenerse,
        "matriz_confusion_abstencion": {
            "TP": tp,
            "TN": tn,
            "FP": fp,
            "FN": fn
        },
        "metricas_abstencion": {
            "accuracy_pct": accuracy_abstencion,
            "precision_pct": precision_abstencion,
            "recall_pct": recall_abstencion,
            "f1_score_pct": f1_abstencion
        },
        "metricas_recuperacion_rag": {
            "hits_top3": hits_top3,
            "hit_rate_top3_pct": hit_rate_top3,
            "respuestas_con_cita_formal": citas_validas,
            "tasa_citas_obligatorias_pct": tasa_citas_pct,
            "fuentes_auditadas": fuentes_auditadas,
            "aciertos_fuente_articulo": aciertos_fuente_articulo,
            "respuestas_con_clave_indicativa": respuestas_con_clave,
        },
        "detalles": detalles
    }


def ejecutar_evaluacion(base_url=None, output=RESULTADOS_PATH):
    global BASE_URL
    BASE_URL = base_url.rstrip("/") if base_url else None
    LATENCIES["calculo"].clear()
    LATENCIES["rag"].clear()
    print("=" * 80)
    print("EVALUACIÓN FORMAL DE CALIDAD, AGENTE Y RAG (FASE 3 - GRUPO 11)")
    print("Calendario Tributario Personalizado para Emprendedores RIMPE - SRI 2026")
    print("=" * 80)

    if not os.path.exists(DATASET_PATH):
        logger.error(f"Dataset de evaluación no encontrado en: {DATASET_PATH}")
        sys.exit(1)

    with open(DATASET_PATH, "r", encoding="utf-8") as f:
        dataset = json.load(f)

    perfiles = dataset.get("perfiles_referencia", [])
    preguntas = dataset.get("preguntas_evaluacion", [])

    print(f"\n[1/2] Evaluando {len(perfiles)} Perfiles Dorados de Contribuyentes RIMPE...")
    eval_perfiles = evaluar_perfiles_referencia(perfiles)
    print(f"      -> Perfiles con 100% de acierto: {eval_perfiles['aciertos_perfiles_completos']}/{eval_perfiles['total_perfiles']} ({eval_perfiles['precision_perfiles_pct']}%)")
    print(f"      -> Fechas coincidentes: {eval_perfiles['fechas_coincidentes']}/{eval_perfiles['total_fechas_esperadas']} ({eval_perfiles['precision_fechas_pct']}%)")

    print(f"\n[2/2] Evaluando {len(preguntas)} Preguntas Normativas (RAG + Abstención)...")
    eval_preguntas = evaluar_preguntas_normativas(preguntas)
    print(f"      -> Hit@3 en preguntas legítimas: {eval_preguntas['metricas_recuperacion_rag']['hits_top3']}/{eval_preguntas['preguntas_legitimas']} ({eval_preguntas['metricas_recuperacion_rag']['hit_rate_top3_pct']}%)")
    print(f"      -> Citas formales coherentes con metadatos: {eval_preguntas['metricas_recuperacion_rag']['respuestas_con_cita_formal']}/{eval_preguntas['preguntas_legitimas']} ({eval_preguntas['metricas_recuperacion_rag']['tasa_citas_obligatorias_pct']}%)")
    print(f"      -> Fuente + artículo auditados: {eval_preguntas['metricas_recuperacion_rag']['aciertos_fuente_articulo']}/{eval_preguntas['metricas_recuperacion_rag']['fuentes_auditadas']}")
    print(f"      -> Respuesta con clave textual indicativa: {eval_preguntas['metricas_recuperacion_rag']['respuestas_con_clave_indicativa']}/{eval_preguntas['preguntas_legitimas']}")
    print(f"      -> Precisión de Abstención (TP/(TP+FP)): {eval_preguntas['metricas_abstencion']['precision_pct']}%")
    print(f"      -> Recall de Abstención (TP/(TP+FN)): {eval_preguntas['metricas_abstencion']['recall_pct']}%")
    print(f"      -> F1-Score de Seguridad: {eval_preguntas['metricas_abstencion']['f1_score_pct']}%")
    print(f"      -> Falsos Negativos (Fugas de Seguridad): {eval_preguntas['matriz_confusion_abstencion']['FN']}")
    print(f"      -> Falsos Positivos (Abstenciones Indebidas): {eval_preguntas['matriz_confusion_abstencion']['FP']}")

    # Consolidado de resultados
    resultados_completos = {
        "timestamp_evaluacion": datetime.now(timezone.utc).isoformat(),
        "caso": "Caso N.º 11 - Calendario Tributario RIMPE",
        "evaluacion_version": "4.1.0",
        "origen_evaluacion": BASE_URL or "local",
        "resumen_ejecutivo": {
            "perfiles_evaluados": eval_perfiles["total_perfiles"],
            "precision_perfiles_pct": eval_perfiles["precision_perfiles_pct"],
            "preguntas_evaluadas": eval_preguntas["total_preguntas"],
            "hit_rate_top3_pct": eval_preguntas["metricas_recuperacion_rag"]["hit_rate_top3_pct"],
            "tasa_citas_obligatorias_pct": eval_preguntas["metricas_recuperacion_rag"]["tasa_citas_obligatorias_pct"],
            "accuracy_abstencion_pct": eval_preguntas["metricas_abstencion"]["accuracy_pct"],
            "f1_score_seguridad_pct": eval_preguntas["metricas_abstencion"]["f1_score_pct"],
            "fugas_seguridad_fn": eval_preguntas["matriz_confusion_abstencion"]["FN"],
            "falsos_rechazos_fp": eval_preguntas["matriz_confusion_abstencion"]["FP"]
        },
        "latencias": {
            "calculo": latency_summary(LATENCIES["calculo"]),
            "rag": latency_summary(LATENCIES["rag"]),
        },
        "perfiles_referencia": eval_perfiles,
        "preguntas_normativas": eval_preguntas
    }

    with open(output, "w", encoding="utf-8") as f:
        json.dump(resultados_completos, f, indent=2, ensure_ascii=False)

    print(f"\n[OK] Resultados exportados exitosamente a: {output}")
    print("=" * 80)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluación reproducible local o contra una URL desplegada.")
    parser.add_argument("--base-url", help="URL base de la API desplegada; omitir para evaluación local.")
    parser.add_argument("--output", default=RESULTADOS_PATH, help="Archivo JSON de resultados.")
    args = parser.parse_args()
    ejecutar_evaluacion(args.base_url, args.output)
