"""
Esquemas Pydantic v2 del Dominio Tributario RIMPE (SRI Ecuador).
Define los contratos de datos, validaciones de entrada (RUC, email, montos),
y el esquema estructurado estricto para las respuestas generadas por Google Gemini Flash.
"""

from enum import Enum
from typing import List, Optional
from datetime import datetime, date
from pydantic import BaseModel, Field, EmailStr, field_validator, ConfigDict
from backend.services.calculator import validar_ruc_persona_natural


# ==============================================================================
# ENUMERACIONES DEL DOMINIO
# ==============================================================================

class TipoRegimen(str, Enum):
    """Regímenes tributarios contemplados en la normativa RIMPE."""
    RIMPE_NEGOCIO_POPULAR = "RIMPE_NEGOCIO_POPULAR"
    RIMPE_EMPRENDEDOR = "RIMPE_EMPRENDEDOR"


class CategoriaObligacion(str, Enum):
    """Categoría de la obligación tributaria."""
    RIMPE = "RIMPE"
    REGIMEN_GENERAL = "REGIMEN_GENERAL"


# ==============================================================================
# MODELOS DE PERFIL TRIBUTARIO DEL CONTRIBUYENTE
# ==============================================================================

class PerfilTributarioCreate(BaseModel):
    """Modelo para el registro y actualización del perfil del contribuyente."""
    model_config = ConfigDict(str_strip_whitespace=True)

    ruc: str = Field(
        ...,
        description="RUC de persona natural ecuatoriana (13 dígitos numéricos terminados en 001).",
        examples=["0923456784001"]
    )
    razon_social: str = Field(
        ...,
        min_length=3,
        max_length=150,
        description="Nombres y apellidos completos o razón social según el RUC.",
        examples=["Juan Pérez"]
    )
    nombre_comercial: Optional[str] = Field(
        default=None,
        max_length=150,
        description="Nombre de fantasía o comercial del negocio (opcional).",
        examples=["Bazar y Papelería El Sol"]
    )
    email: EmailStr = Field(
        ...,
        description="Correo electrónico válido para el envío de recordatorios y alertas.",
        examples=["contacto@miemprendimiento.ec"]
    )
    telefono: Optional[str] = Field(
        default=None,
        pattern=r"^\+?[0-9]{9,15}$",
        description="Número de teléfono móvil de contacto en formato numérico.",
        examples=["0991234567"]
    )
    tipo_regimen: TipoRegimen = Field(
        ...,
        description="Régimen tributario asignado por el SRI (RIMPE_NEGOCIO_POPULAR o RIMPE_EMPRENDEDOR)."
    )
    tiene_actividades_excluidas: bool = Field(
        default=False,
        description="Indica si percibe ingresos adicionales por servicios profesionales, arriendos, etc."
    )
    ingresos_brutos_anuales: Optional[float] = Field(
        default=0.0,
        ge=0.0,
        description="Ingresos brutos proyectados o del ejercicio fiscal anterior en USD.",
        examples=[18500.00]
    )
    correo_notificaciones: bool = Field(
        default=True,
        description="Bandera de consentimiento para el envío de recordatorios por email (LOPDP)."
    )

    @field_validator("ruc")
    @classmethod
    def validar_ruc(cls, v: str) -> str:
        v = v.strip()
        if not validar_ruc_persona_natural(v):
            raise ValueError(
                "El RUC ingresado no es válido para personas naturales en Ecuador. "
                "Debe tener 13 dígitos, provincia válida (01-24), tercer dígito < 6, "
                "cumplir algoritmo Módulo 10 y terminar en 001."
            )
        return v


class PerfilTributarioResponse(BaseModel):
    """Respuesta con el perfil del contribuyente registrado."""
    model_config = ConfigDict(from_attributes=True)

    id: str = Field(description="Identificador único del perfil registrado.")
    ruc: str
    razon_social: str
    nombre_comercial: Optional[str] = None
    email: str
    telefono: Optional[str] = None
    tipo_regimen: TipoRegimen
    tiene_actividades_excluidas: bool
    ingresos_brutos_anuales: float
    correo_notificaciones: bool
    noveno_digito: int = Field(description="Noveno dígito del RUC que rige los vencimientos.")
    fecha_creacion: str = Field(description="Fecha y hora de registro ISO.")


