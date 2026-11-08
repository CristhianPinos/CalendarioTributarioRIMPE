"""
Agente Inteligente de Obligaciones Tributarias RIMPE (SRI Ecuador).
Asignatura: Ingeniería de Software con IA Generativa
Caso N.º 11 – Grupo 11: Calendario Tributario RIMPE

Implementa un Bucle ReAct Autónomo (Reasoning + Action) con:
1. Cuatro herramientas formales tipadas mediante esquemas Pydantic.
2. Selección dinámica de herramientas con manejo de trazas y observaciones.
3. Precisión financiera con Decimal (ROUND_HALF_UP).
4. Fundamentación normativa estricta mediante el motor RAG.
5. Límite de iteraciones configurable (control de loops).
6. Compuerta obligatoria de confirmación humana (Human-in-the-Loop - HITL).
7. Lectura de parámetros desacoplados desde config/parametros.yaml.
8. Despacho de correo transaccional SMTP autenticado (Microsoft 365 / Office 365 / Gmail).
"""

import os
import json
import logging
import smtplib
from uuid import uuid4
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field, EmailStr, field_validator
from backend.middleware.logging_lopdp import anonimizar_traza

from backend.services.config_loader import (
    load_parametros,
    get_tarifa_iva_vigente,
    get_tarifas_iva,
    get_parametros_agente_flujo
)
from backend.services.calculator import (
    calcular_vencimientos as calc_vencimientos_core,
    validar_ruc_persona_natural
)
from backend.services.rag_service import responder_con_rag

logger = logging.getLogger("rimpe.agent_service")


# ==============================================================================
# ESQUEMAS PYDANTIC FORMALES PARA LAS HERRAMIENTAS DEL AGENTE
# ==============================================================================

class CalcularVencimientosInput(BaseModel):
    ruc: str = Field(..., description="RUC válido de 13 dígitos del contribuyente persona natural")
    tipo_regimen: str = Field(..., description="RIMPE_NEGOCIO_POPULAR o RIMPE_EMPRENDEDOR")
    anio: int = Field(default=2026, ge=2024, le=2030, description="Año fiscal de las obligaciones")
    tiene_actividades_excluidas: bool = Field(default=False, description="Si realiza actividades profesionales o arriendos")

    @field_validator("ruc")
    @classmethod
    def validar_ruc(cls, v: str) -> str:
        if not validar_ruc_persona_natural(v):
            raise ValueError("El RUC ingresado no cumple con el algoritmo Módulo 10 para personas naturales del SRI.")
        return v


class CalcularVencimientosOutput(BaseModel):
    ruc: str
    noveno_digito: int
    tipo_regimen: str
    anio_fiscal: int
    total_obligaciones: int
    eventos: List[Dict[str, Any]]


class CalcularIVAInput(BaseModel):
    base_imponible: float = Field(..., ge=0.0, description="Monto base sobre el cual se calcula el IVA")
    tarifa_vigente: Optional[float] = Field(None, ge=0.0, le=1.0, description="Tarifa de IVA (0.15, 0.05, 0.0). Si es None, se lee de config/")
    tipo_tarifa: str = Field(default="general", description="general (15%), materiales_construccion (5%), tarifa_cero (0%)")


class CalcularIVAOutput(BaseModel):
    base_imponible: float
    tarifa_aplicada: float
    porcentaje_texto: str
    monto_iva: float
    total_con_iva: float
    fuente_tarifa: str


class RedactarRecordatorioInput(BaseModel):
    codigo_obligacion: str = Field(..., description="Código de la obligación (ej. IVA_SEMESTRAL_1, RENTA_ANUAL_EMPRENDEDOR)")
    ruc: str = Field(..., description="RUC del contribuyente")
    razon_social: str = Field(default="Estimado contribuyente", description="Nombre o razón social")
    tipo_regimen: str = Field(..., description="RIMPE_NEGOCIO_POPULAR o RIMPE_EMPRENDEDOR")
    fecha_vencimiento: str = Field(..., description="Fecha límite calculada en formato YYYY-MM-DD")
    monto_estimado: Optional[float] = Field(None, description="Monto estimado de impuesto si aplica")


class RedactarRecordatorioOutput(BaseModel):
    asunto: str
    cuerpo_recordatorio: str
    citas_normativas: List[str]
    codigo_obligacion: str
    fecha_vencimiento: str
    requiere_confirmacion_humana: bool = True


