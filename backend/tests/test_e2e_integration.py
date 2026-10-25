"""
Pruebas de Integración End-to-End (E2E) para la Solución Completa
Asignatura: Ingeniería de Software con IA Generativa
Caso N.º 11 – Grupo 11

Valida los 4 flujos principales de negocio integrados:
1. Flujo Completo RIMPE Emprendedor (Cálculo determinista -> Explicación GenAI -> Simulación de Renta).
2. Flujo Completo RIMPE Negocio Popular (Declaración única en mayo -> Escala progresiva $0 a $60).
3. Flujo Contribuyente Mixto (Actividades excluidas -> Incorporación de IVA Régimen General).
4. Flujo de Observabilidad, Privacidad LOPDP y Cabeceras de Rendimiento.
5. Verificación de Integridad del Artefacto de Producción del Frontend.
"""

import os
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)

# RUCs reales de prueba (Módulo 10 personas naturales Ecuador)
RUC_EMPRENDEDOR = "0923456784001"  # Guayas - 9no dígito 8
RUC_POPULAR = "1710034065001"       # Pichincha - 9no dígito 6
RUC_MIXTO = "0910000009001"         # 9no dígito 0


def test_e2e_flujo_1_emprendedor_completo():
    """
    E2E Flujo 1: Contribuyente RIMPE Emprendedor
    Paso 1: Cálculo de vencimientos en /api/perfil/calcular-vencimientos.
    Paso 2: Consulta de explicación didáctica en /api/obligaciones/explicar.
    Paso 3: Simulación de impuesto a la renta en /api/simulador/renta.
    """
    # 1. Cálculo de Calendario
    payload_cal = {
        "ruc": RUC_EMPRENDEDOR,
        "tipo_regimen": "RIMPE_EMPRENDEDOR",
        "anio": 2026,
        "tiene_actividades_excluidas": False
    }
    res_cal = client.post("/api/perfil/calcular-vencimientos", json=payload_cal)
    assert res_cal.status_code == 200
    data_cal = res_cal.json()

    assert data_cal["noveno_digito"] == 8
    assert data_cal["total_obligaciones"] == 3
    eventos = data_cal["eventos"]
    codigos = [e["codigo_obligacion"] for e in eventos]
    assert "IVA_SEMESTRAL_1" in codigos
    assert "IVA_SEMESTRAL_2" in codigos
    assert "RENTA_ANUAL_EMPRENDEDOR" in codigos

    # 2. Explicación Didáctica GenAI de una de las obligaciones calculadas
    evt_iva1 = next(e for e in eventos if e["codigo_obligacion"] == "IVA_SEMESTRAL_1")
    payload_exp = {
        "codigo_obligacion": evt_iva1["codigo_obligacion"],
        "tipo_regimen": "RIMPE_EMPRENDEDOR",
        "fecha_vencimiento": evt_iva1["fecha_vencimiento"],
        "noveno_digito": data_cal["noveno_digito"],
        "ruc": RUC_EMPRENDEDOR,
        "es_declaracion_en_cero": False
    }
    res_exp = client.post("/api/obligaciones/explicar", json=payload_exp)
    assert res_exp.status_code == 200
    data_exp = res_exp.json()
    assert "obligacion" in data_exp
    rec = data_exp["obligacion"]
    assert rec["codigo_obligacion"] == "IVA_SEMESTRAL_1"
    assert len(rec["explicacion_sencilla"]) > 15
    assert len(rec["base_legal_oficial"]) > 5
    assert data_exp["modelo_utilizado"] is not None

    # 3. Simulación de Impuesto a la Renta para este Emprendedor (ej. $45,000 USD)
    payload_sim = {
        "ingresos_brutos": 45000.0,
        "tipo_regimen": "RIMPE_EMPRENDEDOR"
    }
    res_sim = client.post("/api/simulador/renta", json=payload_sim)
    assert res_sim.status_code == 200
    data_sim = res_sim.json()
    assert data_sim["impuesto_causado"] > 60.0
    assert data_sim["tipo_marginal"] is not None


