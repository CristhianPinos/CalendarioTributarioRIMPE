"""
Servicio de Integración con Google Gemini Flash y Resiliencia con Tenacity.
Proporciona explicaciones pedagógicas de obligaciones tributarias para el régimen RIMPE.
Incluye:
1. Reintentos exponenciales automáticos con Tenacity (1s, 2s, 4s) ante errores 429 y 503.
2. Salida estructurada estricta mapeada a RecordatorioEstructurado.
3. Fallback determinista oficial para garantizar 100% de disponibilidad offline o ante saturación de cuota.
4. Protección de credenciales cargando GEMINI_API_KEY desde variables de entorno (.env).
"""

import os
import json
import time
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from dotenv import load_dotenv
import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
    RetryError
)

from backend.schemas import (
    TipoRegimen,
    ExplicacionObligacionRequest,
    ExplicacionObligacionResponse,
    RecordatorioEstructurado
)

# Cargar variables de entorno desde la raíz del proyecto
BASE_DIR = Path(__file__).resolve().parent.parent.parent
ENV_PATH = BASE_DIR / ".env"
load_dotenv(dotenv_path=ENV_PATH)

logger = logging.getLogger("rimpe.llm_service")

# Modelos recomendados ordenados por prioridad de disponibilidad
PRIMARY_MODEL = os.getenv("GEMINI_MODEL", "gemini-3-flash-preview")
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
PROMPTS_DIR = BASE_DIR / "backend" / "prompts"


def cargar_prompt_template(version: str = "v3") -> str:
    """Carga la plantilla de prompt correspondiente desde backend/prompts/."""
    archivo_prompt = PROMPTS_DIR / f"system_{version}.md"
    if archivo_prompt.exists():
        with open(archivo_prompt, "r", encoding="utf-8") as f:
            return f.read()
    return ""



class GeminiAPIException(Exception):
    """Excepción específica para errores temporales o de cuota de la API de Gemini."""
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message
        super().__init__(f"Gemini API Error {status_code}: {message}")


class GeminiRateLimitException(GeminiAPIException):
    """Excepción para código HTTP 429 (Too Many Requests / Quota Exceeded)."""
    pass


class GeminiServiceUnavailableException(GeminiAPIException):
    """Excepción para código HTTP 503 (High Demand / Service Unavailable)."""
    pass


# ==============================================================================
# CATÁLOGO DE RESPUESTAS DETERMINISTAS OFICIALES (FALLBACK DE ALTA DISPONIBILIDAD)
# ==============================================================================

