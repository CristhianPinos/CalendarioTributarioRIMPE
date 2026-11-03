"""
Script Formal de Evaluación de Calidad, Agente y RAG (Semana 3)
Caso N.º 11 – Grupo 11: Calendario Tributario Personalizado para Emprendedores RIMPE
Asignatura: Ingeniería de Software con IA Generativa - UNIANDES (Octubre 2026)

Evalúa de forma reproducible:
1. 10 Perfiles de Referencia (Dígitos 0-9, Negocio Popular, Emprendedor, Actividades Excluidas)
   verificando precisión exacta de fechas de vencimiento con traslados de feriados y fines de semana.
2. 20 Preguntas Normativas (16 con sustento legal + 4 casos de abstención obligatoria)
   midiendo Hit@3, Citas Obligatorias y Matriz de Confusión de Abstención.
3. Exporta métricas consolidadas en eval/resultados_evaluacion.json.
"""

import os
import sys
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List

# Asegurar path al backend
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.services.agent_service import tool_calcular_vencimientos, CalcularVencimientosInput
from backend.services.rag_service import responder_con_rag

logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")
logger = logging.getLogger("evaluacion_semana3")

DATASET_PATH = os.path.join(os.path.dirname(__file__), "dataset_evaluacion.json")
RESULTADOS_PATH = os.path.join(os.path.dirname(__file__), "resultados_evaluacion.json")


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
        res = tool_calcular_vencimientos(params)
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

    detalles = []

    for q in preguntas:
        q_id = q["id"]
        texto = q["pregunta"]
        debe_abstenerse = q["debe_abstenerse"]
        tipo = q.get("tipo", "normativa")
        regimen = q.get("regimen", "AMBOS")
        art_esp = q.get("articulo_esperado")
        articulos_validos = q.get("articulos_validos", [art_esp] if art_esp else [])

        res_rag = responder_con_rag(pregunta=texto, regimen=regimen, top_k=3)
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

        if not debe_abstenerse:
            preguntas_legitimas += 1
            
            # Hit@3: si alguna de las citas recuperadas coincide con alguno de los artículos válidos
            if articulos_validos:
                for c in res_rag.citas:
                    for a in articulos_validos:
                        if a.lower() in c.articulo_seccion.lower() or a.lower() in c.cita_oficial.lower():
                            hit_normativo = True
                            break
                    if hit_normativo:
                        break
            else:
                hit_normativo = len(res_rag.citas) > 0

            if hit_normativo:
                hits_top3 += 1

            # Citas formales con corchetes [..., Art. ...]
            if len(citas) > 0 and any("[" in c and "]" in c for c in citas):
                tiene_cita_formal = True
                citas_validas += 1

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
            "tasa_citas_obligatorias_pct": tasa_citas_pct
        },
        "detalles": detalles
    }


def ejecutar_evaluacion():
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
    print(f"      -> Tasa de Citas Obligatorias: {eval_preguntas['metricas_recuperacion_rag']['respuestas_con_cita_formal']}/{eval_preguntas['preguntas_legitimas']} ({eval_preguntas['metricas_recuperacion_rag']['tasa_citas_obligatorias_pct']}%)")
    print(f"      -> Precisión de Abstención (TP/(TP+FP)): {eval_preguntas['metricas_abstencion']['precision_pct']}%")
    print(f"      -> Recall de Abstención (TP/(TP+FN)): {eval_preguntas['metricas_abstencion']['recall_pct']}%")
    print(f"      -> F1-Score de Seguridad: {eval_preguntas['metricas_abstencion']['f1_score_pct']}%")
    print(f"      -> Falsos Negativos (Fugas de Seguridad): {eval_preguntas['matriz_confusion_abstencion']['FN']}")
    print(f"      -> Falsos Positivos (Abstenciones Indebidas): {eval_preguntas['matriz_confusion_abstencion']['FP']}")

    # Consolidado de resultados
    resultados_completos = {
        "timestamp_evaluacion": datetime.now(timezone.utc).isoformat(),
        "caso": "Caso N.º 11 - Calendario Tributario RIMPE",
        "evaluacion_version": "3.0.0",
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
        "perfiles_referencia": eval_perfiles,
        "preguntas_normativas": eval_preguntas
    }

    with open(RESULTADOS_PATH, "w", encoding="utf-8") as f:
        json.dump(resultados_completos, f, indent=2, ensure_ascii=False)

    print(f"\n[OK] Resultados exportados exitosamente a: {RESULTADOS_PATH}")
    print("=" * 80)


if __name__ == "__main__":
    ejecutar_evaluacion()
