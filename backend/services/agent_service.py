"""
Agente Inteligente de Obligaciones Tributarias RIMPE (SRI Ecuador).
Asignatura: Ingeniería de Software con IA Generativa
Caso N.º 11 – Grupo 11: Calendario Tributario RIMPE

Implementa un Bucle ReAct Autónomo (Reasoning + Action) con:
1. Cuatro herramientas formales tipadas mediante esquemas Pydantic.
2. Selección dinámica de herramientas con manejo de trazas y observaciones.
3. Precisión financiera con Decimal (ROUND_HALF_UP).
4. Referencias normativas verificadas para los recordatorios y consulta RAG separada.
5. Límite de iteraciones configurable (control de loops).
6. Compuerta obligatoria de confirmación humana (Human-in-the-Loop - HITL).
7. Lectura de parámetros desacoplados desde config/parametros.yaml.
8. Despacho de correo transaccional por la API HTTPS de Mailjet.
"""

import os
from html import escape
import json
import logging
from uuid import uuid4
from datetime import date, datetime, timezone
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
from backend.services.llm import BASE_LEGAL_POR_OBLIGACION
from backend.services import mailjet_service
from backend.services.agent_planner import seleccionar_herramienta

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
    titulo_obligacion: Optional[str] = Field(default=None, description="Título del evento calculado")
    anio_fiscal: Optional[int] = Field(default=None, ge=2024, le=2030)
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
    Herramienta 3: Redacta un recordatorio para la obligación seleccionada.
    Usa referencias legales verificadas del mismo catálogo que el modal.
    """
    codigo = params.codigo_obligacion
    fecha = date.fromisoformat(params.fecha_vencimiento)
    anio = params.anio_fiscal or (fecha.year - 1 if codigo in {
        "IVA_SEMESTRAL_2", "RENTA_ANUAL_EMPRENDEDOR", "RENTA_ANUAL_NEGOCIO_POPULAR"
    } else fecha.year)
    titulos = {
        "IVA_SEMESTRAL_1": "Declaración semestral de IVA (enero-junio)",
        "IVA_SEMESTRAL_2": "Declaración semestral de IVA (julio-diciembre)",
        "RENTA_ANUAL_EMPRENDEDOR": "Declaración anual de renta RIMPE Emprendedor",
        "RENTA_ANUAL_NEGOCIO_POPULAR": "Declaración anual de renta RIMPE Negocio Popular",
        "IVA_REGIMEN_GENERAL_MIXTO": "IVA por actividades excluidas del RIMPE",
    }
    titulo = params.titulo_obligacion or titulos.get(codigo, "Obligación tributaria")
    detalle_ejercicio = "" if f"ejercicio fiscal {anio}" in titulo.lower() else f" (ejercicio fiscal {anio})"
    asunto = f"Recordatorio Calendario RIMPE: {titulo} ({params.fecha_vencimiento})"
    instrucciones = {
        "IVA_SEMESTRAL_1": f"Revisa tus comprobantes de ventas y adquisiciones de enero a junio de {anio}. Contrasta los datos precargados y presenta la declaración de IVA que corresponda en SRI en Línea.",
        "IVA_SEMESTRAL_2": f"Revisa tus comprobantes de ventas y adquisiciones de julio a diciembre de {anio}. Contrasta los datos precargados y presenta la declaración de IVA que corresponda en SRI en Línea.",
        "RENTA_ANUAL_EMPRENDEDOR": f"Revisa tus ingresos del ejercicio fiscal {anio}, descuentos, devoluciones y retenciones aplicables. Verifica el formulario de renta y el importe calculado antes de presentar la declaración en SRI en Línea.",
        "RENTA_ANUAL_NEGOCIO_POPULAR": f"Revisa los ingresos de tu actividad durante el ejercicio fiscal {anio} y verifica en SRI en Línea la declaración y la cuota que correspondan a tu caso.",
        "IVA_REGIMEN_GENERAL_MIXTO": "Consulta en tu RUC las obligaciones de IVA de las actividades excluidas del RIMPE. Confirma en SRI en Línea la periodicidad, el formulario y la fecha aplicable antes de declarar.",
    }
    accion = instrucciones.get(codigo, "Consulta las obligaciones activas de tu RUC y verifica el trámite aplicable en SRI en Línea.")
    referencia = BASE_LEGAL_POR_OBLIGACION.get(codigo)
    citas = [f"[{referencia}]"] if referencia else []
    linea_fecha = (
        f"Fecha orientativa mostrada en este calendario: {params.fecha_vencimiento}. Confirma la fecha aplicable en SRI en Línea."
        if codigo == "IVA_REGIMEN_GENERAL_MIXTO"
        else f"Fecha de vencimiento calculada por el calendario: {params.fecha_vencimiento}."
    )

    cuerpo = (
        f"Estimado(a) {params.razon_social} (RUC: {params.ruc[:4]}****{params.ruc[10:]}),\n\n"
        f"Obligación: {titulo}{detalle_ejercicio}.\n"
        f"{linea_fecha}\n\n"
        f"Acción sugerida: {accion}\n\n"
        + (f"Referencia normativa: {citas[0]}\n\n" if citas else "")
        + "Recordatorio informativo de Calendario RIMPE. El envío se realiza únicamente tras la autorización del usuario. "
        "No constituye una comunicación oficial del SRI."
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
    ENVIADO significa que Mailjet aceptó el mensaje, no que llegó a la bandeja.
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

    if mailjet_service.configurado():
        try:
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
                  <h1 style="margin: 0; font-size: 18px; font-weight: 700;">{escape(os.getenv('MAILJET_FROM_NAME', 'Calendario RIMPE'))}</h1>
                  <p style="margin: 4px 0 0 0; font-size: 12px; color: #93c5fd;">Recordatorio informativo tributario</p>
                </div>
                <div style="padding: 28px; color: #1e293b; font-size: 14px; line-height: 1.6;">
                  <div style="white-space: pre-wrap; margin-bottom: 24px;">{escape(params.texto)}</div>
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

            message_id = mailjet_service.enviar_correo(params.destinatario, params.asunto, cuerpo_texto, cuerpo_html)
            logger.info("Mailjet aceptó el correo. Audit ID: %s; MessageID: %s", id_auditoria, message_id)
        except mailjet_service.MailjetUncertainError:
            logger.warning("Resultado de Mailjet incierto. Audit ID: %s", id_auditoria)
            return EnviarRecordatorioOutput(
                estado="ESTADO_INCIERTO", destinatario=params.destinatario, canal=params.canal,
                confirmado=True, mensaje_accion="No se pudo confirmar si Mailjet aceptó el mensaje; revise el proveedor antes de reintentar.",
                timestamp=ts, id_registro_auditoria=id_auditoria,
            )
        except mailjet_service.MailjetError:
            logger.error("Mailjet rechazó el envío. Audit ID: %s", id_auditoria)
            return EnviarRecordatorioOutput(
                estado="ERROR_ENVIO", destinatario=params.destinatario, canal=params.canal,
                confirmado=True, mensaje_accion="Mailjet rechazó el envío antes de aceptarlo; puede reintentarse.",
                timestamp=ts, id_registro_auditoria=id_auditoria,
            )
    else:
        logger.warning("Mailjet no configurado. Envío simulado. Audit ID: %s", id_auditoria)
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
        mensaje_accion="Mailjet aceptó el recordatorio para su entrega.",
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
    origen_seleccion: str = "flujo_seguro"
    herramientas_permitidas: List[str] = Field(default_factory=list)


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
    def __init__(self, max_iteraciones: Optional[int] = None, usar_seleccion_gemini: bool = False):
        cfg_agente = get_parametros_agente_flujo()
        self.max_iteraciones = max_iteraciones or cfg_agente.get("max_iteraciones_agente", 5)
        self.usar_seleccion_gemini = usar_seleccion_gemini

    def ejecutar(
        self,
        instruccion: str,
        perfil: Dict[str, Any],
        base_imponible_iva: Optional[float] = None,
        confirmacion_envio: bool = False,
        codigo_obligacion: Optional[str] = None,
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
                disponibles = []
                if estado_contexto["vencimientos"] is None:
                    disponibles.append("calcular_vencimientos")
                else:
                    if base_imponible_iva is not None and estado_contexto["iva"] is None:
                        disponibles.append("calcular_iva")
                    if estado_contexto["recordatorio"] is None:
                        disponibles.append("redactar_recordatorio")
                    if (estado_contexto["recordatorio"] is not None
                            and (base_imponible_iva is None or estado_contexto["iva"] is not None)
                            and estado_contexto["envio"] is None):
                        disponibles.append("enviar_recordatorio")
                if not disponibles:
                    break
                herramienta_a_ejecutar, origen_seleccion = seleccionar_herramienta(
                    disponibles, [traza.herramienta for traza in trazas],
                    usar_gemini=self.usar_seleccion_gemini,
                )

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
                        timestamp=datetime.now(timezone.utc).isoformat(),
                        origen_seleccion=origen_seleccion, herramientas_permitidas=disponibles,
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
                        timestamp=datetime.now(timezone.utc).isoformat(),
                        origen_seleccion=origen_seleccion, herramientas_permitidas=disponibles,
                    ))

                elif herramienta_a_ejecutar == "redactar_recordatorio":
                    venc = estado_contexto["vencimientos"]
                    proxima = next(
                        (evento for evento in venc.eventos if evento["codigo_obligacion"] == codigo_obligacion),
                        None,
                    ) if codigo_obligacion else venc.eventos[0]
                    if proxima is None:
                        return ResultadoAgente(
                            instruccion_original=instruccion, exito=False,
                            num_iteraciones=iteraciones, limite_alcanzado=False,
                            trazas_herramientas=trazas,
                            respuesta_final="La obligación seleccionada no corresponde al perfil calculado.",
                        )
                    monto_iva_val = estado_contexto["iva"].monto_iva if estado_contexto["iva"] else None

                    inp_redactar = RedactarRecordatorioInput(
                        codigo_obligacion=proxima["codigo_obligacion"],
                        ruc=ruc,
                        razon_social=razon_social,
                        tipo_regimen=tipo_regimen,
                        fecha_vencimiento=proxima["fecha_vencimiento"],
                        monto_estimado=monto_iva_val,
                        titulo_obligacion=proxima["titulo"],
                        anio_fiscal=venc.anio_fiscal,
                    )
                    out_redactar = tool_redactar_recordatorio(inp_redactar)
                    estado_contexto["recordatorio"] = out_redactar
                    trazas.append(TrazaEjecucionHerramienta(
                        herramienta="redactar_recordatorio",
                        entradas=anonimizar_traza(inp_redactar.model_dump()),
                        salidas=anonimizar_traza(out_redactar.model_dump()),
                        timestamp=datetime.now(timezone.utc).isoformat(),
                        origen_seleccion=origen_seleccion, herramientas_permitidas=disponibles,
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
                        timestamp=datetime.now(timezone.utc).isoformat(),
                        origen_seleccion=origen_seleccion, herramientas_permitidas=disponibles,
                    ))

            # Si el bucle terminó pero aún quedaban acciones pendientes en el plan
            if estado_contexto["envio"] is None and iteraciones >= self.max_iteraciones:
                limite_alcanzado = True

            # ------------------------------------------------------------------
            # SÍNTESIS DE LA RESPUESTA FINAL
            # ------------------------------------------------------------------
            out_envio = estado_contexto["envio"]
            venc = estado_contexto["vencimientos"]
            proxima = next(
                (evento for evento in venc.eventos if evento["codigo_obligacion"] == codigo_obligacion),
                {},
            ) if (venc and codigo_obligacion) else (venc.eventos[0] if (venc and venc.eventos) else {})

            if limite_alcanzado:
                respuesta_texto = "Se alcanzó el límite de pasos antes de preparar el recordatorio completo."
                requiere_accion = True
            elif out_envio and out_envio.estado == "PENDIENTE_CONFIRMACION":
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
                exito=not limite_alcanzado,
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