FALLBACK_OBLIGACIONES: Dict[str, Dict[str, str]] = {
    "IVA_SEMESTRAL_1": {
        "codigo_obligacion": "IVA_SEMESTRAL_1",
        "titulo_pedagogico": "Declaración Semestral de IVA (Primer Semestre: Ene - Jun)",
        "base_legal_oficial": "Ley de Régimen Tributario Interno (LRTI) Art. 97.8 y Resolución SRI NAC-DGERCGC24-00000027.",
        "explicacion_sencilla": (
            "Como contribuyente RIMPE Emprendedor, debes consolidar y reportar todas tus ventas y compras "
            "gravadas con tarifa 15% o tarifa 0% efectuadas entre el 1 de enero y el 30 de junio. "
            "Si no tuviste actividad económica durante este periodo, igualmente estás obligado a presentar la "
            "declaración en ceros para mantener tu RUC al día."
        ),
        "consecuencia_incumplimiento": (
            "La presentación tardía genera una multa mínima de $30,00 USD conforme al Art. 100 de la LRTI "
            "más los intereses acumulados por cada mes o fracción de mora en caso de existir impuesto a pagar."
        ),
        "sugerencia_accion": (
            "Revisa tus comprobantes electrónicos emitidos en el portal SRI. Accede con tu clave al Formulario 104 "
            "en línea, selecciona el periodo semestral correspondiente y confirma el envío antes del vencimiento."
        ),
        "canal_recomendado": "Portal SRI en Línea (www.sri.gob.ec) > Declaraciones > Declaración de Impuestos > Formulario 104."
    },
    "IVA_SEMESTRAL_2": {
        "codigo_obligacion": "IVA_SEMESTRAL_2",
        "titulo_pedagogico": "Declaración Semestral de IVA (Segundo Semestre: Jul - Dic)",
        "base_legal_oficial": "LRTI Art. 97.8 y Resolución SRI NAC-DGERCGC24-00000027.",
        "explicacion_sencilla": (
            "Reporte semestral de tus actividades comerciales correspondientes a la segunda mitad del año. "
            "Permite liquidar el IVA cobrado a tus clientes restando el crédito tributario por tus adquisiciones de negocio."
        ),
        "consecuencia_incumplimiento": (
            "Sanción pecuniaria por omisión o declaración tardía ($30,00 USD mínimo) y posible suspensión temporal "
            "de la vigencia de autorización de tus comprobantes de venta."
        ),
        "sugerencia_accion": (
            "Descarga el reporte de facturación electrónica del segundo semestre y llena el formulario de IVA semestral."
        ),
        "canal_recomendado": "Portal SRI en Línea > Declaraciones > Formulario 104."
    },
    "RENTA_ANUAL_EMPRENDEDOR": {
        "codigo_obligacion": "RENTA_ANUAL_EMPRENDEDOR",
        "titulo_pedagogico": "Declaración Anual de Impuesto a la Renta (RIMPE Emprendedor)",
        "base_legal_oficial": "LRTI Art. 97.6 (reformado por la Ley de Eficiencia Económica, R.O. 461) y RALRTI Art. 219.",
        "explicacion_sencilla": (
            "Liquidación anual obligatoria del Impuesto a la Renta para personas naturales que superaron los "
            "$20.000,00 USD hasta $300.000,00 USD en ingresos brutos gravados. Se calcula aplicando la tabla progresiva "
            "oficial (fracción básica más porcentaje marginal sobre el excedente) descontando las retenciones que te hayan realizado."
        ),
        "consecuencia_incumplimiento": (
            "Recargo del 20% sobre el impuesto determinado más intereses de mora calculados por el Banco Central del Ecuador "
            "y multas tipificadas en el Código Tributario."
        ),
        "sugerencia_accion": (
            "Suma tus ingresos brutos del año fiscal, resta tus retenciones del 1% y liquida mediante el Formulario de Renta Personas Naturales."
        ),
        "canal_recomendado": "Portal SRI en Línea > Declaraciones > Declaración de Impuesto a la Renta Personas Naturales."
    },
    "RENTA_ANUAL_NEGOCIO_POPULAR": {
        "codigo_obligacion": "RENTA_ANUAL_NEGOCIO_POPULAR",
        "titulo_pedagogico": "Declaración y Pago de Cuota Simplificada RIMPE Negocio Popular",
        "base_legal_oficial": "Ley Orgánica de Eficiencia Económica y Generación de Empleo (Art. 23) y LRTI Art. 97.6.",
        "explicacion_sencilla": (
            "Los Negocios Populares con ingresos de hasta $2.500,00 USD pagan $0,00 USD de impuesto. "
            "Aquellos con ingresos entre $2.500,01 y $20.000,00 USD pagan una cuota fija que va desde $5,00 hasta $60,00 USD. "
            "Esta cuota anual incluye y consolida el impuesto a la renta y el IVA, por lo que no debes hacer declaraciones de IVA adicionales."
        ),
        "consecuencia_incumplimiento": (
            "Multa mínima reglamentaria de $15,00 USD si no se causa impuesto, o recargos e intereses de mora sobre la cuota fija aplicable."
        ),
        "sugerencia_accion": (
            "Verifica el total de tus notas de venta o facturas emitidas y cancela tu cuota fija en línea mediante débito bancario o ventanilla."
        ),
        "canal_recomendado": "Portal SRI en Línea > Pagos > Pago de Obligaciones RIMPE."
    },
    "IVA_REGIMEN_GENERAL_MIXTO": {
        "codigo_obligacion": "IVA_REGIMEN_GENERAL_MIXTO",
        "titulo_pedagogico": "Declaración de IVA por Actividades Excluidas (Régimen General Mixto)",
        "base_legal_oficial": "LRTI Art. 97.4, Art. 65 y RALRTI Art. 158.",
        "explicacion_sencilla": (
            "Si además de tu actividad RIMPE percibes ingresos excluidos (ej. honorarios por servicios profesionales, "
            "comisiones, arriendos o relación de dependencia), dichos ingresos deben declararse de manera separada "
            "bajo las reglas del Régimen General, aplicando la tarifa vigente de IVA y facturando electrónicamente con desglose."
        ),
        "consecuencia_incumplimiento": (
            "Clausura del establecimiento o multas formales del Régimen General por no emitir comprobantes autorizados con IVA o no liquidarlo a tiempo."
        ),
        "sugerencia_accion": (
            "Presenta tu Formulario 104 declarando exclusivamente las ventas y adquisiciones de la actividad profesional o excluida."
        ),
        "canal_recomendado": "Portal SRI en Línea > Declaraciones > Formulario 104 Régimen General."
    }
}


