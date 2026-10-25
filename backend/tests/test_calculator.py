"""
Suite de Pruebas Unitarias para el Motor Determinista de Calendario y Obligaciones RIMPE.
Valida con rigurosidad matemática y normativa oficial del SRI Ecuador:
1. Algoritmo Módulo 10 para RUC de personas naturales.
2. Mapeo exacto de los 10 novenos dígitos a sus fechas de vencimiento nominales.
3. Traslado automático por fines de semana (sábado y domingo hacia el lunes hábil).
4. Traslado automático por feriados nacionales ecuatorianos oficiales.
5. Diferenciación estricta de obligaciones entre RIMPE Emprendedor y RIMPE Negocio Popular.
6. Simulación progresiva de cuotas de Impuesto a la Renta según la Ley de Eficiencia Económica.
"""

import pytest
from datetime import date
from backend.services.calculator import (
    validar_ruc_persona_natural,
    es_dia_inhabil,
    trasladar_al_siguiente_dia_habil,
    calcular_vencimientos,
    simular_cuota_renta,
    cargar_reglas_sri
)


# ==============================================================================
# 1. PRUEBAS DE VALIDACIÓN DE RUC (MÓDULO 10 ECUADOR)
# ==============================================================================

class TestValidacionRucPersonaNatural:
    """Valida exhaustivamente el algoritmo Módulo 10 oficial del SRI."""

    @pytest.mark.parametrize("ruc_valido, descripcion", [
        ("0923456784001", "Guayas - Dígito verificador 4"),
        ("1710034065001", "Pichincha - Dígito verificador 5"),
        ("0910000017001", "9no dígito 1 - Verificador 7"),
        ("0910000025001", "9no dígito 2 - Verificador 5"),
        ("0910000033001", "9no dígito 3 - Verificador 3"),
        ("0910000041001", "9no dígito 4 - Verificador 1"),
        ("0910000058001", "9no dígito 5 - Verificador 8"),
        ("0910000066001", "9no dígito 6 - Verificador 6"),
        ("0910000074001", "9no dígito 7 - Verificador 4"),
        ("0910000082001", "9no dígito 8 - Verificador 2"),
        ("0910000090001", "9no dígito 9 - Verificador 0 (residuo exacto)"),
        ("0910000009001", "9no dígito 0 - Verificador 9"),
    ])
    def test_rucs_validos_personas_naturales(self, ruc_valido, descripcion):
        assert validar_ruc_persona_natural(ruc_valido) is True, f"Fallo al validar: {descripcion}"

    @pytest.mark.parametrize("ruc_invalido, motivo", [
        ("092345678400", "Longitud menor a 13 dígitos (12 dígitos)"),
        ("09234567840011", "Longitud mayor a 13 dígitos (14 dígitos)"),
        ("092345678400A", "Contiene caracteres alfabéticos"),
        ("0023456784001", "Código de provincia 00 inválido"),
        ("2523456784001", "Código de provincia 25 inexistente en Ecuador (máx 24)"),
        ("9923456784001", "Código de provincia 99 inválido"),
        ("0963456784001", "Tercer dígito 6 (reservado para entidades públicas)"),
        ("0993456784001", "Tercer dígito 9 (reservado para personas jurídicas privadas)"),
        ("0923456784002", "Sufijo de establecimiento no termina en 001"),
        ("0923456785001", "Dígito verificador erróneo (debería ser 4, tiene 5)"),
        ("", "Cadena vacía"),
        (None, "Valor None"),
        (1234567890001, "Tipo de dato no string (entero)"),
    ])
    def test_rucs_invalidos(self, ruc_invalido, motivo):
        assert validar_ruc_persona_natural(ruc_invalido) is False, f"Fallo al rechazar: {motivo}"


# ==============================================================================
# 2. PRUEBAS DE MAPEO DE LOS 10 NOVENOS DÍGITOS DEL RUC
# ==============================================================================

