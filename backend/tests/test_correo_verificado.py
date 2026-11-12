"""La interfaz pública no tiene operador, pero un correo sin verificar no se despacha."""

import asyncio

import httpx

from backend.main import app
from backend.routers import correo_router
from backend.services.agent_service import ResultadoAgente


def request(method, path, **kwargs):
    async def run():
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            return await client.request(method, path, **kwargs)
    return asyncio.run(run())


def payload(code="123456", confirm=True, email="destino@example.com"):
    return {
        "email": email, "codigo": code, "codigo_obligacion": "IVA_SEMESTRAL_1", "confirmacion_envio": confirm,
        "perfil": {
            "ruc": "0923456784001", "razon_social": "Perfil sintético",
            "tipo_regimen": "RIMPE_EMPRENDEDOR", "email": email,
        },
    }


def test_rutas_anteriores_cerradas_y_despacho_directo_bloqueado():
    assert request("GET", "/api/perfiles").status_code == 404
    assert request("GET", "/api/flujo/recordatorios-pendientes").status_code == 404
    assert request("POST", "/api/agente/ejecutar", json={
        "instruccion": "Enviar", "perfil": payload()["perfil"], "confirmacion_envio": True,
    }).status_code == 403
    assert request("POST", "/api/agente/herramientas/enviar-recordatorio", json={
        "destinatario": "destino@example.com", "asunto": "Prueba", "texto": "Recordatorio de prueba con cita legal",
        "confirmacion_usuario": True,
    }).status_code == 403


def test_codigo_obligatorio_unico_y_sin_perfil_persistido(monkeypatch):
    correo_router._pending.clear()
    correo_router._requests.clear()
    correo_router._global_requests.clear()
    correo_router._sent.clear()
    monkeypatch.setattr(correo_router, "_mail_ready", lambda: None)
    delivered = {}
    monkeypatch.setattr(correo_router, "_send_code", lambda email, code: delivered.update(email=email, code=code))
    called = []

    def fake_agent(self, **kwargs):
        called.append(kwargs)
        return ResultadoAgente(
            instruccion_original=kwargs["instruccion"], exito=True, num_iteraciones=1,
            limite_alcanzado=False, trazas_herramientas=[], respuesta_final="Mailjet aceptó",
            estado_envio="ENVIADO",
        )

    monkeypatch.setattr(correo_router.AgenteTributarioRIMPE, "ejecutar", fake_agent)
    assert request("POST", "/api/correo/enviar-recordatorio", json=payload()).status_code == 403
    assert request("POST", "/api/correo/solicitar-codigo", json={"email": "destino@example.com"}).status_code == 200
    assert delivered["email"] == "destino@example.com"
    assert request("POST", "/api/correo/enviar-recordatorio", json=payload(code="000000", confirm=False)).status_code == 403
    assert request("POST", "/api/correo/enviar-recordatorio", json=payload(code="000000")).status_code == 403
    success = request("POST", "/api/correo/enviar-recordatorio", json=payload(code=delivered["code"]))
    assert success.status_code == 200
    assert success.json()["estado_envio"] == "ENVIADO"
    assert called[0]["perfil"]["email"] == "destino@example.com"
    assert called[0]["confirmacion_envio"] is True
    assert request("POST", "/api/correo/enviar-recordatorio", json=payload(code=delivered["code"])).status_code == 403
    assert request("POST", "/api/correo/solicitar-codigo", json={"email": "destino@example.com"}).status_code == 429


def test_correo_de_perfil_debe_coincidir(monkeypatch):
    monkeypatch.setattr(correo_router, "_mail_ready", lambda: None)
    data = payload()
    data["perfil"]["email"] = "otro@example.com"
    assert request("POST", "/api/correo/enviar-recordatorio", json=data).status_code == 403


