"""Autorización del operador para acciones sobre recordatorios."""

import os
import secrets
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials


_basic = HTTPBasic(auto_error=False)


def optional_operator(
    credentials: Optional[HTTPBasicCredentials] = Depends(_basic),
) -> Optional[str]:
    """Valida credenciales si se presentan, sin exigirlas para preparar contenido."""
    if credentials is None:
        return None

    configured_user = os.getenv("REMINDER_OPERATOR_USER", "")
    configured_password = os.getenv("REMINDER_OPERATOR_PASSWORD", "")
    if not configured_user or len(configured_password) < 16:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="La autorización de operadores no está configurada.",
        )

    valid_user = secrets.compare_digest(credentials.username, configured_user)
    valid_password = secrets.compare_digest(credentials.password, configured_password)
    if not (valid_user and valid_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales de operador inválidas.",
            headers={"WWW-Authenticate": "Basic"},
        )
    return configured_user


def require_operator(operator: Optional[str] = Depends(optional_operator)) -> str:
    """Exige un operador configurado y autenticado antes de una acción privilegiada."""
    if not os.getenv("REMINDER_OPERATOR_USER") or len(os.getenv("REMINDER_OPERATOR_PASSWORD", "")) < 16:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="La autorización de operadores no está configurada.",
        )
    if operator is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Se requiere autenticación de operador.",
            headers={"WWW-Authenticate": "Basic"},
        )
    return operator


def require_dispatch_operator(operator: Optional[str]) -> str:
    """Comprueba la identidad de una operación de despacho condicional."""
    if operator is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Se requiere autenticación de operador para despachar.",
            headers={"WWW-Authenticate": "Basic"},
        )
    return operator