def obtener_fallback_determinista(
    codigo_obligacion: str,
    fecha_vencimiento: str,
    tipo_regimen: TipoRegimen,
    es_declaracion_en_cero: bool = False
) -> RecordatorioEstructurado:
    """Retorna una explicación oficial determinista sin depender de servicios externos."""
    plantilla = FALLBACK_OBLIGACIONES.get(
        codigo_obligacion,
        {
            "codigo_obligacion": codigo_obligacion,
            "titulo_pedagogico": f"Obligación Tributaria: {codigo_obligacion}",
            "base_legal_oficial": "Ley de Régimen Tributario Interno y Resoluciones Generales del SRI Ecuador.",
            "explicacion_sencilla": (
                f"Obligación formal del régimen {tipo_regimen.value}. Verifique los comprobantes "
                "de venta emitidos y recibidos durante el periodo fiscal para realizar su declaración correspondiente."
            ),
            "consecuencia_incumplimiento": "Intereses de mora y multas tipificadas en el Código Tributario ecuatoriano.",
            "sugerencia_accion": "Ingrese al portal oficial del SRI y remita la declaración correspondiente.",
            "canal_recomendado": "Portal SRI en Línea (www.sri.gob.ec)."
        }
    )

    titulo = plantilla["titulo_pedagogico"]
    explicacion = plantilla["explicacion_sencilla"]
    sugerencia = plantilla["sugerencia_accion"]
    consecuencia = plantilla["consecuencia_incumplimiento"]

    if es_declaracion_en_cero:
        titulo = f"[DECLARACIÓN EN CEROS] {titulo}"
        explicacion = (
            "GUÍA OFICIAL PARA DECLARACIÓN EN CEROS (SIN MOVIMIENTO): Aunque no hayas registrado ventas ni "
            "compras gravadas en este semestre, el SRI exige presentar de forma 100% obligatoria tu declaración informativa "
            "con valores en cero ($0.00). Omitir esta declaración genera multas automáticas inmediatas, aunque el impuesto a pagar sea $0.00."
        )
        sugerencia = (
            "1. Accede a SRI en Línea (www.sri.gob.ec) con tu RUC y contraseña.\n"
            "2. Selecciona 'Declaraciones' > 'Declaración de Impuestos' y elige el formulario correspondiente.\n"
            "3. En la pregunta inicial: '¿Para el período a declarar requiere registrar información?', marca NO.\n"
            "4. Confirma que los casilleros queden en $0.00 y pulsa 'Firmar y Enviar' para descargar tu comprobante de cumplimiento."
        )
        consecuencia = (
            "La falta de presentación o el envío tardío de una declaración en ceros causa una multa pecuniaria de $30.00 a $60.00 USD "
            "(Art. 100 de la LRTI), además del riesgo de bloqueo o suspensión preventiva de tu RUC."
        )

    return RecordatorioEstructurado(
        codigo_obligacion=plantilla["codigo_obligacion"],
        titulo_pedagogico=titulo,
        fecha_limite_formateada=f"Vence impostergablemente el {fecha_vencimiento}",
        base_legal_oficial=plantilla["base_legal_oficial"],
        explicacion_sencilla=explicacion,
        consecuencia_incumplimiento=consecuencia,
        sugerencia_accion=sugerencia,
        canal_recomendado=plantilla["canal_recomendado"]
    )


# ==============================================================================
# LLAMADA HTTP A GOOGLE GEMINI FLASH CON BACKOFF EXPONENCIAL
# ==============================================================================

