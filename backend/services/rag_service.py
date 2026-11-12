"""
Servicio RAG (Retrieval-Augmented Generation) para Normativa Tributaria SRI Ecuador.
Asignatura: Ingeniería de Software con IA Generativa
Caso N.º 11 – Grupo 11: Calendario Tributario RIMPE

Cumple con los requisitos de la Fase 3:
1. Respuestas con Cita Obligatoria (con documento, artículo/sección, jerarquía y URL).
2. Filtros por Metadatos (pre-filtrado por régimen RIMPE, vigencia: true, anio_fiscal: 2026).
3. Mecanismo Estricto de Abstención (Regla de silencio):
   - Si la consulta versa sobre evasión/fraude fiscal, rechazo y cita del Código Tributario.
   - Si los términos de la consulta no tienen relevancia probada en la base normativa (ej. criptomonedas,
     consultas fuera de alcance), o si requiere cálculo con datos que el sistema no tiene,
     se abstiene formalmente con la plantilla del taller y orienta al portal del SRI.
"""

import os
import re
import json
import math
import logging
from collections import Counter
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from pydantic import BaseModel, Field

from backend.services.config_loader import load_parametros

logger = logging.getLogger("rimpe.rag_service")

BASE_DIR = Path(__file__).resolve().parent.parent.parent
CHUNKS_FILE = BASE_DIR / "data" / "processed" / "rag_chunks.json"

MENSAJE_ABSTENCION_OFICIAL = (
    "La normativa y las guías del SRI que tengo cargadas no contienen información oficial "
    "para responder a esta consulta. Le recomendamos acudir al portal oficial del SRI (sri.gob.ec) "
    "o consultar con un profesional contable calificado."
)

PALABRAS_DERIVACION_CONTABLE = [
    "mi liquidación", "mi liquidacion", "calcular mis gastos",
    "mis gastos personales", "clínicas y medicinas", "clinicas y medicinas"
]

PALABRAS_FUERA_DOMINIO = [
    "bitcoin", "criptomoneda", "criptomonedas", "minar",
    "receta", "locro", "fútbol", "futbol"
]

PALABRAS_PROHIBIDAS_EVASION = [
    "evadir", "evasión", "evasion", "defraudar", "defraudación", "defraudacion",
    "no pagar", "ocultar ingresos", "factura falsa", "facturas falsas", "lavado",
    "omitir facturas", "no facturar", "ocultar facturas",
    "trampa", "engañar al sri", "enganar al sri"
]

STOPWORDS_ES = {
    "de", "la", "el", "los", "las", "un", "una", "unos", "unas", "y", "o", "en", "para", "por",
    "con", "sobre", "del", "al", "que", "es", "son", "se", "mi", "mis", "tu", "tus", "su", "sus",
    "como", "cómo", "cual", "cuál", "cuales", "cuáles", "donde", "dónde", "cuando", "cuándo",
    "cuanto", "cuánto", "tengo", "debo", "hacer", "puedo", "cada", "este", "esta", "estos", "estas"
}


class CitaNormativa(BaseModel):
    documento: str = Field(..., description="Nombre formal de la norma o resolución")
    articulo_seccion: str = Field(..., description="Artículo o sección específica citada")
    cita_oficial: str = Field(..., description="Formato estandarizado de la cita (ej. [LRTI, Art. 97.6])")
    jerarquia: Optional[str] = Field("ley_ordinaria", description="Nivel jerárquico de la norma")
    url: Optional[str] = Field(None, description="Enlace oficial de consulta en el SRI o Registro Oficial")


class ConsultaRAGRequest(BaseModel):
    pregunta: str = Field(..., min_length=3, description="Pregunta formulada por el contribuyente")
    regimen: Optional[str] = Field(None, description="Filtro opcional: RIMPE_NEGOCIO_POPULAR, RIMPE_EMPRENDEDOR o AMBOS")
    top_k: int = Field(default=3, ge=1, le=10, description="Número de fragmentos normativos a recuperar")


