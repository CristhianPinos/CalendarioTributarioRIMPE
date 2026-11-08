"""
Router de Consultas RAG para Normativa Tributaria RIMPE (SRI Ecuador).
Asignatura: Ingeniería de Software con IA Generativa
Caso N.º 11 – Grupo 11: Calendario Tributario RIMPE

Provee endpoints para responder preguntas con citas obligatorias,
filtros por régimen tributario y mecanismo de abstención auditado.
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Optional

from backend.services.rag_service import (
    responder_con_rag,
    ConsultaRAGRequest,
    ConsultaRAGResponse
)

router = APIRouter(
    prefix="/api/rag",
    tags=["RAG Normativo"]
)


@router.post("/consultar", response_model=ConsultaRAGResponse)
def consultar_normativa_rag(payload: ConsultaRAGRequest):
    """
    Consulta la base de conocimiento normativa del SRI (RAG 2026).
    Retorna la respuesta con citas legales obligatorias ([LRTI, Art. X])
    o activa la política de abstención si no hay sustento en las fuentes.
    """
    try:
        resultado = responder_con_rag(
            pregunta=payload.pregunta,
            regimen=payload.regimen,
            top_k=payload.top_k
        )
        return resultado
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="No se pudo procesar la consulta normativa."
        )