def _enviar_http_gemini(url: str, payload: Dict[str, Any], timeout_sec: float) -> httpx.Response:
    """Envía la solicitud HTTP POST al endpoint de Gemini."""
    with httpx.Client(timeout=timeout_sec) as http_client:
        return http_client.post(url, json=payload)


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=4),
    retry=retry_if_exception_type((GeminiRateLimitException, GeminiServiceUnavailableException, httpx.TimeoutException)),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True
)
def _invocar_gemini_raw(
    prompt: str,
    api_key: str,
    model: str = PRIMARY_MODEL,
    timeout_sec: float = 25.0
) -> Tuple[Dict[str, Any], int]:
    """
    Ejecuta la llamada HTTP cruda al endpoint de Google Gemini con control estricto de reintentos.
    Retorna (parsed_json_dict, total_tokens).
    Lanza GeminiRateLimitException ante HTTP 429 para activar backoff.
    Lanza GeminiServiceUnavailableException ante HTTP 503 para activar backoff.
    """
    url = GEMINI_API_URL.format(model=model) + f"?key={api_key}"

    schema = {
        "type": "OBJECT",
        "properties": {
            "codigo_obligacion": {"type": "STRING"},
            "titulo_pedagogico": {"type": "STRING"},
            "fecha_limite_formateada": {"type": "STRING"},
            "base_legal_oficial": {"type": "STRING"},
            "explicacion_sencilla": {"type": "STRING"},
            "consecuencia_incumplimiento": {"type": "STRING"},
            "sugerencia_accion": {"type": "STRING"},
            "canal_recomendado": {"type": "STRING"}
        },
        "required": [
            "codigo_obligacion",
            "titulo_pedagogico",
            "fecha_limite_formateada",
            "base_legal_oficial",
            "explicacion_sencilla",
            "consecuencia_incumplimiento",
            "sugerencia_accion",
            "canal_recomendado"
        ]
    }

    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }],
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": schema,
            "temperature": 0.2
        }
    }

    try:
        response = _enviar_http_gemini(url, payload, timeout_sec)
    except httpx.TimeoutException as exc:
        logger.warning(f"Timeout al conectar con Gemini ({timeout_sec}s). Reintentando...")
        raise exc

    if response.status_code == 429:
        logger.warning("Gemini devolvió HTTP 429 (Límite de tasa excedido). Activando backoff...")
        raise GeminiRateLimitException(429, response.text)

    if response.status_code in (500, 502, 503, 504):
        logger.warning(f"Gemini devolvió HTTP {response.status_code} (Alta demanda / servicio caído). Activando backoff...")
        raise GeminiServiceUnavailableException(response.status_code, response.text)

    if response.status_code != 200:
        raise GeminiAPIException(response.status_code, response.text)

    data = response.json()
    candidates = data.get("candidates", [])
    if not candidates:
        raise GeminiAPIException(500, "Gemini no devolvió ningún candidato de respuesta.")

    part = candidates[0].get("content", {}).get("parts", [{}])[0]
    text = part.get("text", "")
    parsed_dict = json.loads(text)

    total_tokens = data.get("usageMetadata", {}).get("totalTokenCount", 0)
    return parsed_dict, total_tokens


# ==============================================================================
# SERVICIO PRINCIPAL EXPUESTO AL BACKEND
# ==============================================================================

