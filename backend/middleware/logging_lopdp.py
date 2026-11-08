"""
Middleware de Observabilidad y Anonimización Conforme a la LOPDP (Ecuador).
Ley Orgánica de Protección de Datos Personales (R.O. Suplemento 459).

Garantiza la trazabilidad de peticiones, auditoría de tiempos de respuesta
y registro seguro sin filtrar datos personales de contribuyentes (PII)
tales como RUCs completos, nombres, correos electrónicos o secretos en logs.
"""

import re
import time
import logging
from typing import Callable
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.responses import JSONResponse

logger = logging.getLogger("rimpe.audit.lopdp")
logger.setLevel(logging.INFO)

# Configurar formateador de auditoría si no tiene manejadores previos
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "[%(asctime)s] [AUDIT-LOPDP] [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)


def enmascarar_ruc(ruc: str) -> str:
    """Enmascara un RUC dejando solo los 4 primeros dígitos y el sufijo final (ej. 0923****001)."""
    if isinstance(ruc, str) and len(ruc) == 13 and ruc.isdigit():
        return f"{ruc[:4]}****{ruc[10:]}"
    return "***RUC_PROTEGIDO***"


def enmascarar_email(email: str) -> str:
    """Enmascara una dirección de email (ej. juan.perez@empresa.ec -> j***@empresa.ec)."""
    if isinstance(email, str) and "@" in email:
        partes = email.split("@", 1)
        usuario = partes[0]
        dominio = partes[1]
        if len(usuario) <= 2:
            return f"{usuario[0]}*@{dominio}"
        return f"{usuario[0]}***{usuario[-1]}@{dominio}"
    return "***EMAIL_PROTEGIDO***"


def anonimizar_texto(texto: str) -> str:
    """
    Detecta y reemplaza patrones de datos sensibles en cadenas de texto
    utilizando expresiones regulares conformes a la LOPDP.
    """
    # Anonimizar RUCs de 13 dígitos
    texto = re.sub(
        r"\b(\d{4})\d{6}(\d{3})\b",
        r"\1****\2",
        texto
    )
    # Cédulas de 10 dígitos, sin alterar los RUC ya enmascarados.
    texto = re.sub(r"\b(\d{2})\d{6}(\d{2})\b", r"\1******\2", texto)
    # Anonimizar emails
    texto = re.sub(
        r"\b([a-zA-Z0-9_.+-])[a-zA-Z0-9_.+-]*@([a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)\b",
        r"\1***@\2",
        texto
    )
    return texto


def anonimizar_traza(valor):
    """Minimiza datos personales en trazas de herramientas devueltas por la API."""
    if isinstance(valor, dict):
        ocultar = {"razon_social", "nombre_comercial", "asunto", "texto", "cuerpo_recordatorio"}
        return {
            clave: "[DATO_PROTEGIDO]" if clave in ocultar else anonimizar_traza(item)
            for clave, item in valor.items()
        }
    if isinstance(valor, list):
        return [anonimizar_traza(item) for item in valor]
    if isinstance(valor, str):
        return anonimizar_texto(valor)
    return valor


class LoggingLOPDPMiddleware(BaseHTTPMiddleware):
    """
    Middleware Starlette/FastAPI que intercepta cada solicitud entrante y saliente,
    registrando latencia, código de estado y ruta de forma totalmente desprovista de PII.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        metodo = request.method
        # La plantilla de ruta evita registrar IDs aportados por el cliente.
        ruta = "<sin_resolver>"

        try:
            response = await call_next(request)
            ruta = getattr(request.scope.get("route"), "path", "<sin_resolver>")
            process_time_ms = round((time.time() - start_time) * 1000, 2)

            # Inyectar cabecera de auditoría de tiempo de proceso
            response.headers["X-Process-Time-Ms"] = str(process_time_ms)
            response.headers["X-Data-Protection"] = "LOPDP-Ecuador-Compliant"

            # Registro de auditoría seguro (sin PII)
            logger.info(
                f"METHOD={metodo} PATH={ruta} STATUS={response.status_code} "
                f"LATENCY_MS={process_time_ms}"
            )

            return response

        except Exception as exc:
            process_time_ms = round((time.time() - start_time) * 1000, 2)
            logger.error(
                f"METHOD={metodo} PATH={ruta} STATUS=500 ERROR={type(exc).__name__} "
                f"LATENCY_MS={process_time_ms}"
            )
            return JSONResponse(
                status_code=500,
                content={"detail": "No se pudo procesar la solicitud."},
                headers={
                    "X-Process-Time-Ms": str(process_time_ms),
                    "X-Data-Protection": "LOPDP-Ecuador-Compliant",
                },
            )