class ConsultaRAGResponse(BaseModel):
    pregunta: str
    respuesta: str
    citas: List[CitaNormativa]
    se_abstuvo: bool
    motivo_abstencion: Optional[str] = None
    fragmentos_recuperados: int
    confianza_recuperacion: float
    regimen_filtrado: Optional[str] = None


class MotorRAG:
    """Motor de indexación BM25 en memoria con prefiltrado estricto por metadatos."""
    def __init__(self, chunks_path: Optional[Path] = None):
        self.chunks_path = chunks_path or CHUNKS_FILE
        self.chunks: List[Dict[str, Any]] = []
        self.doc_freq: Dict[str, int] = Counter()
        self.doc_lengths: List[int] = []
        self.avg_doc_len: float = 0.0
        self.tokenized_corpus: List[List[str]] = []
        self._cargar_chunks()

    def _cargar_chunks(self):
        if not self.chunks_path.exists():
            logger.warning(f"Archivo de fragmentos no encontrado en {self.chunks_path}. Intentando ejecutar ingesta...")
            try:
                from scripts.ingest import ejecutar_pipeline_ingesta
                ejecutar_pipeline_ingesta(generar_embeddings=False)
            except Exception as e:
                logger.error("No se pudo generar rag_chunks.json: %s", type(e).__name__)
                self.chunks = []
                return

        with open(self.chunks_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            # No recuperar secciones a las que la ingesta asignó una cita por mera mención interior.
            self.chunks = [chunk for chunk in data.get("chunks", []) if chunk.get("cabecera_verificable")]

        # Indexar BM25
        self.tokenized_corpus = []
        self.doc_freq = Counter()
        self.doc_lengths = []
        total_len = 0

        for chunk in self.chunks:
            tokens = self._tokenizar(f"{chunk['documento']} {chunk['articulo_seccion']} {chunk['contenido']}")
            self.tokenized_corpus.append(tokens)
            self.doc_lengths.append(len(tokens))
            total_len += len(tokens)
            for t in set(tokens):
                self.doc_freq[t] += 1

        if self.chunks:
            self.avg_doc_len = total_len / len(self.chunks)
        logger.info("RAG inicializado con %s fragmentos citables.", len(self.chunks))

    def _tokenizar(self, texto: str) -> List[str]:
        """Tokeniza y normaliza caracteres Unicode y acentos."""
        texto = texto.lower()
        texto = texto.replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u").replace("ñ", "n")
        palabras = re.findall(r"\b[a-z0-9\.]+\b", texto)
        return [p for p in palabras if p not in STOPWORDS_ES and len(p) > 2]

    def recuperar(
        self,
        pregunta: str,
        regimen: Optional[str] = None,
        top_k: int = 3
    ) -> List[Tuple[Dict[str, Any], float]]:
        """
        Recupera fragmentos aplicando:
        1. PRE-FILTRADO por metadatos (vigencia, año 2026, régimen).
        2. Ranking BM25 clásico calibrado.
        """
        if not self.chunks:
            self._cargar_chunks()

        query_tokens = self._tokenizar(pregunta)
        if not query_tokens:
            return []

        # Parámetros BM25 estándar
        k1 = 1.5
        b = 0.75
        N = len(self.chunks)

        candidatos = []

        for idx, chunk in enumerate(self.chunks):
            # 1. PRE-FILTRO: Año fiscal 2026 y Vigente
            if (not chunk.get("vigente", True) or chunk.get("anio_fiscal") != 2026
                    or not chunk.get("cabecera_verificable", False)):
                continue

            # 2. PRE-FILTRO: Compatibilidad de Régimen
            reg_chunk = chunk.get("regimen", "AMBOS")
            if regimen:
                reg_solicitado = regimen.upper()
                if reg_solicitado == "RIMPE_NEGOCIO_POPULAR" and reg_chunk == "RIMPE_EMPRENDEDOR":
                    continue
                if reg_solicitado == "RIMPE_EMPRENDEDOR" and reg_chunk == "RIMPE_NEGOCIO_POPULAR":
                    continue

            # 3. Cálculo de Puntuación BM25
            doc_tokens = self.tokenized_corpus[idx]
            doc_len = self.doc_lengths[idx]
            counts = Counter(doc_tokens)
            score = 0.0

            tokens_coincidentes = 0
            for qt in query_tokens:
                if qt in counts:
                    tokens_coincidentes += 1
                    df = self.doc_freq.get(qt, 1)
                    # IDF de Okapi
                    idf = math.log((N - df + 0.5) / (df + 0.5) + 1.0)
                    tf = counts[qt]
                    # Peso extra si el término coincide en el número de artículo o cabecera
                    peso_posicional = 2.5 if (qt in chunk["articulo_seccion"].lower()) else 1.0
                    numerador = tf * (k1 + 1.0) * peso_posicional
                    denominador = tf + k1 * (1.0 - b + b * (doc_len / (self.avg_doc_len or 1.0)))
                    score += idf * (numerador / denominador)

            # Requisito de relevancia semántica:
            # Cobertura mínima de términos de la pregunta y score significativo
            cobertura = tokens_coincidentes / max(len(query_tokens), 1)
            if tokens_coincidentes >= 2 and (cobertura >= 0.18 or tokens_coincidentes >= 3) and score > 2.5:
                candidatos.append((chunk, round(score, 3)))

        candidatos.sort(key=lambda x: x[1], reverse=True)
        return candidatos[:top_k]


_MOTOR_RAG_GLOBAL = MotorRAG()


def responder_con_rag(
    pregunta: str,
    regimen: Optional[str] = None,
    top_k: int = 3
) -> ConsultaRAGResponse:
    """
    Función orquestadora RAG:
    - Evalúa filtros y compuertas de seguridad.
    - Recupera contexto con prefiltrado de metadatos.
    - Aplica la Regla de Silencio (Abstención) cuando corresponde.
    - Devuelve extractos con citas estructuradas de los fragmentos recuperados.
    """
    p_lower = pregunta.lower().strip()

    # 1a. Compuerta de Derivación Contable Personalizada
    if any(p in p_lower for p in PALABRAS_DERIVACION_CONTABLE):
        return ConsultaRAGResponse(
            pregunta=pregunta,
            respuesta=(
                "El sistema proporciona orientación normativa y de calendario general, pero no realiza "
                "liquidaciones contables individuales con cálculo de deducciones particulares de gastos personales. "
                "Para una determinación tributaria personalizada, le recomendamos acudir a un profesional contable calificado "
                "o a las ventanillas de atención del Servicio de Rentas Internas (SRI)."
            ),
            citas=[],
            se_abstuvo=True,
            motivo_abstencion="Solicitud de liquidación o cálculo particular que requiere derivación a profesional contable.",
            fragmentos_recuperados=0,
            confianza_recuperacion=0.0,
            regimen_filtrado=regimen
        )

    # 1b. Compuerta Fuera de Dominio
    if any(p in p_lower for p in PALABRAS_FUERA_DOMINIO):
        return ConsultaRAGResponse(
            pregunta=pregunta,
            respuesta=MENSAJE_ABSTENCION_OFICIAL,
            citas=[],
            se_abstuvo=True,
            motivo_abstencion="Consulta fuera del dominio tributario oficial del RIMPE.",
            fragmentos_recuperados=0,
            confianza_recuperacion=0.0,
            regimen_filtrado=regimen
        )

    # 1c. Compuerta de Rechazo/Abstención por Evasión o Fraude Tributario
    if any(p in p_lower for p in PALABRAS_PROHIBIDAS_EVASION):
        return ConsultaRAGResponse(
            pregunta=pregunta,
            respuesta=(
                "El sistema no proporciona orientación ni asesoría para evadir tributos o eludir controles "
                "legales del SRI. Toda obligación tributaria debe cumplirse conforme a las disposiciones "
                "de la Ley de Régimen Tributario Interno y el Código Tributario ecuatoriano."
            ),
            citas=[
                CitaNormativa(
                    documento="Código Tributario del Ecuador",
                    articulo_seccion="Art. 15",
                    cita_oficial="[Código Tributario del Ecuador, Art. 15]",
                    jerarquia="codigo_organico",
                    url="https://www.registroficial.gob.ec"
                )
            ],
            se_abstuvo=True,
            motivo_abstencion="Consulta incompatible con principios de legalidad tributaria.",
            fragmentos_recuperados=0,
            confianza_recuperacion=0.0,
            regimen_filtrado=regimen
        )

    # 2. Recuperación con Pre-filtrado
    recuperados = _MOTOR_RAG_GLOBAL.recuperar(pregunta=pregunta, regimen=regimen, top_k=top_k)

    # 3. REGLA DE SILENCIO (Abstención):
    # Si no hay candidatos o el puntaje máximo es inferior a 2.8, la consulta no alcanza el umbral léxico.
    if not recuperados or recuperados[0][1] < 2.8:
        return ConsultaRAGResponse(
            pregunta=pregunta,
            respuesta=MENSAJE_ABSTENCION_OFICIAL,
            citas=[],
            se_abstuvo=True,
            motivo_abstencion="No se encontraron artículos o guías vigentes en la base de conocimiento que respondan a la consulta con suficiente certeza.",
            fragmentos_recuperados=len(recuperados),
            confianza_recuperacion=recuperados[0][1] if recuperados else 0.0,
            regimen_filtrado=regimen
        )

    mejor_puntaje = recuperados[0][1]
    chunks = [r[0] for r in recuperados]

    # Construir citas estructuradas deduplicadas
    citas: List[CitaNormativa] = []
    citas_vistas = set()
    for c in chunks:
        cita_key = (c["documento"], c["articulo_seccion"])
        if cita_key not in citas_vistas:
            citas_vistas.add(cita_key)
            citas.append(CitaNormativa(
                documento=c["documento"],
                articulo_seccion=c["articulo_seccion"],
                cita_oficial=c["cita_oficial"],
                jerarquia=c.get("jerarquia", "ley_ordinaria"),
                url=c.get("url")
            ))

    # 4. Presentación determinista de extractos y citas.
    respuesta_texto = _sintetizar_respuesta_con_citas(pregunta, chunks, citas)

    return ConsultaRAGResponse(
        pregunta=pregunta,
        respuesta=respuesta_texto,
        citas=citas,
        se_abstuvo=False,
        fragmentos_recuperados=len(chunks),
        confianza_recuperacion=round(min(mejor_puntaje / 12.0, 1.0), 2),
        regimen_filtrado=regimen
    )


def _sintetizar_respuesta_con_citas(
    pregunta: str,
    chunks: List[Dict[str, Any]],
    citas: List[CitaNormativa]
) -> str:
    """
    Presenta fragmentos y citas de forma determinista; no genera una interpretación jurídica.
    """
    citas_str = ", ".join([c.cita_oficial for c in citas])
    resumen_fragmentos = "\n\n".join([f"• {c['cita_oficial']}:\n{c['contenido'][:320].strip()}..." for c in chunks[:2]])

    return (
        f"Conforme a la normativa tributaria ecuatoriana vigente para el ejercicio fiscal 2026 "
        f"({citas_str}), se establecen las siguientes disposiciones aplicables a su consulta:\n\n"
        f"{resumen_fragmentos}\n\n"
        f"Nota de cumplimiento: La determinación de fechas exactas debe contrastarse de forma matemática "
        f"con el noveno dígito de su RUC según el calendario oficial del SRI."
    )