# ==============================================================================
# MODELOS DE CÁLCULO DE VENCIMIENTOS Y CALENDARIO
# ==============================================================================

class CalculoVencimientosRequest(BaseModel):
    """Solicitud para calcular vencimientos de obligaciones tributarias."""
    model_config = ConfigDict(str_strip_whitespace=True)

    ruc: str = Field(
        ...,
        description="RUC de persona natural ecuatoriana.",
        examples=["0923456784001"]
    )
    tipo_regimen: TipoRegimen = Field(
        ...,
        description="Régimen tributario a calcular."
    )
    anio: int = Field(
        default=2026,
        ge=2024,
        le=2030,
        description="Año del ejercicio fiscal sobre el cual se calculan los vencimientos.",
        examples=[2026]
    )
    tiene_actividades_excluidas: bool = Field(
        default=False,
        description="Indica si debe agregarse la obligación de régimen general."
    )

    @field_validator("ruc")
    @classmethod
    def validar_ruc(cls, v: str) -> str:
        v = v.strip()
        if not validar_ruc_persona_natural(v):
            raise ValueError("El RUC ingresado no cumple con el algoritmo Módulo 10 del SRI.")
        return v


class EventoCalendario(BaseModel):
    """Representa una obligación con fecha de vencimiento ajustada a días hábiles."""
    id: str = Field(description="Identificador único del evento para el frontend.")
    codigo_obligacion: str = Field(description="Código estándar de la obligación (e.g. IVA_SEMESTRAL_1).")
    titulo: str = Field(description="Título descriptivo de la obligación.")
    fecha_vencimiento: str = Field(description="Fecha final límite ajustada a días hábiles (YYYY-MM-DD).")
    fecha_nominal: str = Field(description="Fecha nominal teórica según noveno dígito (YYYY-MM-DD).")
    fue_trasladada: bool = Field(description="True si la fecha original cayó en fin de semana o feriado.")
    motivo_traslado: str = Field(description="Motivo del traslado (e.g. Sábado, Domingo, Feriado).")
    categoria: str = Field(description="Categoría (RIMPE o REGIMEN_GENERAL).")
    color_identificador: str = Field(description="Color hexadecimal para renderizar en el calendario mensual.")
    formulario_sri: str = Field(description="Nombre o número de formulario oficial del SRI.")
    descripcion: str = Field(description="Resumen explicativo determinista de la obligación.")


class CalendarioTributarioResponse(BaseModel):
    """Respuesta consolidada del calendario tributario para el contribuyente."""
    ruc: str
    noveno_digito: int
    tipo_regimen: TipoRegimen
    anio_fiscal: int
    tiene_actividades_excluidas: bool
    total_obligaciones: int
    eventos: List[EventoCalendario]


# ==============================================================================
# MODELO ESTRUCTURADO ESTRICTO PARA GENERACIÓN CON LLM (GEMINI)
# ==============================================================================

class RecordatorioEstructurado(BaseModel):
    """
    Esquema JSON estricto exigido al modelo Google Gemini Flash.
    Garantiza que la IA nunca invente fechas ni montos, concentrándose en la
    pedagogía, la cita legal oficial y las consecuencias de incumplimiento.
    """
    model_config = ConfigDict(str_strip_whitespace=True)

    codigo_obligacion: str = Field(
        ...,
        description="Código de la obligación explicada (e.g. IVA_SEMESTRAL_1, RENTA_ANUAL_EMPRENDEDOR)."
    )
    titulo_pedagogico: str = Field(
        ...,
        description="Título claro, amigable y comprensible para el emprendedor."
    )
    fecha_limite_formateada: str = Field(
        ...,
        description="Fecha límite máxima en lenguaje natural (ej. 'Lunes 20 de Julio de 2026')."
    )
    base_legal_oficial: str = Field(
        ...,
        description="Artículos específicos de la LRTI, RALRTI o Resoluciones SRI que fundamentan la obligación."
    )
    explicacion_sencilla: str = Field(
        ...,
        description="Explicación clara en 2 o 3 párrafos cortos sin tecnicismos innecesarios."
    )
    consecuencia_incumplimiento: str = Field(
        ...,
        description="Multas, intereses y recargos aplicables según el Código Tributario y el Art. 100 de la LRTI."
    )
    sugerencia_accion: str = Field(
        ...,
        description="Pasos recomendados a seguir en el portal SRI en Línea para cumplir a tiempo."
    )
    canal_recomendado: str = Field(
        ...,
        description="Canal oficial para el trámite (ej. 'Portal SRI en Línea > Declaraciones > Declaración de Impuestos')."
    )