def generar_explicacion_obligacion(
    request: ExplicacionObligacionRequest,
    api_key: Optional[str] = None,
    prompt_template: Optional[str] = None,
    model_name: Optional[str] = None
) -> ExplicacionObligacionResponse:
    """
    Genera la explicación pedagógica estructurada para la obligación tributaria especificada.
    Si la API de Gemini falla tras agotar los 3 reintentos exponenciales o no hay conexión/API Key,
    sirve de manera transparente el catálogo determinista oficial de alta disponibilidad.
    """
    key = api_key or os.getenv("GEMINI_API_KEY", "")
    model = model_name or PRIMARY_MODEL
    start_time = time.time()

    # Si no se configuró clave o está vacía, retornar fallback directamente
    if not key or key == "tu_clave_real_de_gemini_aqui":
        logger.warning("GEMINI_API_KEY no configurada o es plantilla. Usando fallback determinista oficial.")
        recordatorio = obtener_fallback_determinista(
            request.codigo_obligacion,
            request.fecha_vencimiento,
            request.tipo_regimen,
            request.es_declaracion_en_cero
        )
        latency = round((time.time() - start_time) * 1000, 2)
        return ExplicacionObligacionResponse(
            obligacion=recordatorio,
            modelo_utilizado="fallback-determinista-sri",
            tokens_utilizados=0,
            tiempo_generacion_ms=latency,
            fuente_conocimiento="Catálogo Oficial SRI (Offline Fallback - LRTI & Resoluciones 24-0027/23-0034)"
        )

    # Construir el prompt para la IA
    if prompt_template:
        base_prompt = prompt_template
    else:
        template_v3 = cargar_prompt_template("v3")
        if template_v3:
            base_prompt = (
                template_v3.replace("{codigo_obligacion}", request.codigo_obligacion)
                .replace("{tipo_regimen}", request.tipo_regimen.value)
                .replace("{fecha_vencimiento}", request.fecha_vencimiento)
                .replace("{tiene_actividades_excluidas}", "Sí" if request.tiene_actividades_excluidas else "No")
                .replace("{ingresos_estimados}", f"{request.ingresos_estimados or 0:.2f}")
                .replace("{contexto_adicional}", request.contexto_adicional or "Ninguno")
            )
        else:
            base_prompt = (
                "Eres un asesor tributario experto del Servicio de Rentas Internas (SRI) del Ecuador. "
                "Explica con claridad, empatía y rigor legal la siguiente obligación para un contribuyente ecuatoriano:\n"
                f"- Código de obligación: {request.codigo_obligacion}\n"
                f"- Régimen RIMPE: {request.tipo_regimen.value}\n"
                f"- Fecha de vencimiento límite calculada: {request.fecha_vencimiento}\n"
                f"- Actividades excluidas adicionales: {'Sí' if request.tiene_actividades_excluidas else 'No'}\n"
                f"- Ingresos anuales estimados: ${request.ingresos_estimados or 0:.2f} USD\n"
                f"- Contexto adicional del usuario: {request.contexto_adicional or 'Ninguno'}\n\n"
                "REGLAS OBLIGATORIAS:\n"
                "1. Cita las normas legales vigentes de Ecuador (LRTI, RALRTI, Ley de Eficiencia Económica, Resoluciones NAC-DGERCGC24-00000027 o 23-0034).\n"
                "2. NO inventes fechas de vencimiento; utiliza estrictamente la fecha de vencimiento límite proporcionada.\n"
                "3. La explicación debe ser comprensible para un microemprendedor, sin perder precisión jurídica.\n"
                "4. Menciona las sanciones o multas tipificadas por el SRI ante el retraso."
            )

    if request.es_declaracion_en_cero:
        base_prompt += (
            "\n\nCASO ESPECIAL - DECLARACIÓN EN CERO:\n"
            "El contribuyente indica que NO TUVO ACTIVIDAD ECONÓMICA NI VENTAS en este período y va a DECLARAR EN CERO.\n"
            "Explica enfáticamente:\n"
            "1. Que declarar en cero es 100% OBLIGATORIO por ley y que no hacerlo acarrea multas de $30 a $60 USD.\n"
            "2. El paso a paso exacto para seleccionar 'NO' en registro de información y enviar la declaración en ceros en sri.gob.ec.\n"
        )

    try:
        parsed_json, tokens = _invocar_gemini_raw(
            prompt=base_prompt,
            api_key=key,
            model=model
        )
        recordatorio = RecordatorioEstructurado(**parsed_json)
        latency = round((time.time() - start_time) * 1000, 2)

        return ExplicacionObligacionResponse(
            obligacion=recordatorio,
            modelo_utilizado=model,
            tokens_utilizados=tokens,
            tiempo_generacion_ms=latency,
            fuente_conocimiento="Normativa oficial SRI Ecuador (Resoluciones NAC-24-0027, NAC-23-0034, LRTI)"
        )

    except (RetryError, GeminiAPIException, Exception) as err:
        logger.error(f"Fallo en llamada a Gemini tras reintentos ({err}). Activando fallback determinista de alta disponibilidad.")
        recordatorio = obtener_fallback_determinista(
            request.codigo_obligacion,
            request.fecha_vencimiento,
            request.tipo_regimen,
            request.es_declaracion_en_cero
        )
        latency = round((time.time() - start_time) * 1000, 2)
        return ExplicacionObligacionResponse(
            obligacion=recordatorio,
            modelo_utilizado="fallback-determinista-sri",
            tokens_utilizados=0,
            tiempo_generacion_ms=latency,
            fuente_conocimiento="Catálogo Oficial SRI (Offline Fallback - LRTI & Resoluciones 24-0027/23-0034)"
        )