class TestMapeoNovenoDigito:
    """Verifica que cada uno de los dígitos 1 al 0 mapee al día nominal legal oficial."""

    @pytest.mark.parametrize("noveno_digito, ruc, dia_esperado", [
        (1, "0910000017001", 10),
        (2, "0910000025001", 12),
        (3, "0910000033001", 14),
        (4, "0910000041001", 16),
        (5, "0910000058001", 18),
        (6, "0910000066001", 20),
        (7, "0910000074001", 22),
        (8, "0910000082001", 24),
        (9, "0910000090001", 26),
        (0, "0910000009001", 28),
    ])
    def test_mapeo_dia_base_todos_los_digitos(self, noveno_digito, ruc, dia_esperado):
        resultado = calcular_vencimientos(
            ruc=ruc,
            tipo_regimen="RIMPE_EMPRENDEDOR",
            anio=2026
        )
        assert resultado["noveno_digito"] == noveno_digito

        # Verificamos la fecha nominal del IVA Semestral 1 (julio 2026)
        evento_iva1 = next(e for e in resultado["eventos"] if e["codigo_obligacion"] == "IVA_SEMESTRAL_1")
        fecha_nominal = date.fromisoformat(evento_iva1["fecha_nominal"])
        assert fecha_nominal.day == dia_esperado, f"Dígito {noveno_digito} debe tener día base {dia_esperado}"
        assert fecha_nominal.month == 7
        assert fecha_nominal.year == 2026


# ==============================================================================
# 3. PRUEBAS DE TRASLADO POR FIN DE SEMANA Y FERIADOS
# ==============================================================================

class TestTrasladoFechasInhabiles:
    """Valida la prórroga obligatoria al primer día hábil siguiente."""

    def test_traslado_sabado_a_lunes(self):
        # El 18 de Julio de 2026 es SÁBADO (weekday == 5).
        # RUC con 9no dígito 5 -> día nominal 18.
        ruc_digito_5 = "0910000058001"
        resultado = calcular_vencimientos(
            ruc=ruc_digito_5,
            tipo_regimen="RIMPE_EMPRENDEDOR",
            anio=2026
        )
        evento_iva1 = next(e for e in resultado["eventos"] if e["codigo_obligacion"] == "IVA_SEMESTRAL_1")
        
        assert evento_iva1["fecha_nominal"] == "2026-07-18"
        assert evento_iva1["fue_trasladada"] is True
        assert "Sábado" in evento_iva1["motivo_traslado"]
        # Debe trasladarse al lunes 20 de julio de 2026
        assert evento_iva1["fecha_vencimiento"] == "2026-07-20"
        fecha_venc = date.fromisoformat(evento_iva1["fecha_vencimiento"])
        assert fecha_venc.weekday() == 0  # Lunes

    def test_traslado_domingo_a_lunes(self):
        # El 14 de Marzo de 2027 es DOMINGO (weekday == 6).
        # RUC con 9no dígito 3 -> día nominal 14.
        # Para ejercicio fiscal 2026, Renta Emprendedor vence en marzo 2027.
        ruc_digito_3 = "0910000033001"
        resultado = calcular_vencimientos(
            ruc=ruc_digito_3,
            tipo_regimen="RIMPE_EMPRENDEDOR",
            anio=2026
        )
        evento_renta = next(e for e in resultado["eventos"] if e["codigo_obligacion"] == "RENTA_ANUAL_EMPRENDEDOR")
        
        assert evento_renta["fecha_nominal"] == "2027-03-14"
        assert evento_renta["fue_trasladada"] is True
        assert "Domingo" in evento_renta["motivo_traslado"]
        # Debe trasladarse al lunes 15 de marzo de 2027
        assert evento_renta["fecha_vencimiento"] == "2027-03-15"
        fecha_venc = date.fromisoformat(evento_renta["fecha_vencimiento"])
        assert fecha_venc.weekday() == 0  # Lunes

    def test_traslado_por_feriado_nacional_batalla_pichincha(self):
        # 24 de Mayo es Feriado Nacional (Batalla de Pichincha).
        # En 2027, el 24 de mayo cae Lunes.
        # RUC con 9no dígito 8 -> día nominal 24.
        # Para RIMPE Negocio Popular (año 2026), Renta vence en Mayo 2027.
        ruc_digito_8 = "0910000082001"
        resultado = calcular_vencimientos(
            ruc=ruc_digito_8,
            tipo_regimen="RIMPE_NEGOCIO_POPULAR",
            anio=2026
        )
        evento_renta_np = resultado["eventos"][0]
        
        assert evento_renta_np["fecha_nominal"] == "2027-05-24"
        assert evento_renta_np["fue_trasladada"] is True
        assert "Batalla de Pichincha" in evento_renta_np["motivo_traslado"]
        # Debe trasladarse al día hábil siguiente: martes 25 de mayo de 2027
        assert evento_renta_np["fecha_vencimiento"] == "2027-05-25"
        fecha_venc = date.fromisoformat(evento_renta_np["fecha_vencimiento"])
        assert fecha_venc.weekday() == 1  # Martes

    def test_fecha_en_dia_habil_no_se_traslada(self):
        # RUC con 9no dígito 1 -> día nominal 10.
        # Julio 10 de 2026 cae VIERNES (weekday == 4), día plenamente hábil.
        ruc_digito_1 = "0910000017001"
        resultado = calcular_vencimientos(
            ruc=ruc_digito_1,
            tipo_regimen="RIMPE_EMPRENDEDOR",
            anio=2026
        )
        evento_iva1 = next(e for e in resultado["eventos"] if e["codigo_obligacion"] == "IVA_SEMESTRAL_1")
        
        assert evento_iva1["fecha_nominal"] == "2026-07-10"
        assert evento_iva1["fecha_vencimiento"] == "2026-07-10"
        assert evento_iva1["fue_trasladada"] is False
        assert evento_iva1["motivo_traslado"] == "NINGUNO"


