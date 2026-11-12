"""Transporte de correo transaccional por la API HTTPS de Mailjet."""

import os

import requests


MAILJET_URL = "https://api.mailjet.com/v3.1/send"


class MailjetError(Exception):
    """El proveedor rechazó el envío o la configuración está incompleta."""


class MailjetUncertainError(MailjetError):
    """La solicitud salió, pero no se recibió una respuesta concluyente."""


def configurado() -> bool:
    key = os.getenv("MAILJET_API_KEY", "").strip()
    secret = os.getenv("MAILJET_SECRET_KEY", "").strip()
    sender = os.getenv("MAILJET_FROM_EMAIL", "").strip()
    return bool(key and secret and sender and not key.startswith("tu_") and not secret.startswith("tu_"))


def enviar_correo(destinatario: str, asunto: str, texto: str, html: str | None = None) -> str:
    """Devuelve MessageID cuando Mailjet acepta la solicitud; no prueba entrega."""
    if not configurado():
        raise MailjetError("Mailjet no está configurado.")
    sender = os.environ["MAILJET_FROM_EMAIL"].strip()
    name = os.getenv("MAILJET_FROM_NAME", "Calendario RIMPE").strip('"\'')
    message = {
        "From": {"Email": sender, "Name": name},
        "To": [{"Email": destinatario}],
        "Subject": asunto,
        "TextPart": texto,
    }
    if html:
        message["HTMLPart"] = html
    try:
        response = requests.post(
            MAILJET_URL,
            auth=(os.environ["MAILJET_API_KEY"].strip(), os.environ["MAILJET_SECRET_KEY"].strip()),
            json={"Messages": [message]},
            timeout=15,
        )
    except requests.exceptions.RequestException as exc:
        raise MailjetUncertainError("Sin respuesta concluyente de Mailjet.") from None
    if response.status_code != 200:
        raise MailjetError("Mailjet rechazó la solicitud de envío.")
    try:
        result = response.json()["Messages"][0]
        if result["Status"] != "success":
            raise MailjetError("Mailjet rechazó el mensaje.")
        message_id = result["To"][0]["MessageID"]
        return str(message_id)
    except (KeyError, IndexError, TypeError, ValueError):
        raise MailjetUncertainError("Mailjet respondió sin confirmación del mensaje.") from None
