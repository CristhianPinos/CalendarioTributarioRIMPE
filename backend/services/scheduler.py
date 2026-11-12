"""
Servicio del Flujo Programado Diario y Gestión de Recordatorios con Confirmación Humana (HITL).
Asignatura: Ingeniería de Software con IA Generativa
Caso N.º 11 – Grupo 11: Calendario Tributario RIMPE

Cumple con la orden de la Fase 3 y la Checklist de Entrega 3:
1. Flujo programado (tarea diaria) que detecta vencimientos próximos (5 días hábiles antes).
2. Prepara y redacta recordatorios con citas normativas obligatorias usando el motor RAG.
3. Compuerta de Confirmación Humana (Human-in-the-Loop - HITL):
   Los recordatorios se almacenan en estado 'PENDIENTE_CONFIRMACION'.
   Solo un usuario autorizado puede revisarlos y confirmar su despacho.
4. Idempotencia estricta: reintentar la tarea no genera recordatorios duplicados para la misma obligación.
"""

import os
import json
import hashlib
import logging
import threading
from functools import wraps
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, EmailStr

from backend.services.config_loader import (
    load_parametros,
    get_parametros_agente_flujo,
    get_feriados_2026
)
from backend.services.agent_service import (
    tool_calcular_vencimientos,
    tool_redactar_recordatorio,
    tool_enviar_recordatorio,
    CalcularVencimientosInput,
    RedactarRecordatorioInput,
    EnviarRecordatorioInput,
    EnviarRecordatorioOutput
)
from backend.services.storage import SQLiteStore

logger = logging.getLogger("rimpe.scheduler_service")

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_PROCESSED_DIR = BASE_DIR / "data" / "processed"
PENDIENTES_DB_PATH = DATA_PROCESSED_DIR / "recordatorios_pendientes.json"


# ==============================================================================
# MODELOS DE DATOS DEL FLUJO PROGRAMADO
# ==============================================================================

class RecordatorioColaItem(BaseModel):
    id_recordatorio: str
    ruc: str
    razon_social: str
    email: EmailStr
    tipo_regimen: str
    codigo_obligacion: str
    titulo_obligacion: str
    fecha_vencimiento: str
    dias_restantes: int
    asunto: str
    cuerpo_recordatorio: str
    citas_normativas: List[str]
    estado: str = Field(default="PENDIENTE_CONFIRMACION", description="PENDIENTE_CONFIRMACION, EN_PROCESO, ENVIADO, SIMULADO, ERROR_ENVIO o ESTADO_INCIERTO")
    fecha_generacion: str
    fecha_envio: Optional[str] = None
    id_auditoria_envio: Optional[str] = None
    usuario_confirmador: Optional[str] = None
    fecha_ultimo_intento: Optional[str] = None


class ResumenTareaDiaria(BaseModel):
    fecha_ejecucion: str
    contribuyentes_evaluados: int
    vencimientos_detectados: int
    recordatorios_nuevos_generados: int
    recordatorios_existentes_omitidos: int
    recordatorios_preparados: List[RecordatorioColaItem]
    dias_anticipacion_configurados: int


# ==============================================================================
# CONJUNTO DE CONTRIBUYENTES REGISTRADOS POR DEFECTO PARA EL ESCANEO DIARIO
# ==============================================================================