# ==============================================================================
# 4. PRUEBAS DE OBLIGACIONES POR RÉGIMEN Y CONDICIÓN MIXTA
# ==============================================================================

class TestObligacionesPorRegimen:
    """Verifica la separación de obligaciones entre Negocio Popular y Emprendedor."""

    def test_rimpe_emprendedor_genera_tres_obligaciones(self):
        ruc = "0923456784001"  # 9no dígito 8
        resultado = calcular_vencimientos(
            ruc=ruc,
            tipo_regimen="RIMPE_EMPRENDEDOR",
            anio=2026,
            tiene_actividades_excluidas=False
        )
        assert resultado["tipo_regimen"] == "RIMPE_EMPRENDEDOR"
        assert resultado["total_obligaciones"] == 3

        codigos = [e["codigo_obligacion"] for e in resultado["eventos"]]
        assert "IVA_SEMESTRAL_1" in codigos
        assert "IVA_SEMESTRAL_2" in codigos
        assert "RENTA_ANUAL_EMPRENDEDOR" in codigos

    def test_rimpe_negocio_popular_genera_una_sola_obligacion(self):
        ruc = "0923456784001"
        resultado = calcular_vencimientos(
            ruc=ruc,
            tipo_regimen="RIMPE_NEGOCIO_POPULAR",
            anio=2026,
            tiene_actividades_excluidas=False
        )
        assert resultado["tipo_regimen"] == "RIMPE_NEGOCIO_POPULAR"
        assert resultado["total_obligaciones"] == 1

        evento = resultado["eventos"][0]
        assert evento["codigo_obligacion"] == "RENTA_ANUAL_NEGOCIO_POPULAR"
        assert "Mayo" in evento["descripcion"] or "Mayo" in evento["titulo"] or "-05-" in evento["fecha_nominal"]
        # Negocio popular NO debe incluir declaraciones de IVA semestral
        codigos = [e["codigo_obligacion"] for e in resultado["eventos"]]
        assert "IVA_SEMESTRAL_1" not in codigos
        assert "IVA_SEMESTRAL_2" not in codigos

    def test_condicion_mixta_agrega_obligacion_regimen_general(self):
        ruc = "0923456784001"
        resultado = calcular_vencimientos(
            ruc=ruc,
            tipo_regimen="RIMPE_EMPRENDEDOR",
            anio=2026,
            tiene_actividades_excluidas=True
        )
        assert resultado["tiene_actividades_excluidas"] is True
        assert resultado["total_obligaciones"] == 4

        codigos = [e["codigo_obligacion"] for e in resultado["eventos"]]
        assert "IVA_REGIMEN_GENERAL_MIXTO" in codigos

        evento_mixto = next(e for e in resultado["eventos"] if e["codigo_obligacion"] == "IVA_REGIMEN_GENERAL_MIXTO")
        assert evento_mixto["categoria"] == "REGIMEN_GENERAL"


# ==============================================================================
# 5. PRUEBAS DEL SIMULADOR PROGRESIVO DE IMPUESTO A LA RENTA
# ==============================================================================

