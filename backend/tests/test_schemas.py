"""
Pruebas Unitarias para los Esquemas de Dominio Pydantic v2 (backend/schemas.py).
Valida:
1. Rechazo estricto con ValidationError (HTTP 422) ante datos vacíos, RUC inválido o emails malformados.
2. Comportamiento de Enums para tipos de régimen tributario.
3. Validación estricta del esquema de respuesta de la IA (RecordatorioEstructurado).
4. Límites de rangos numéricos y formatos de fecha.
"""

import pytest
from pydantic import ValidationError
from backend.schemas import (
    TipoRegimen,
    CategoriaObligacion,
    PerfilTributarioCreate,
    CalculoVencimientosRequest,
    ExplicacionObligacionRequest,
    RecordatorioEstructurado,
    SimulacionRentaRequest
)


class TestPerfilTributarioCreateValidation:
    """Valida los campos del registro de perfil tributario."""

    def test_perfil_valido(self):
        data = {
            "ruc": "0923456784001",
            "razon_social": "Carlos Alberto Moreira",
            "nombre_comercial": "Tienda Don Carlos",
            "email": "carlos.moreira@example.com",
            "telefono": "0991234567",
            "tipo_regimen": "RIMPE_NEGOCIO_POPULAR",
            "tiene_actividades_excluidas": False,
            "ingresos_brutos_anuales": 15000.0,
            "correo_notificaciones": True
        }
        perfil = PerfilTributarioCreate(**data)
        assert perfil.ruc == "0923456784001"
        assert perfil.tipo_regimen == TipoRegimen.RIMPE_NEGOCIO_POPULAR
        assert perfil.email == "carlos.moreira@example.com"

    def test_perfil_error_ruc_invalido(self):
        data = {
            "ruc": "0923456785001",  # Dígito verificador erróneo
            "razon_social": "Carlos Moreira",
            "email": "carlos@example.com",
            "tipo_regimen": "RIMPE_NEGOCIO_POPULAR"
        }
        with pytest.raises(ValidationError) as exc_info:
            PerfilTributarioCreate(**data)
        assert "ruc" in str(exc_info.value)
        assert "Módulo 10" in str(exc_info.value)

    def test_perfil_error_email_invalido(self):
        data = {
            "ruc": "0923456784001",
            "razon_social": "Carlos Moreira",
            "email": "correo-no-valido-sin-arroba",
            "tipo_regimen": "RIMPE_EMPRENDEDOR"
        }
        with pytest.raises(ValidationError) as exc_info:
            PerfilTributarioCreate(**data)
        assert "email" in str(exc_info.value)

    def test_perfil_error_regimen_no_reconocido(self):
        data = {
            "ruc": "0923456784001",
            "razon_social": "Carlos Moreira",
            "email": "carlos@example.com",
            "tipo_regimen": "REGIMEN_INVENTADO"
        }
        with pytest.raises(ValidationError) as exc_info:
            PerfilTributarioCreate(**data)
        assert "tipo_regimen" in str(exc_info.value)

    def test_perfil_error_ingresos_negativos(self):
        data = {
            "ruc": "0923456784001",
            "razon_social": "Carlos Moreira",
            "email": "carlos@example.com",
            "tipo_regimen": "RIMPE_EMPRENDEDOR",
            "ingresos_brutos_anuales": -500.0
        }
        with pytest.raises(ValidationError) as exc_info:
            PerfilTributarioCreate(**data)
        assert "ingresos_brutos_anuales" in str(exc_info.value)


class TestCalculoVencimientosRequestValidation:
    """Valida la solicitud de cálculo determinista de vencimientos."""

    def test_calculo_valido(self):
        req = CalculoVencimientosRequest(
            ruc="0923456784001",
            tipo_regimen=TipoRegimen.RIMPE_EMPRENDEDOR,
            anio=2026,
            tiene_actividades_excluidas=True
        )
        assert req.ruc == "0923456784001"
        assert req.anio == 2026

    def test_calculo_error_anio_fuera_de_rango(self):
        with pytest.raises(ValidationError) as exc_info:
            CalculoVencimientosRequest(
                ruc="0923456784001",
                tipo_regimen=TipoRegimen.RIMPE_EMPRENDEDOR,
                anio=2015  # < 2024
            )
        assert "anio" in str(exc_info.value)


class TestRecordatorioEstructuradoValidation:
    """Valida que el contrato estructurado con Google Gemini sea exigente e inmutable."""

    def test_recordatorio_completo_valido(self):
        data = {
            "codigo_obligacion": "IVA_SEMESTRAL_1",
            "titulo_pedagogico": "Declaración del Primer Semestre de IVA 2026",
            "fecha_limite_formateada": "Lunes 20 de Julio de 2026",
            "base_legal_oficial": "Art. 97.8 LRTI y Resolución SRI NAC-DGERCGC24-00000027",
            "explicacion_sencilla": "Como emprendedor RIMPE, debes declarar tus ventas de enero a junio.",
            "consecuencia_incumplimiento": "Multa mínima de $30 USD según Art. 100 de la LRTI.",
            "sugerencia_accion": "Ingresa al portal SRI en Línea con tu clave y llena el Formulario 104.",
            "canal_recomendado": "Portal SRI en Línea > Declaraciones > Impuesto al Valor Agregado"
        }
        rec = RecordatorioEstructurado(**data)
        assert rec.codigo_obligacion == "IVA_SEMESTRAL_1"
        assert "Lunes 20" in rec.fecha_limite_formateada

    def test_recordatorio_incompleto_falla(self):
        data = {
            "codigo_obligacion": "IVA_SEMESTRAL_1",
            "titulo_pedagogico": "Declaración IVA",
            # Faltan campos requeridos como base_legal_oficial, explicacion_sencilla, etc.
        }
        with pytest.raises(ValidationError):
            RecordatorioEstructurado(**data)


class TestExplicacionObligacionRequestValidation:
    """Valida los parámetros de solicitud para generar explicaciones con LLM."""

    def test_formato_fecha_correcto(self):
        req = ExplicacionObligacionRequest(
            codigo_obligacion="IVA_SEMESTRAL_1",
            tipo_regimen=TipoRegimen.RIMPE_EMPRENDEDOR,
            fecha_vencimiento="2026-07-20"
        )
        assert req.fecha_vencimiento == "2026-07-20"

    def test_formato_fecha_invalido(self):
        with pytest.raises(ValidationError) as exc_info:
            ExplicacionObligacionRequest(
                codigo_obligacion="IVA_SEMESTRAL_1",
                tipo_regimen=TipoRegimen.RIMPE_EMPRENDEDOR,
                fecha_vencimiento="20-07-2026"  # Debe ser YYYY-MM-DD
            )
        assert "fecha_vencimiento" in str(exc_info.value)