class EnviarRecordatorioInput(BaseModel):
    destinatario: EmailStr = Field(..., description="Correo electrónico del contribuyente")
    asunto: str = Field(..., min_length=5, description="Asunto del mensaje de recordatorio")
    texto: str = Field(..., min_length=15, description="Cuerpo del mensaje redactado")
    confirmacion_usuario: bool = Field(default=False, description="Debe ser True para efectuar el despacho real (HITL)")
    canal: str = Field(default="email", description="Canal de entrega (email, consola)")


class EnviarRecordatorioOutput(BaseModel):
    estado: str = Field(..., description="PENDIENTE_CONFIRMACION, ENVIADO, SIMULADO, ERROR_ENVIO o ESTADO_INCIERTO")
    destinatario: str
    canal: str
    confirmado: bool
    mensaje_accion: str
    timestamp: str
    id_registro_auditoria: Optional[str] = None
    usuario_confirmador: Optional[str] = None


# ==============================================================================
# IMPLEMENTACIÓN DETERMINISTA DE LAS 4 HERRAMIENTAS FORMALES
# ==============================================================================

def tool_calcular_vencimientos(params: CalcularVencimientosInput) -> CalcularVencimientosOutput:
    """
    Herramienta 1: Calcula fechas de vencimiento deterministas según el noveno dígito
    del RUC y calendario oficial SRI con traslado automático por fines de semana y feriados.
    """
    resultado = calc_vencimientos_core(
        ruc=params.ruc,
        tipo_regimen=params.tipo_regimen,
        anio=params.anio,
        tiene_actividades_excluidas=params.tiene_actividades_excluidas
    )
    return CalcularVencimientosOutput(**resultado)


