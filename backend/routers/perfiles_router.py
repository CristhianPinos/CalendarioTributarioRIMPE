"""Registro privado de perfiles para el escaneo periódico consentido."""

import os
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import Field

from backend.operator_auth import require_operator
from backend.schemas import PerfilTributarioCreate
from backend.services.scheduler import _STORE_GLOBAL


router = APIRouter(prefix="/api/perfiles", tags=["Perfiles registrados"],
                   dependencies=[Depends(require_operator)])


class PerfilPersistenteRequest(PerfilTributarioCreate):
    anio: int = Field(default=2026, ge=2024, le=2030)
    correo_notificaciones: bool = Field(default=False)


@router.post("")
def guardar_perfil(payload: PerfilPersistenteRequest):
    """Guarda o actualiza el perfil; la autorización de correo es explícita."""
    if os.getenv("RIMPE_DEMO_READONLY", "false").lower() in ("1", "true", "yes"):
        raise HTTPException(status_code=503, detail="El registro de perfiles no está disponible en la demostración.")
    return _STORE_GLOBAL.upsert_profile(payload.model_dump(mode="json"))


@router.get("")
def listar_perfiles() -> List[dict]:
    return _STORE_GLOBAL.listar_perfiles()


@router.get("/{ruc}")
def obtener_perfil(ruc: str) -> dict:
    profile = _STORE_GLOBAL.get_profile(ruc)
    if profile is None:
        raise HTTPException(status_code=404, detail="No se encontró el perfil solicitado.")
    return profile