class ExplicacionObligacionRequest(BaseModel):
    """Solicitud enviada al backend para generar la explicación pedagógica con IA."""
    model_config = ConfigDict(str_strip_whitespace=True)

    codigo_obligacion: str = Field(
        ...,
        min_length=3,
        description="Código de la obligación (e.g. IVA_SEMESTRAL_1, RENTA_ANUAL_EMPRENDEDOR)."
    )
    tipo_regimen: TipoRegimen = Field(
        ...,
        description="Régimen RIMPE del contribuyente."
    )
    fecha_vencimiento: str = Field(
        ...,
        pattern=r"^\d{4}-\d{2}-\d{2}$",
        description="Fecha de vencimiento calculada determinísticamente (YYYY-MM-DD)."
    )
    ingresos_estimados: Optional[float] = Field(
        default=None,
        ge=0.0,
        description="Ingresos brutos anuales para contextualizar la explicación si aplica."
    )
    tiene_actividades_excluidas: bool = Field(
        default=False,
        description="Indica si el contribuyente mantiene actividades excluidas."
    )
    es_declaracion_en_cero: bool = Field(
        default=False,
        description="Indica si el contribuyente no tuvo ventas ni compras y debe declarar en cero."
    )
    contexto_adicional: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Pregunta específica o contexto del emprendedor para enriquecer la explicación."
    )


class ExplicacionObligacionResponse(BaseModel):
    """Respuesta del endpoint con la explicación estructurada generada por Gemini."""
    obligacion: RecordatorioEstructurado
    modelo_utilizado: str = Field(
        default="gemini-2.0-flash",
        description="Nombre exacto del modelo generativo utilizado."
    )
    tokens_utilizados: Optional[int] = Field(
        default=None,
        description="Total de tokens consumidos (prompt + respuesta)."
    )
    tiempo_generacion_ms: Optional[float] = Field(
        default=None,
        description="Latencia de inferencia en milisegundos."
    )
    fuente_conocimiento: str = Field(
        default="Normativa oficial SRI Ecuador (Resoluciones NAC-24-0027, NAC-23-0034, LRTI, Ley de Eficiencia Económica).",
        description="Documentos oficiales SRI utilizados como base para la explicación."
    )


# ==============================================================================
# MODELOS DE SIMULACIÓN DE IMPUESTO A LA RENTA
# ==============================================================================

class SimulacionRentaRequest(BaseModel):
    """Solicitud de cálculo determinista de cuota estimada de impuesto a la renta."""
    ingresos_brutos: float = Field(
        ...,
        ge=0.0,
        description="Ingresos brutos totales gravados en el ejercicio fiscal (USD)."
    )
    tipo_regimen: TipoRegimen = Field(
        ...,
        description="Régimen bajo el cual se realizará la simulación."
    )


class SimulacionRentaResponse(BaseModel):
    """Respuesta con el desglose exacto de la cuota calculada."""
    tipo_regimen: TipoRegimen
    ingresos_brutos: float
    cuota_fija_usd: Optional[float] = None
    fraccion_basica: Optional[float] = None
    tipo_marginal: Optional[str] = None
    impuesto_causado: float
    tramo_aplicado: Optional[str] = None
    alerta_transicion: Optional[str] = None
    nota: Optional[str] = None