def test_obligacion_ajena_al_perfil_no_se_envia(monkeypatch):
    from backend.services.agent_service import AgenteTributarioRIMPE

    def fail_if_smtp(_):
        raise AssertionError("No debe invocarse SMTP")

    monkeypatch.setattr("backend.services.agent_service.tool_enviar_recordatorio", fail_if_smtp)
    result = AgenteTributarioRIMPE().ejecutar(
        instruccion="Enviar obligación seleccionada",
        perfil={**payload()["perfil"], "anio": 2026},
        confirmacion_envio=True,
        codigo_obligacion="OBLIGACION_INEXISTENTE",
    )
    assert result.exito is False


def test_agente_despacha_la_obligacion_seleccionada(monkeypatch):
    from backend.services import agent_service

    selected = []

    def redactar(params):
        selected.append(params.codigo_obligacion)
        return agent_service.RedactarRecordatorioOutput(
            asunto="Recordatorio RIMPE de prueba",
            cuerpo_recordatorio="Recordatorio tributario de prueba con cita legal.",
            citas_normativas=["LRTI Art. 97.6"],
            codigo_obligacion=params.codigo_obligacion,
            fecha_vencimiento=params.fecha_vencimiento,
        )

    def enviar(params):
        assert params.destinatario == "destino@example.com"
        assert params.confirmacion_usuario is True
        return agent_service.EnviarRecordatorioOutput(
            estado="ENVIADO", destinatario=params.destinatario, canal="email",
            confirmado=True, mensaje_accion="Aceptado por SMTP", timestamp="2026-11-11T00:00:00Z",
        )

    monkeypatch.setattr(agent_service, "tool_redactar_recordatorio", redactar)
    monkeypatch.setattr(agent_service, "tool_enviar_recordatorio", enviar)
    result = agent_service.AgenteTributarioRIMPE().ejecutar(
        instruccion="Enviar obligación seleccionada",
        perfil={**payload()["perfil"], "anio": 2026},
        confirmacion_envio=True,
        codigo_obligacion="IVA_SEMESTRAL_2",
    )
    assert result.exito is True
    assert result.estado_envio == "ENVIADO"
    assert selected == ["IVA_SEMESTRAL_2"]


def test_codigo_se_entrega_por_mailjet_configurado(monkeypatch):
    sent = []
    monkeypatch.setattr(correo_router, "enviar_correo", lambda *args: sent.append(args))
    correo_router._send_code("destino@example.com", "123456")
    assert sent[0][0] == "destino@example.com"
    assert "123456" in sent[0][2]


def test_correo_verificado_contiene_obligacion_y_anio_correctos(monkeypatch):
    from backend.services import mailjet_service

    codigo_emitido = []
    mensajes = []
    monkeypatch.setattr(correo_router, "_mail_ready", lambda: None)
    monkeypatch.setattr(correo_router, "_send_code", lambda email, code: codigo_emitido.append(code))
    monkeypatch.setattr(mailjet_service, "configurado", lambda: True)

    def capturar(destinatario, asunto, texto, html):
        mensajes.append((destinatario, asunto, texto, html))
        return "id-sintetico"

    monkeypatch.setattr(mailjet_service, "enviar_correo", capturar)
    email = "auditoria-recordatorio@example.com"
    correo_router.solicitar_codigo(correo_router.SolicitarCodigo(email=email))
    datos = payload(code=codigo_emitido[0], email=email)
    datos.update(codigo_obligacion="IVA_SEMESTRAL_2", anio=2027)
    resultado = correo_router.enviar_recordatorio(correo_router.EnviarRecordatorioVerificado(**datos))

    assert resultado.exito is True
    assert resultado.estado_envio == "ENVIADO"
    assert all(t.origen_seleccion == "flujo_seguro" for t in resultado.trazas_herramientas)
    assert len(mensajes) == 1
    destinatario, asunto, texto, html = mensajes[0]
    assert destinatario == email
    assert "semestre 2: jul - dic" in asunto.lower()
    assert "ejercicio fiscal 2027" in texto
    assert "2028-01-" in texto
    assert "LRTI, art. 97.8" in texto
    assert "declaración informativa en cero" not in texto
    assert "comunicación oficial del SRI" in html