class TestSimuladorRenta:
    """Valida los cálculos de cuotas fijas y progresivas del Impuesto a la Renta."""

    @pytest.mark.parametrize("ingresos, cuota_esperada", [
        (0.00, 0.00),
        (1500.00, 0.00),
        (2500.00, 0.00),
        (2500.01, 5.00),
        (4999.99, 5.00),
        (5000.00, 5.00),
        (5000.01, 15.00),
        (10000.00, 15.00),
        (10000.01, 35.00),
        (15000.00, 35.00),
        (15000.01, 60.00),
        (20000.00, 60.00),
    ])
    def test_simulacion_negocio_popular_tramos(self, ingresos, cuota_esperada):
        sim = simular_cuota_renta(ingresos_brutos=ingresos, tipo_regimen="RIMPE_NEGOCIO_POPULAR")
        assert sim["impuesto_causado"] == cuota_esperada

    def test_simulacion_negocio_popular_alerta_transicion_superior(self):
        sim = simular_cuota_renta(ingresos_brutos=25000.00, tipo_regimen="RIMPE_NEGOCIO_POPULAR")
        assert sim["impuesto_causado"] == 60.00
        assert "alerta_transicion" in sim
        assert "superan los $20.000,00 USD" in sim["alerta_transicion"]

    def test_simulacion_emprendedor_rango_base(self):
        # Ingreso hasta 20000 en Emprendedor
        sim = simular_cuota_renta(ingresos_brutos=18000.00, tipo_regimen="RIMPE_EMPRENDEDOR")
        assert sim["impuesto_causado"] == 60.00

    def test_simulacion_emprendedor_tramo_20k_a_50k(self):
        # Ingresos: 30,000 USD
        # Fracción básica: 60.00 USD
        # Excedente: 30000 - 20000.01 = 9999.99 * 1% = 100.00 USD
        # Total: 160.00 USD
        sim = simular_cuota_renta(ingresos_brutos=30000.00, tipo_regimen="RIMPE_EMPRENDEDOR")
        assert sim["fraccion_basica"] == 60.00
        assert sim["tipo_marginal"] == "1.0%"
        assert sim["impuesto_causado"] == 160.00

    def test_simulacion_emprendedor_tramo_50k_a_75k(self):
        # Ingresos: 60,000 USD
        # Fracción básica: 360.00 USD
        # Excedente: 60000 - 50000.01 = 9999.99 * 1.25% = 125.00 USD
        # Total: 485.00 USD
        sim = simular_cuota_renta(ingresos_brutos=60000.00, tipo_regimen="RIMPE_EMPRENDEDOR")
        assert sim["fraccion_basica"] == 360.00
        assert sim["tipo_marginal"] == "1.25%"
        assert sim["impuesto_causado"] == 485.00

    def test_simulacion_error_ingresos_negativos(self):
        with pytest.raises(ValueError, match="no pueden ser negativos"):
            simular_cuota_renta(ingresos_brutos=-100.00, tipo_regimen="RIMPE_EMPRENDEDOR")

    def test_simulacion_error_ingresos_exceden_limite_rimpe(self):
        with pytest.raises(ValueError, match="superan el límite máximo"):
            simular_cuota_renta(ingresos_brutos=350000.00, tipo_regimen="RIMPE_EMPRENDEDOR")

    def test_simulacion_error_regimen_desconocido(self):
        with pytest.raises(ValueError, match="No se pudo calcular la cuota"):
            simular_cuota_renta(ingresos_brutos=25000.00, tipo_regimen="REGIMEN_INEXISTENTE")


# ==============================================================================
# 6. PRUEBAS DE EXCEPCIONES Y ERRORES DE ENTRADA
# ==============================================================================

class TestExcepcionesMotor:
    """Valida la respuesta robusta ante entradas malformadas o faltantes."""

    def test_error_ruc_invalido_en_calcular_vencimientos(self):
        with pytest.raises(ValueError, match="no cumple con el algoritmo Módulo 10"):
            calcular_vencimientos(
                ruc="0999999999001",
                tipo_regimen="RIMPE_EMPRENDEDOR",
                anio=2026
            )

    def test_error_regimen_invalido_en_calcular_vencimientos(self):
        with pytest.raises(ValueError, match="Tipo de régimen inválido"):
            calcular_vencimientos(
                ruc="0923456784001",
                tipo_regimen="REGIMEN_GENERAL",
                anio=2026
            )

    def test_error_archivo_configuracion_inexistente(self):
        with pytest.raises(FileNotFoundError, match="Archivo de reglas SRI no encontrado"):
            cargar_reglas_sri("config/ruta_fantasma_inexistente.json")
