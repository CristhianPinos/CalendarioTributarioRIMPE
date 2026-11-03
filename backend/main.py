"""
API Backend - Calendario Tributario RIMPE
Asignatura: Ingeniería de Software con IA Generativa
Caso N.º 11 – Grupo 11
"""

import os
import json
from datetime import datetime, timezone
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from backend.middleware.logging_lopdp import LoggingLOPDPMiddleware
from backend.routers.obligaciones_router import router as obligaciones_router
from backend.routers.calendario_router import router as calendario_router
from backend.routers.rag_router import router as rag_router
from backend.routers.agente_router import router as agente_router
from backend.routers.flujo_router import router as flujo_router

# Cargar variables de entorno desde .env si existe
load_dotenv()

APP_VERSION = "3.2.0"
PROJECT_NAME = "Calendario Tributario RIMPE"

app = FastAPI(
    title="API Calendario Tributario RIMPE (SRI Ecuador)",
    description=(
        "Backend inteligente para el cálculo determinista de obligaciones tributarias, "
        "motor RAG con citas normativas obligatorias y política de abstención, "
        "agente con 4 herramientas tipadas y límite de iteraciones, "
        "flujo programado diario con compuerta de confirmación humana (HITL), "
        "y observabilidad conforme a la Ley Orgánica de Protección de Datos Personales (LOPDP)."
    ),
    version=APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc"
)

# 1. Middleware de observabilidad y privacidad LOPDP
app.add_middleware(LoggingLOPDPMiddleware)

# 2. Configuración de CORS para permitir la integración con React (Vite / CRA)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. Inclusión de Routers
app.include_router(calendario_router)
app.include_router(obligaciones_router)
app.include_router(rag_router)
app.include_router(agente_router)
app.include_router(flujo_router)


CONFIG_PATH = Path(os.getenv("SRI_RULES_PATH", "./config/sri_rules_2026.json"))


def check_config_loaded() -> bool:
    """Verifica la existencia y validez del archivo de configuración tributaria."""
    try:
        if CONFIG_PATH.exists():
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                return "calendario_noveno_digito" in data and "meses_declaracion" in data
        return False
    except Exception:
        return False


@app.get("/", tags=["Sistema"])
def read_root():
    """Ruta raíz de bienvenida e información del estado del servicio."""
    return {
        "proyecto": PROJECT_NAME,
        "version": APP_VERSION,
        "fase": "Fase 3 - RAG, Agente, Flujo Programado y Calidad (Semana 3)",
        "estado": "operativo",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "config_cargada": check_config_loaded(),
        "documentacion": "/docs"
    }


@app.get("/health", tags=["Sistema"])
def health_check():
    """Endpoint de salud del backend para monitoreo continuo y pruebas."""
    config_ok = check_config_loaded()
    gemini_key_present = bool(os.getenv("GEMINI_API_KEY"))

    return {
        "status": "healthy" if config_ok else "degraded",
        "service": "backend-fastapi",
        "version": APP_VERSION,
        "checks": {
            "sri_rules_config": config_ok,
            "gemini_api_key_configured": gemini_key_present,
            "rag_chunks_available": Path("data/processed/rag_chunks.json").exists()
        },
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