def tool_calcular_iva(params: CalcularIVAInput) -> CalcularIVAOutput:
    """
    Herramienta 2: Calcula el Impuesto al Valor Agregado (IVA) determinista
    extrayendo las tarifas oficiales desde config/parametros.yaml (nunca en duro)
    utilizando Decimal con redondeo financiero ROUND_HALF_UP.
    """
    if params.tarifa_vigente is not None:
        tarifa_val = params.tarifa_vigente
        fuente = "Parámetro explícito de llamada"
    else:
        tarifa_val = get_tarifa_iva_vigente(params.tipo_tarifa)
        fuente = f"config/parametros.yaml (tipo: {params.tipo_tarifa})"

    dos_decimales = Decimal("0.01")
    d_base = Decimal(str(params.base_imponible))
    d_tarifa = Decimal(str(tarifa_val))

    d_monto_iva = (d_base * d_tarifa).quantize(dos_decimales, rounding=ROUND_HALF_UP)
    d_total = (d_base + d_monto_iva).quantize(dos_decimales, rounding=ROUND_HALF_UP)

    porcentaje_num = int((d_tarifa * Decimal("100")).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    porcentaje_str = f"{porcentaje_num}%"

    return CalcularIVAOutput(
        base_imponible=float(d_base),
        tarifa_aplicada=float(d_tarifa),
        porcentaje_texto=porcentaje_str,
        monto_iva=float(d_monto_iva),
        total_con_iva=float(d_total),
        fuente_tarifa=fuente
    )


def tool_redactar_recordatorio(params: RedactarRecordatorioInput) -> RedactarRecordatorioOutput:
    """
    Herramienta 3: Redacta un recordatorio pedagógico y formal para el contribuyente.
    Consulta el motor RAG para fundamentar cada recordatorio con su cita de ley obligatoria.
    """
    pregunta_normativa = f"¿Cuándo y cómo se presenta la obligación {params.codigo_obligacion} para {params.tipo_regimen}?"
    respuesta_rag = responder_con_rag(pregunta=pregunta_normativa, regimen=params.tipo_regimen, top_k=2)

    citas = [c.cita_oficial for c in respuesta_rag.citas] if respuesta_rag.citas else ["[LRTI, Art. 97.6]"]
    citas_str = " ".join(citas)

    if "IVA" in params.codigo_obligacion:
        asunto = f"Recordatorio Tributario SRI: Declaración Semestral de IVA ({params.fecha_vencimiento})"
        instruccion_pago = (
            "Recuerde que si no registró ventas ni compras en este período, debe presentar "
            "su declaración informativa en cero para evitar sanciones del SRI."
        )
    elif "RENTA" in params.codigo_obligacion:
        asunto = f"Recordatorio Tributario SRI: Declaración Anual de Impuesto a la Renta ({params.fecha_vencimiento})"
        instruccion_pago = (
            "Prepare el consolidado de sus ingresos brutos gravados del ejercicio fiscal 2026. "
            "La tarifa aplicable se calculará según las tablas progresivas vigentes de la Ley de Eficiencia Económica."
        )
    else:
        asunto = f"Aviso de Vencimiento Tributario SRI - {params.fecha_vencimiento}"
        instruccion_pago = "Revise el portal oficial de SRI en Línea con su usuario y clave."

    monto_texto = f"\nMonto estimado preliminar: ${params.monto_estimado:.2f} USD." if params.monto_estimado is not None else ""

    cuerpo = (
        f"Estimado(a) {params.razon_social} (RUC: {params.ruc[:4]}****{params.ruc[10:]}),\n\n"
        f"Le informamos que de acuerdo al calendario tributario oficial del SRI, su obligación "
        f"'{params.codigo_obligacion}' correspondiente al Régimen {params.tipo_regimen} "
        f"vence el próximo {params.fecha_vencimiento}.\n\n"
        f"{instruccion_pago}{monto_texto}\n\n"
        f"Base Legal y Citas Obligatorias:\n{citas_str}\n\n"
        f"Nota: Este mensaje ha sido redactado por el Asistente Inteligente RIMPE y requiere su "
        f"confirmación antes de registrarse en la bitácora de despachos oficiales."
    )

    return RedactarRecordatorioOutput(
        asunto=asunto,
        cuerpo_recordatorio=cuerpo,
        citas_normativas=citas,
        codigo_obligacion=params.codigo_obligacion,
        fecha_vencimiento=params.fecha_vencimiento,
        requiere_confirmacion_humana=True
    )


def tool_enviar_recordatorio(params: EnviarRecordatorioInput) -> EnviarRecordatorioOutput:
    """
    Herramienta 4: Despacha el recordatorio con COMPUERTA OBLIGATORIA de confirmación humana (HITL).
    Si confirmacion_usuario es False, NO despacha y retorna estado PENDIENTE_CONFIRMACION.
    ENVIADO significa que el servidor SMTP aceptó el mensaje, no que llegó a la bandeja.
    """
    ts = datetime.now(timezone.utc).isoformat()

    if not params.confirmacion_usuario:
        logger.info("Recordatorio detenido en compuerta HITL; requiere confirmación.")
        return EnviarRecordatorioOutput(
            estado="PENDIENTE_CONFIRMACION",
            destinatario=params.destinatario,
            canal=params.canal,
            confirmado=False,
            mensaje_accion="El recordatorio está listo para despacho, pero requiere confirmación explícita del usuario (HITL).",
            timestamp=ts,
            id_registro_auditoria=None
        )

    id_auditoria = f"AUD-DISPATCH-{uuid4().hex}"

    # Lectura de credenciales SMTP desde entorno (.env)
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port_raw = os.getenv("SMTP_PORT", "587")
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")
    smtp_from_email = os.getenv("SMTP_FROM_EMAIL", smtp_user)
    smtp_from_name = os.getenv("SMTP_FROM_NAME", "Calendario Tributario SRI RIMPE").strip('"\'')
    smtp_use_tls = os.getenv("SMTP_USE_TLS", "True").lower() in ("true", "1", "t", "yes")

    if smtp_host and smtp_user and smtp_password:
        accepted = False
        sending = False
        try:
            smtp_port = int(smtp_port_raw)
            msg = MIMEMultipart("alternative")
            msg["Subject"] = params.asunto
            msg["From"] = f'"{smtp_from_name}" <{smtp_from_email}>'
            msg["To"] = params.destinatario

            cuerpo_texto = f"{params.texto}\n\nID Auditoría: {id_auditoria}"
            cuerpo_html = f"""
            <!DOCTYPE html>
            <html lang="es">
            <head>
              <meta charset="utf-8">
            </head>
            <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f8fafc; margin: 0; padding: 20px;">
              <div style="max-width: 620px; margin: 0 auto; background: #ffffff; border-radius: 16px; border: 1px solid #e2e8f0; overflow: hidden; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);">
                <div style="background: linear-gradient(135deg, #1e3a8a 0%, #1e1b4b 100%); color: #ffffff; padding: 24px 28px;">
                  <h1 style="margin: 0; font-size: 18px; font-weight: 700;">{smtp_from_name}</h1>
                  <p style="margin: 4px 0 0 0; font-size: 12px; color: #93c5fd;">Notificación Oficial - SRI Ecuador 2026</p>
                </div>
                <div style="padding: 28px; color: #1e293b; font-size: 14px; line-height: 1.6;">
                  <div style="white-space: pre-wrap; margin-bottom: 24px;">{params.texto}</div>
                  <div style="padding: 14px 18px; background-color: #f1f5f9; border-left: 4px solid #2563eb; border-radius: 6px; font-size: 12px; color: #475569;">
                    <strong>Confirmación HITL Registrada:</strong> Este recordatorio fue autorizado formalmente por el usuario en el asistente tributario interactivo.
                  </div>
                </div>
                <div style="background-color: #f8fafc; border-top: 1px solid #e2e8f0; padding: 16px 28px; font-size: 11px; color: #64748b; font-family: monospace;">
                  Audit ID: <strong>{id_auditoria}</strong> | Timestamp: {ts}
                </div>
              </div>
            </body>
            </html>
            """

            msg.attach(MIMEText(cuerpo_texto, "plain", "utf-8"))
            msg.attach(MIMEText(cuerpo_html, "html", "utf-8"))

            with smtplib.SMTP(smtp_host, smtp_port, timeout=15) as server:
                if smtp_use_tls:
                    server.starttls()
                server.login(smtp_user, smtp_password)
                sending = True
                refused = server.sendmail(smtp_from_email, [params.destinatario], msg.as_string())
                if refused:
                    sending = False
                    raise ValueError("El servidor SMTP rechazó al destinatario.")
                accepted = True

            logger.info(f"Servidor SMTP aceptó el correo. Audit ID: {id_auditoria}")

        except Exception:
            if accepted:
                logger.warning("SMTP aceptó el mensaje pero falló el cierre de conexión. Audit ID: %s", id_auditoria)
            else:
                estado = "ESTADO_INCIERTO" if sending else "ERROR_ENVIO"
                logger.error("No se pudo confirmar el despacho SMTP. Estado: %s. Audit ID: %s", estado, id_auditoria)
                return EnviarRecordatorioOutput(
                    estado=estado, destinatario=params.destinatario, canal=params.canal,
                    confirmado=True, mensaje_accion=(
                        "No se pudo determinar si SMTP aceptó el mensaje; revise el servidor antes de reintentar."
                        if sending else "El envío SMTP falló antes de transmitir el mensaje; puede reintentarse."
                    ), timestamp=ts, id_registro_auditoria=id_auditoria,
                )
    else:
        logger.warning("SMTP no configurado. Envío simulado. Audit ID: %s", id_auditoria)
        return EnviarRecordatorioOutput(
            estado="SIMULADO", destinatario=params.destinatario, canal=params.canal,
            confirmado=True, mensaje_accion="Aprobación registrada en modo simulación; no se envió ningún correo.",
            timestamp=ts, id_registro_auditoria=id_auditoria,
        )

    return EnviarRecordatorioOutput(
        estado="ENVIADO",
        destinatario=params.destinatario,
        canal=params.canal,
        confirmado=True,
        mensaje_accion="El servidor SMTP aceptó el recordatorio para su entrega.",
        timestamp=ts,
        id_registro_auditoria=id_auditoria
    )


# ==============================================================================
# AGENTE TRIBUTARIO ORQUESTADOR (BUCLE ReAct CON AUDITORÍA Y HITL)
# ==============================================================================

class TrazaEjecucionHerramienta(BaseModel):
    herramienta: str
    entradas: Dict[str, Any]
    salidas: Dict[str, Any]
    timestamp: str


class ResultadoAgente(BaseModel):
    instruccion_original: str
    exito: bool
    num_iteraciones: int
    limite_alcanzado: bool
    trazas_herramientas: List[TrazaEjecucionHerramienta]
    respuesta_final: str
    estado_envio: Optional[str] = None
    requiere_accion_usuario: bool = False
    usuario_confirmador: Optional[str] = None


class AgenteTributarioRIMPE:
    """
    Agente tributario reactivo basado en el patrón ReAct (Reasoning + Action).
    Selecciona dinámicamente qué herramienta ejecutar según el estado de la meta,
    registra trazas de ejecución estructuradas y respeta límites estrictos de iteración y HITL.
    """
    def __init__(self, max_iteraciones: Optional[int] = None):
        cfg_agente = get_parametros_agente_flujo()
        self.max_iteraciones = max_iteraciones or cfg_agente.get("max_iteraciones_agente", 5)

    def ejecutar(
        self,
        instruccion: str,
        perfil: Dict[str, Any],
        base_imponible_iva: Optional[float] = None,
        confirmacion_envio: bool = False
    ) -> ResultadoAgente:
        """
        Bucle ReAct principal:
        Itera razonando sobre el estado actual, seleccionando la siguiente herramienta
        a invocar y almacenando las observaciones hasta concluir la meta o agotar iteraciones.
        """
        iteraciones = 0
        trazas: List[TrazaEjecucionHerramienta] = []
        limite_alcanzado = False

        ruc = perfil.get("ruc", "")
        tipo_regimen = perfil.get("tipo_regimen", "RIMPE_EMPRENDEDOR")
        email = perfil.get("email", "contribuyente@sri.ec")
        razon_social = perfil.get("razon_social", "Contribuyente RIMPE")

        # Estado del agente en memoria de trabajo
        estado_contexto = {
            "vencimientos": None,
            "iva": None,
            "recordatorio": None,
            "envio": None
        }

        try:
            while iteraciones < self.max_iteraciones:
                # ------------------------------------------------------------------
                # FASE REASON: Decidir siguiente acción basada en el contexto actual
                # ------------------------------------------------------------------
                if estado_contexto["vencimientos"] is None:
                    herramienta_a_ejecutar = "calcular_vencimientos"
                elif base_imponible_iva is not None and estado_contexto["iva"] is None:
                    herramienta_a_ejecutar = "calcular_iva"
                elif estado_contexto["recordatorio"] is None:
                    herramienta_a_ejecutar = "redactar_recordatorio"
                elif estado_contexto["envio"] is None:
                    herramienta_a_ejecutar = "enviar_recordatorio"
                else:
                    # Todas las tareas requeridas por la instrucción han concluido
                    break

                iteraciones += 1

                # ------------------------------------------------------------------
                # FASE ACT: Ejecución de la herramienta seleccionada
                # ------------------------------------------------------------------
                if herramienta_a_ejecutar == "calcular_vencimientos":
                    inp_venc = CalcularVencimientosInput(
                        ruc=ruc,
                        tipo_regimen=tipo_regimen,
                        anio=perfil.get("anio", 2026),
                        tiene_actividades_excluidas=perfil.get("tiene_actividades_excluidas", False)
                    )
                    out_venc = tool_calcular_vencimientos(inp_venc)
                    estado_contexto["vencimientos"] = out_venc
                    trazas.append(TrazaEjecucionHerramienta(
                        herramienta="calcular_vencimientos",
                        entradas=anonimizar_traza(inp_venc.model_dump()),
                        salidas=anonimizar_traza(out_venc.model_dump()),
                        timestamp=datetime.now(timezone.utc).isoformat()
                    ))

                    if not out_venc.eventos:
                        return ResultadoAgente(
                            instruccion_original=instruccion,
                            exito=False,
                            num_iteraciones=iteraciones,
                            limite_alcanzado=False,
                            trazas_herramientas=trazas,
                            respuesta_final="No se identificaron obligaciones vigentes para el perfil ingresado."
                        )

                elif herramienta_a_ejecutar == "calcular_iva":
                    inp_iva = CalcularIVAInput(
                        base_imponible=base_imponible_iva,
                        tipo_tarifa="general"
                    )
                    out_iva = tool_calcular_iva(inp_iva)
                    estado_contexto["iva"] = out_iva
                    trazas.append(TrazaEjecucionHerramienta(
                        herramienta="calcular_iva",
                        entradas=anonimizar_traza(inp_iva.model_dump()),
                        salidas=anonimizar_traza(out_iva.model_dump()),
                        timestamp=datetime.now(timezone.utc).isoformat()
                    ))

                elif herramienta_a_ejecutar == "redactar_recordatorio":
                    venc = estado_contexto["vencimientos"]
                    proxima = venc.eventos[0]
                    monto_iva_val = estado_contexto["iva"].monto_iva if estado_contexto["iva"] else None

                    inp_redactar = RedactarRecordatorioInput(
                        codigo_obligacion=proxima["codigo_obligacion"],
                        ruc=ruc,
                        razon_social=razon_social,
                        tipo_regimen=tipo_regimen,
                        fecha_vencimiento=proxima["fecha_vencimiento"],
                        monto_estimado=monto_iva_val
                    )
                    out_redactar = tool_redactar_recordatorio(inp_redactar)
                    estado_contexto["recordatorio"] = out_redactar
                    trazas.append(TrazaEjecucionHerramienta(
                        herramienta="redactar_recordatorio",
                        entradas=anonimizar_traza(inp_redactar.model_dump()),
                        salidas=anonimizar_traza(out_redactar.model_dump()),
                        timestamp=datetime.now(timezone.utc).isoformat()
                    ))

                elif herramienta_a_ejecutar == "enviar_recordatorio":
                    redactado = estado_contexto["recordatorio"]
                    inp_envio = EnviarRecordatorioInput(
                        destinatario=email,
                        asunto=redactado.asunto,
                        texto=redactado.cuerpo_recordatorio,
                        confirmacion_usuario=confirmacion_envio,
                        canal="email"
                    )
                    out_envio = tool_enviar_recordatorio(inp_envio)
                    estado_contexto["envio"] = out_envio
                    trazas.append(TrazaEjecucionHerramienta(
                        herramienta="enviar_recordatorio",
                        entradas=anonimizar_traza(inp_envio.model_dump()),
                        salidas=anonimizar_traza(out_envio.model_dump()),
                        timestamp=datetime.now(timezone.utc).isoformat()
                    ))

            # Si el bucle terminó pero aún quedaban acciones pendientes en el plan
            if (
                estado_contexto["envio"] is None
                and (
                    estado_contexto["recordatorio"] is None
                    or (base_imponible_iva is not None and estado_contexto["iva"] is None)
                    or estado_contexto["vencimientos"] is None
                )
            ):
                limite_alcanzado = (iteraciones >= self.max_iteraciones)

            # ------------------------------------------------------------------
            # SÍNTESIS DE LA RESPUESTA FINAL
            # ------------------------------------------------------------------
            out_envio = estado_contexto["envio"]
            venc = estado_contexto["vencimientos"]
            proxima = venc.eventos[0] if (venc and venc.eventos) else {}

            if out_envio and out_envio.estado == "PENDIENTE_CONFIRMACION":
                respuesta_texto = (
                    f"Se calcularon {venc.total_obligaciones} obligaciones. Próximo vencimiento: "
                    f"{proxima.get('fecha_vencimiento')} ({proxima.get('titulo')}). "
                    f"El recordatorio ha sido redactado con citas normativas y está en espera de su "
                    f"CONFIRMACIÓN para ser despachado a {email}."
                )
                requiere_accion = True
            elif out_envio and out_envio.estado == "ENVIADO":
                respuesta_texto = (
                    f"El recordatorio para la obligación '{proxima.get('codigo_obligacion')}' "
                    f"ha sido confirmado por el usuario y despachado con éxito a {email}."
                )
                requiere_accion = False
            elif out_envio and out_envio.estado == "SIMULADO":
                respuesta_texto = "La aprobación fue registrada en modo simulación. No se envió ningún correo."
                requiere_accion = True
            elif out_envio and out_envio.estado in ("ERROR_ENVIO", "ESTADO_INCIERTO"):
                respuesta_texto = out_envio.mensaje_accion
                requiere_accion = True
            else:
                respuesta_texto = f"Ciclo completado con {iteraciones} iteraciones."
                requiere_accion = False

            return ResultadoAgente(
                instruccion_original=instruccion,
                exito=True,
                num_iteraciones=iteraciones,
                limite_alcanzado=limite_alcanzado,
                trazas_herramientas=trazas,
                respuesta_final=respuesta_texto,
                estado_envio=out_envio.estado if out_envio else None,
                requiere_accion_usuario=requiere_accion
            )

        except Exception as e:
            logger.error("Error en bucle del agente ReAct: %s", type(e).__name__)
            return ResultadoAgente(
                instruccion_original=instruccion,
                exito=False,
                num_iteraciones=iteraciones,
                limite_alcanzado=limite_alcanzado,
                trazas_herramientas=trazas,
                respuesta_final="No se pudo completar la operación del agente. Revise los datos e inténtelo de nuevo.",
                requiere_accion_usuario=False
            )