CONTRIBUYENTES_REGISTRADOS_DEFAULT = [
    {
        "ruc": "0910000017001",
        "razon_social": "Carlos Mendoza - Panadería Central",
        "tipo_regimen": "RIMPE_NEGOCIO_POPULAR",
        "email": "carlos.mendoza@panaderiacentral.ec",
        "anio": 2026,
        "tiene_actividades_excluidas": False
    },
    {
        "ruc": "0910000025001",
        "razon_social": "Andrea Salazar - Boutique y Modas",
        "tipo_regimen": "RIMPE_EMPRENDEDOR",
        "email": "andrea.salazar@boutiquemodas.ec",
        "anio": 2026,
        "tiene_actividades_excluidas": False
    },
    {
        "ruc": "0910000033001",
        "razon_social": "Ferretería El Tornillo S.A.",
        "tipo_regimen": "RIMPE_EMPRENDEDOR",
        "email": "administracion@eltornillo.ec",
        "anio": 2026,
        "tiene_actividades_excluidas": False
    },
    {
        "ruc": "0910000041001",
        "razon_social": "Diana Romero - Taller de Confecciones",
        "tipo_regimen": "RIMPE_NEGOCIO_POPULAR",
        "email": "diana.romero@confecciones.ec",
        "anio": 2026,
        "tiene_actividades_excluidas": False
    },
    {
        "ruc": "0923456784001",
        "razon_social": "Comercial Pinos & Asociados",
        "tipo_regimen": "RIMPE_EMPRENDEDOR",
        "email": "cristhian.pinos@empresa.ec",
        "anio": 2026,
        "tiene_actividades_excluidas": True
    }
]


# ==============================================================================
# GESTOR DE ALMACENAMIENTO DE LA COLA DE RECORDATORIOS (IDEMPOTENCIA)
# ==============================================================================

