"""Selección acotada de herramientas para el agente; nunca decide parámetros ni envíos."""

import json
import logging
import os

import httpx

from backend.services.llm import GEMINI_API_URL, PRIMARY_MODEL


logger = logging.getLogger("rimpe.agent_planner")
ORDEN_SEGURO = (
    "calcular_vencimientos", "calcular_iva", "redactar_recordatorio", "enviar_recordatorio"
)


def seleccionar_herramienta(disponibles: list[str], ejecutadas: list[str], *, usar_gemini: bool) -> tuple[str, str]:
    """Elige una acción permitida. Ante cualquier fallo conserva el recorrido probado."""
    if not disponibles or any(nombre not in ORDEN_SEGURO for nombre in disponibles):
        raise ValueError("El conjunto de herramientas permitidas es inválido.")
    alternativa = next(nombre for nombre in ORDEN_SEGURO if nombre in disponibles)
    clave = os.getenv("GEMINI_API_KEY", "").strip()
    if not usar_gemini or not clave or clave == "tu_clave_real_de_gemini_aqui":
        return alternativa, "flujo_seguro"

    # No se envían al modelo la instrucción libre, el RUC, el nombre, el correo ni importes.
    estado = {"objetivo": "preparar un recordatorio, sin autorizar despachos",
              "herramientas_disponibles": disponibles, "herramientas_ejecutadas": ejecutadas}
    cuerpo = {
        "systemInstruction": {"parts": [{"text": (
            "Elige solo la siguiente herramienta de herramientas_disponibles. "
            "Todas las acciones disponibles que falten deberán completarse. "
            "No decidas fechas, tarifas, destinatarios ni autorización. "
            "Responde únicamente con JSON: {\"herramienta\": \"nombre_exacto\"}."
        )}]},
        "contents": [{"role": "user", "parts": [{"text": json.dumps(estado, ensure_ascii=False)}]}],
        "generationConfig": {"responseMimeType": "application/json", "temperature": 0,
                             "maxOutputTokens": 512},
    }
    try:
        respuesta = httpx.post(
            GEMINI_API_URL.format(model=PRIMARY_MODEL) + f"?key={clave}",
            json=cuerpo, timeout=4.0,
        )
        respuesta.raise_for_status()
        texto = respuesta.json()["candidates"][0]["content"]["parts"][0]["text"]
        nombre = json.loads(texto)["herramienta"]
        if nombre in disponibles:
            return nombre, "gemini"
        logger.warning("Gemini propuso una herramienta fuera de la lista permitida.")
    except (httpx.HTTPError, ValueError, KeyError, IndexError, TypeError):
        logger.warning("No se pudo validar la selección de Gemini; se usa el flujo seguro.")
    return alternativa, "flujo_seguro"
