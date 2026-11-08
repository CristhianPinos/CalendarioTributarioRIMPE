"""
API Backend - Calendario Tributario RIMPE
Asignatura: Ingeniería de Software con IA Generativa
Caso N.º 11 – Grupo 11
"""

import os
import json
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

# La ruta SQLite y la configuración del planificador se leen al importar servicios.
load_dotenv()

from backend.middleware.logging_lopdp import LoggingLOPDPMiddleware
from backend.routers.obligaciones_router import router as obligaciones_router
from backend.routers.calendario_router import router as calendario_router
from backend.routers.rag_router import router as rag_router
from backend.routers.agente_router import router as agente_router
from backend.routers.flujo_router import router as flujo_router
from backend.routers.perfiles_router import router as perfiles_router
from backend.services.periodic_scan import PeriodicScanRunner

# El log de acceso por defecto incluye URLs aportadas por el cliente; el middleware
# registra método, plantilla de ruta, estado y latencia sin identificadores.
logging.getLogger("uvicorn.access").disabled = True

APP_VERSION = "3.2.0"
PROJECT_NAME = "Calendario Tributario RIMPE"
periodic_scan_runner = None
BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIST = BASE_DIR / "frontend" / "dist"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Inicia y detiene el escaneo periódico junto con la aplicación."""
    global periodic_scan_runner
    periodic_scan_runner = PeriodicScanRunner()
    periodic_scan_runner.start()
    try:
        yield
    finally:
        periodic_scan_runner.stop()

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
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)


@app.exception_handler(RequestValidationError)
async def safe_validation_error(request, exc: RequestValidationError):
    """Conserva ubicación y tipo del error 422 sin devolver valores recibidos."""
    errors = [
        {
            "loc": error.get("loc", ()),
            "msg": "Campo obligatorio." if error.get("type") == "missing" else "Valor inválido.",
            "type": error.get("type", "value_error"),
        }
        for error in exc.errors()
    ]
    return JSONResponse(status_code=422, content={"detail": errors})

# 1. Middleware de observabilidad y privacidad LOPDP
app.add_middleware(LoggingLOPDPMiddleware)

# 2. En producción el frontend comparte origen; en desarrollo se permite Vite local.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in os.getenv(
        "CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
    ).split(",") if origin.strip()],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. Inclusión de Routers
app.include_router(calendario_router)
app.include_router(obligaciones_router)
app.include_router(rag_router)
app.include_router(agente_router)
app.include_router(flujo_router)
app.include_router(perfiles_router)

if (FRONTEND_DIST / "assets").is_dir():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="frontend-assets")


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
    if (FRONTEND_DIST / "index.html").is_file():
        return FileResponse(FRONTEND_DIST / "index.html", media_type="text/html")
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
        "demo_readonly": os.getenv("RIMPE_DEMO_READONLY", "false").lower() in ("1", "true", "yes"),
        "checks": {
            "sri_rules_config": config_ok,
            "gemini_api_key_configured": gemini_key_present,
            "rag_chunks_available": Path("data/processed/rag_chunks.json").exists()
        },
        "periodic_scan": {
            "enabled": periodic_scan_runner.enabled if periodic_scan_runner else False,
            "last_run_at": periodic_scan_runner.last_run_at if periodic_scan_runner else None,
            "last_result": periodic_scan_runner.last_result if periodic_scan_runner else None,
        },
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