class ColaRecordatoriosStore:
    """Gestiona la persistencia idempotente de recordatorios pendientes y confirmados."""
    def __init__(self, storage_path: Path = PENDIENTES_DB_PATH):
        self.storage_path = storage_path
        self._ensure_storage()

    def _ensure_storage(self):
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.storage_path.exists():
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump([], f)

    def obtener_todos(self) -> List[Dict[str, Any]]:
        self._ensure_storage()
        try:
            with open(self.storage_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    def guardar_todos(self, items: List[Dict[str, Any]]):
        self._ensure_storage()
        with open(self.storage_path, "w", encoding="utf-8") as f:
            json.dump(items, f, ensure_ascii=False, indent=2)

    def existe_recordatorio_activo(self, ruc: str, codigo_obligacion: str, fecha_vencimiento: str) -> bool:
        """Verifica idempotencia: si ya existe un recordatorio para este RUC y fecha."""
        items = self.obtener_todos()
        for item in items:
            if (
                item["ruc"] == ruc and
                item["codigo_obligacion"] == codigo_obligacion and
                item["fecha_vencimiento"] == fecha_vencimiento
            ):
                return True
        return False

    def agregar_recordatorio(self, recordatorio: RecordatorioColaItem):
        items = self.obtener_todos()
        items.append(recordatorio.model_dump())
        self.guardar_todos(items)
        return True

    def actualizar_estado_envio(self, id_recordatorio: str, id_auditoria: str, usuario_confirmador: str, estado: str = "ENVIADO") -> Optional[RecordatorioColaItem]:
        items = self.obtener_todos()
        for it in items:
            if it["id_recordatorio"] == id_recordatorio:
                it["estado"] = estado
                it["fecha_ultimo_intento"] = datetime.now(timezone.utc).isoformat()
                if estado == "ENVIADO":
                    it["fecha_envio"] = it["fecha_ultimo_intento"]
                it["id_auditoria_envio"] = id_auditoria
                it["usuario_confirmador"] = usuario_confirmador
                self.guardar_todos(items)
                return RecordatorioColaItem(**it)
        return None

    def limpiar_cola(self):
        """Limpia el almacén de recordatorios (útil para pruebas)."""
        self.guardar_todos([])


_STORE_GLOBAL = SQLiteStore()
_DISPATCH_LOCK = threading.Lock()
_SCAN_LOCK = threading.Lock()


class EnvioInciertoError(RuntimeError):
    """El SMTP pudo haber aceptado un mensaje cuyo resultado no se confirmó."""


class ConsentimientoRequeridoError(RuntimeError):
    """El perfil no autoriza recordatorios para el destinatario actual."""


def _serializar_confirmacion(func):
    """Evita dos confirmaciones simultáneas del mismo proceso sobre la cola JSON."""
    @wraps(func)
    def wrapped(*args, **kwargs):
        with _DISPATCH_LOCK:
            return func(*args, **kwargs)
    return wrapped


def _serializar_escaneo(func):
    """Evita que el disparador diario y la ruta manual escriban a la vez."""
    @wraps(func)
    def wrapped(*args, **kwargs):
        with _SCAN_LOCK:
            return func(*args, **kwargs)
    return wrapped


# ==============================================================================
# MOTOR DEL FLUJO PROGRAMADO (TAREA DIARIA)
# ==============================================================================

def calcular_dias_habiles_entre(fecha_inicio: date, fecha_fin: date, feriados: List[Dict[str, Any]]) -> int:
    """Calcula el número de días hábiles entre dos fechas, descontando fines de semana y feriados."""
    if fecha_fin <= fecha_inicio:
        return 0

    dias_habiles = 0
    actual = fecha_inicio + timedelta(days=1)
    
    feriados_set = {(f.get("mes"), f.get("dia")) for f in feriados}

    while actual <= fecha_fin:
        # Lunes a Viernes (0 a 4)
        if actual.weekday() < 5 and (actual.month, actual.day) not in feriados_set:
            dias_habiles += 1
        actual += timedelta(days=1)

    return dias_habiles


@_serializar_escaneo
def ejecutar_tarea_diaria_recordatorios(
    fecha_referencia: Optional[date] = None,
    contribuyentes: Optional[List[Dict[str, Any]]] = None,
    store: Optional[ColaRecordatoriosStore] = None
) -> ResumenTareaDiaria:
    """
    Tarea programada diaria:
    1. Escanea todos los contribuyentes registrados.
    2. Calcula sus obligaciones mediante el motor determinista.
    3. Detecta aquellas que vencen dentro de la ventana de anticipación (5 días hábiles).
    4. Redacta el recordatorio con referencias normativas verificadas.
    5. Guarda el recordatorio con estado 'PENDIENTE_CONFIRMACION' (Compuerta HITL).
    """
    db = store or _STORE_GLOBAL
    hoy = fecha_referencia or date.today()
    if contribuyentes is not None:
        lista_contribuyentes = contribuyentes
    elif os.getenv("SCHEDULER_ALLOW_DEMO_PROFILES", "false").lower() in ("1", "true", "yes"):
        lista_contribuyentes = CONTRIBUYENTES_REGISTRADOS_DEFAULT
    else:
        lista_contribuyentes = db.listar_perfiles_consentidos()

    cfg_flujo = get_parametros_agente_flujo()
    dias_anticipacion = cfg_flujo.get("dias_anticipacion_alerta_diaria", 5)
    feriados = get_feriados_2026()

    recordatorios_generados: List[RecordatorioColaItem] = []
    total_vencimientos = 0
    omitidos_por_idempotencia = 0

    logger.info(f"Iniciando tarea programada para la fecha de referencia: {hoy.isoformat()} (Anticipación: {dias_anticipacion} días hábiles)")

    for c in lista_contribuyentes:
        try:
            inp_calc = CalcularVencimientosInput(
                ruc=c["ruc"],
                tipo_regimen=c["tipo_regimen"],
                anio=c.get("anio", 2026),
                tiene_actividades_excluidas=c.get("tiene_actividades_excluidas", False)
            )
            res_venc = tool_calcular_vencimientos(inp_calc)

            for evento in res_venc.eventos:
                fecha_venc = date.fromisoformat(evento["fecha_vencimiento"])
                
                # Solo evaluar vencimientos que aún no vencen o que vencen a corto plazo
                if fecha_venc >= hoy:
                    dias_habiles_faltantes = calcular_dias_habiles_entre(hoy, fecha_venc, feriados)
                    dias_calendario_faltantes = (fecha_venc - hoy).days

                    # Si está dentro de la ventana de anticipación
                    if 0 <= dias_habiles_faltantes <= dias_anticipacion:
                        total_vencimientos += 1
                        codigo_ob = evento["codigo_obligacion"]

                        # Verificar idempotencia
                        if db.existe_recordatorio_activo(c["ruc"], codigo_ob, evento["fecha_vencimiento"]):
                            omitidos_por_idempotencia += 1
                            continue

                        # Redactar recordatorio con el evento y año calculados
                        inp_red = RedactarRecordatorioInput(
                            codigo_obligacion=codigo_ob,
                            ruc=c["ruc"],
                            razon_social=c.get("razon_social", "Contribuyente"),
                            tipo_regimen=c["tipo_regimen"],
                            fecha_vencimiento=evento["fecha_vencimiento"],
                            titulo_obligacion=evento["titulo"],
                            anio_fiscal=res_venc.anio_fiscal,
                        )
                        out_red = tool_redactar_recordatorio(inp_red)

                        # Crear item de cola en estado PENDIENTE_CONFIRMACION
                        rec_item = RecordatorioColaItem(
                            id_recordatorio="REC-" + hashlib.sha256(
                                f"{c['ruc']}|{codigo_ob}|{evento['fecha_vencimiento']}".encode("utf-8")
                            ).hexdigest()[:32],
                            ruc=c["ruc"],
                            razon_social=c.get("razon_social", "Contribuyente"),
                            email=c.get("email", "contacto@sri.ec"),
                            tipo_regimen=c["tipo_regimen"],
                            codigo_obligacion=codigo_ob,
                            titulo_obligacion=evento["titulo"],
                            fecha_vencimiento=evento["fecha_vencimiento"],
                            dias_restantes=dias_calendario_faltantes,
                            asunto=out_red.asunto,
                            cuerpo_recordatorio=out_red.cuerpo_recordatorio,
                            citas_normativas=out_red.citas_normativas,
                            estado="PENDIENTE_CONFIRMACION",
                            fecha_generacion=datetime.now(timezone.utc).isoformat()
                        )

                        if db.agregar_recordatorio(rec_item):
                            recordatorios_generados.append(rec_item)
                        else:
                            omitidos_por_idempotencia += 1

        except Exception as e:
            logger.error("Error al procesar contribuyente: %s", type(e).__name__)

    logger.info(
        f"Tarea diaria completada. Evaluados: {len(lista_contribuyentes)}, "
        f"Vencimientos: {total_vencimientos}, Nuevos preparados: {len(recordatorios_generados)}, "
        f"Omitidos por idempotencia: {omitidos_por_idempotencia}"
    )

    return ResumenTareaDiaria(
        fecha_ejecucion=hoy.isoformat(),
        contribuyentes_evaluados=len(lista_contribuyentes),
        vencimientos_detectados=total_vencimientos,
        recordatorios_nuevos_generados=len(recordatorios_generados),
        recordatorios_existentes_omitidos=omitidos_por_idempotencia,
        recordatorios_preparados=recordatorios_generados,
        dias_anticipacion_configurados=dias_anticipacion
    )


def listar_recordatorios_pendientes(store: Optional[ColaRecordatoriosStore] = None) -> List[RecordatorioColaItem]:
    """Retorna recordatorios pendientes o con fallo seguro para revisión y reintento."""
    db = store or _STORE_GLOBAL
    items = db.obtener_todos()
    return [RecordatorioColaItem(**it) for it in items if it.get("estado") in ("PENDIENTE_CONFIRMACION", "SIMULADO", "ERROR_ENVIO")]


def listar_recordatorios_en_revision(store: Optional[ColaRecordatoriosStore] = None) -> List[RecordatorioColaItem]:
    """Muestra envíos inciertos que requieren verificación fuera del sistema."""
    db = store or _STORE_GLOBAL
    return [RecordatorioColaItem(**it) for it in db.obtener_todos() if it.get("estado") in ("ESTADO_INCIERTO", "EN_PROCESO")]


@_serializar_confirmacion
def confirmar_y_despachar_recordatorio(
    id_recordatorio: str,
    usuario_confirmador: str = "contador_autorizado",
    store: Optional[ColaRecordatoriosStore] = None
) -> EnviarRecordatorioOutput:
    """
    Compuerta Humana (HITL): Un operador/contador revisa el recordatorio redactado
    y autoriza formalmente su envío. Invoca tool_enviar_recordatorio con confirmacion=True.
    """
    db = store or _STORE_GLOBAL
    items = db.obtener_todos()
    item_encontrado = None

    for it in items:
        if it["id_recordatorio"] == id_recordatorio:
            item_encontrado = it
            break

    if not item_encontrado:
        raise ValueError(f"No se encontró el recordatorio con ID: {id_recordatorio}")

    if item_encontrado["estado"] == "ENVIADO":
        return EnviarRecordatorioOutput(
            estado="ENVIADO",
            destinatario=item_encontrado["email"],
            canal="email",
            confirmado=True,
            mensaje_accion="El recordatorio ya fue enviado previamente (idempotente).",
            timestamp=item_encontrado.get("fecha_envio", datetime.now(timezone.utc).isoformat()),
            id_registro_auditoria=item_encontrado.get("id_auditoria_envio"),
            usuario_confirmador=item_encontrado.get("usuario_confirmador"),
        )

    if item_encontrado["estado"] == "ESTADO_INCIERTO":
        raise EnvioInciertoError("El resultado del envío es incierto. Revise el servidor SMTP antes de reintentar.")

    if item_encontrado["estado"] == "EN_PROCESO":
        raise EnvioInciertoError("El envío está en proceso o quedó sin resultado. Revise el servidor SMTP.")

    if hasattr(db, "has_consent") and not db.has_consent(item_encontrado["ruc"], item_encontrado["email"]):
        raise ConsentimientoRequeridoError("El perfil no autoriza recordatorios para el destinatario actual.")

    if hasattr(db, "reservar_envio") and not db.reservar_envio(id_recordatorio):
        raise EnvioInciertoError("El recordatorio ya está siendo procesado o requiere revisión.")

    # Invocar herramienta formal con confirmación=True
    inp_envio = EnviarRecordatorioInput(
        destinatario=item_encontrado["email"],
        asunto=item_encontrado["asunto"],
        texto=item_encontrado["cuerpo_recordatorio"],
        confirmacion_usuario=True,
        canal="email"
    )
    try:
        out_envio = tool_enviar_recordatorio(inp_envio)
    except Exception:
        if hasattr(db, "reservar_envio"):
            db.actualizar_estado_envio(id_recordatorio, "AUD-RESULTADO-INCIERTO", usuario_confirmador, "ESTADO_INCIERTO")
        raise
    out_envio = out_envio.model_copy(update={"usuario_confirmador": usuario_confirmador})

    # Persistir exactamente el estado observado; solo ENVIADO registra fecha de envío.
    db.actualizar_estado_envio(
        id_recordatorio=id_recordatorio,
        id_auditoria=out_envio.id_registro_auditoria or "AUD-DEFAULT",
        usuario_confirmador=usuario_confirmador,
        estado=out_envio.estado,
    )

    return out_envio


def confirmar_todos_los_pendientes(
    usuario_confirmador: str = "contador_autorizado",
    store: Optional[ColaRecordatoriosStore] = None
) -> List[EnviarRecordatorioOutput]:
    """Confirma y despacha en lote todos los recordatorios pendientes de la cola."""
    pendientes = [p for p in listar_recordatorios_pendientes(store) if p.estado == "PENDIENTE_CONFIRMACION"]
    resultados = []
    for p in pendientes:
        try:
            res = confirmar_y_despachar_recordatorio(
                id_recordatorio=p.id_recordatorio,
                usuario_confirmador=usuario_confirmador,
                store=store
            )
            resultados.append(res)
        except ConsentimientoRequeridoError:
            logger.info("Recordatorio omitido por ausencia de consentimiento vigente.")
    return resultados
