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

# Cargar variables de entorno desde .env si existe
load_dotenv()

APP_VERSION = "2.0.0"
PROJECT_NAME = "Calendario Tributario RIMPE"

app = FastAPI(
    title="API Calendario Tributario RIMPE (SRI Ecuador)",
    description=(
        "Backend inteligente para el cálculo determinista de obligaciones tributarias, "
        "explicaciones pedagógicas con Google Gemini Flash bajo esquema estructurado, "
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


CONFIG_PATH = Path(os.getenv("SRI_RULES_PATH", "./config/sri_rules_2026.json"))


def check_config_loaded() -> bool:
    """Verifica la existencia y validez del archivo de configuración tributaria."""
    try:
        if CONFIG_PATH.exists():
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                return "calendario_noveno_digito" in data
        return False
    except Exception:
        return False


@app.get("/", tags=["General"])
def root():
    """Endpoint raíz con metadatos del proyecto y enlaces útiles."""
    return {
        "proyecto": PROJECT_NAME,
        "caso": "Caso 11 - Grupo 11",
        "descripcion": "Calendario Tributario Personalizado con Recordatorios para Emprendedores RIMPE",
        "version": APP_VERSION,
        "documentacion": "/docs",
        "salud": "/health"
    }


@app.get("/health", tags=["Monitoreo"])
def health_check():
    """
    Endpoint de verificación de salud del servicio (Health Check).
    Verifica que el servicio esté respondiendo, reporta el entorno y el estado de la configuración.
    """
    config_ok = check_config_loaded()

    return {
        "status": "ok",
        "project": "CalendarioTributarioRIMPE",
        "version": APP_VERSION,
        "environment": os.getenv("ENVIRONMENT", "development"),
        "llm_provider": os.getenv("LLM_PROVIDER", "gemini"),
        "gemini_model": os.getenv("GEMINI_MODEL", "gemini-3-flash-preview"),
        "config_loaded": config_ok,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


if __name__ == "__main__":
    import uvicorn
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("backend.main:app", host=host, port=port, reload=True)
