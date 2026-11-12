"""Contrato de transporte HTTPS y estados observables de Mailjet."""

import requests
import pytest

from backend.services import mailjet_service


@pytest.fixture
def configured(monkeypatch):
    monkeypatch.setenv("MAILJET_API_KEY", "key-test")
    monkeypatch.setenv("MAILJET_SECRET_KEY", "secret-test")
    monkeypatch.setenv("MAILJET_FROM_EMAIL", "remitente@example.com")


def test_mailjet_success_uses_https_and_verified_sender(configured, monkeypatch):
    class Response:
        status_code = 200
        def json(self):
            return {"Messages": [{"Status": "success", "To": [{"MessageID": 12345}]}]}

    def post(url, *, auth, json, timeout):
        assert url == "https://api.mailjet.com/v3.1/send"
        assert auth == ("key-test", "secret-test")
        assert json["Messages"][0]["From"]["Email"] == "remitente@example.com"
        assert json["Messages"][0]["To"][0]["Email"] == "destino@example.com"
        assert json["Messages"][0]["TextPart"] == "Mensaje de prueba"
        assert timeout == 15
        return Response()

    monkeypatch.setattr(mailjet_service.requests, "post", post)
    assert mailjet_service.enviar_correo("destino@example.com", "Prueba", "Mensaje de prueba") == "12345"


def test_mailjet_rejection_and_timeout_are_distinct(configured, monkeypatch):
    class Rejected:
        status_code = 401

    monkeypatch.setattr(mailjet_service.requests, "post", lambda *args, **kwargs: Rejected())
    with pytest.raises(mailjet_service.MailjetError, match="rechazó"):
        mailjet_service.enviar_correo("destino@example.com", "Prueba", "Mensaje")

    def timeout(*args, **kwargs):
        raise requests.exceptions.Timeout("detalle privado")

    monkeypatch.setattr(mailjet_service.requests, "post", timeout)
    with pytest.raises(mailjet_service.MailjetUncertainError, match="concluyente"):
        mailjet_service.enviar_correo("destino@example.com", "Prueba", "Mensaje")


def test_mailjet_missing_credentials_does_not_send(monkeypatch):
    monkeypatch.delenv("MAILJET_SECRET_KEY", raising=False)
    monkeypatch.setattr(mailjet_service.requests, "post", lambda *args, **kwargs: pytest.fail("No debe enviar"))
    with pytest.raises(mailjet_service.MailjetError, match="configurado"):
        mailjet_service.enviar_correo("destino@example.com", "Prueba", "Mensaje")