def test_e2e_flujo_2_negocio_popular_completo():
    """
    E2E Flujo 2: Contribuyente RIMPE Negocio Popular
    Paso 1: Cálculo de vencimientos (1 sola obligación en mayo).
    Paso 2: Explicación didáctica (formulario simplificado, sin IVA periódico).
    Paso 3: Simulación de cuota fija ($0 o $60 USD).
    """
    # 1. Cálculo de Calendario
    payload_cal = {
        "ruc": RUC_POPULAR,
        "tipo_regimen": "RIMPE_NEGOCIO_POPULAR",
        "anio": 2026,
        "tiene_actividades_excluidas": False
    }
    res_cal = client.post("/api/perfil/calcular-vencimientos", json=payload_cal)
    assert res_cal.status_code == 200
    data_cal = res_cal.json()
    assert data_cal["total_obligaciones"] == 1
    assert data_cal["eventos"][0]["codigo_obligacion"] == "RENTA_ANUAL_NEGOCIO_POPULAR"
    assert "2027-05" in data_cal["eventos"][0]["fecha_vencimiento"]

    # 2. Explicación Didáctica
    payload_exp = {
        "codigo_obligacion": "RENTA_ANUAL_NEGOCIO_POPULAR",
        "tipo_regimen": "RIMPE_NEGOCIO_POPULAR",
        "fecha_vencimiento": data_cal["eventos"][0]["fecha_vencimiento"],
        "noveno_digito": data_cal["noveno_digito"],
        "ruc": RUC_POPULAR
    }
    res_exp = client.post("/api/obligaciones/explicar", json=payload_exp)
    assert res_exp.status_code == 200
    rec = res_exp.json()["obligacion"]
    assert "negocio popular" in rec["explicacion_sencilla"].lower() or "cuota" in rec["explicacion_sencilla"].lower() or "mayo" in rec["explicacion_sencilla"].lower()

    # 3. Simulación de Renta: caso cuota $0 (< $2,500), caso cuota $35 ($15,000) y caso cuota $60 ($18,000)
    res_sim_cero = client.post("/api/simulador/renta", json={"ingresos_brutos": 1800.0, "tipo_regimen": "RIMPE_NEGOCIO_POPULAR"})
    assert res_sim_cero.status_code == 200
    assert res_sim_cero.json()["impuesto_causado"] == 0.0

    res_sim_treinta_y_cinco = client.post("/api/simulador/renta", json={"ingresos_brutos": 15000.0, "tipo_regimen": "RIMPE_NEGOCIO_POPULAR"})
    assert res_sim_treinta_y_cinco.status_code == 200
    assert res_sim_treinta_y_cinco.json()["impuesto_causado"] == 35.0

    res_sim_sesenta = client.post("/api/simulador/renta", json={"ingresos_brutos": 18000.0, "tipo_regimen": "RIMPE_NEGOCIO_POPULAR"})
    assert res_sim_sesenta.status_code == 200
    assert res_sim_sesenta.json()["impuesto_causado"] == 60.0


def test_e2e_flujo_3_contribuyente_mixto():
    """
    E2E Flujo 3: Contribuyente con actividades excluyentes (ej. Servicios profesionales)
    Verifica que se sume automáticamente la obligación de IVA bajo Régimen General.
    """
    payload = {
        "ruc": RUC_MIXTO,
        "tipo_regimen": "RIMPE_EMPRENDEDOR",
        "anio": 2026,
        "tiene_actividades_excluidas": True
    }
    res = client.post("/api/perfil/calcular-vencimientos", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["tiene_actividades_excluidas"] is True
    assert data["total_obligaciones"] == 4

    categorias = [e["categoria"] for e in data["eventos"]]
    assert "REGIMEN_GENERAL" in categorias


def test_e2e_observabilidad_lopdp_y_cabeceras():
    """
    E2E Flujo 4: Verifica la observabilidad, cabeceras CORS y X-Process-Time-Ms.
    """
    res = client.get("/health")
    assert res.status_code == 200
    assert "x-process-time-ms" in res.headers
    assert float(res.headers["x-process-time-ms"]) >= 0.0

    # Petición OPTIONS para verificar CORS
    res_cors = client.options(
        "/api/perfil/calcular-vencimientos",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST"
        }
    )
    assert res_cors.status_code in [200, 204]


def test_e2e_frontend_dist_bundle_integrity():
    """
    E2E Flujo 5: Verifica que el artefacto de producción de Vite en frontend/dist/
    esté compilado y contenga index.html con sus bundles de React.
    """
    dist_dir = Path("frontend/dist")
    index_html = dist_dir / "index.html"
    assert index_html.exists(), "frontend/dist/index.html debe existir tras npm run build"

    content = index_html.read_text(encoding="utf-8")
    assert "Calendario Tributario RIMPE" in content
    assert '<div id="root">' in content
    assert '<script type="module"' in content

    # Comprobar que existan assets generados (.js y .css)
    assets_dir = dist_dir / "assets"
    assert assets_dir.exists(), "La carpeta frontend/dist/assets debe existir"
    js_files = list(assets_dir.glob("*.js"))
    css_files = list(assets_dir.glob("*.css"))
    assert len(js_files) > 0, "Debe existir al menos un bundle JS compilado"
    assert len(css_files) > 0, "Debe existir al menos un bundle CSS compilado"
