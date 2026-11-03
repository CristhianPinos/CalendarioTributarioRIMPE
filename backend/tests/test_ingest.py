"""
Pruebas Automatizadas para el Pipeline de Ingesta RAG (scripts/ingest.py).
Asignatura: Ingeniería de Software con IA Generativa
Caso N.º 11 – Grupo 11: Calendario Tributario RIMPE

Verifica el cumplimiento de los criterios:
- Extracción limpia de texto.
- Fragmentación por artículo con cabecera verificable (sin fragmentos huérfanos).
- Metadatos obligatorios presentes (documento, articulo_seccion, anio_fiscal, vigencia, regimen, url).
"""

import json
import pytest
from pathlib import Path
from scripts.ingest import (
    normalizar_texto,
    inferir_regimen,
    fragmentar_por_articulos_o_secciones,
    CHUNKS_OUTPUT_FILE,
    FUENTES_CATALOGO
)


def test_normalizar_texto():
    """Verifica la limpieza de saltos de línea quebrados, guiones y espacios dobles."""
    texto_sucio = "Resolu-\nción del   SRI\r\n\r\n\r\npara  el  año 2026."
    limpio = normalizar_texto(texto_sucio)
    assert "Resolución" in limpio
    assert "  " not in limpio
    assert "\r" not in limpio


def test_inferir_regimen():
    """Verifica la correcta clasificación preliminar de régimen por palabras clave."""
    assert inferir_regimen("El negocio popular emitirá nota de venta") == "RIMPE_NEGOCIO_POPULAR"
    assert inferir_regimen("El contribuyente considerado emprendedor emitirá factura con retención") == "RIMPE_EMPRENDEDOR"
    assert inferir_regimen("Disposiciones generales para todo el régimen RIMPE") == "AMBOS"


def test_fragmentar_por_articulos_preserva_cabecera():
    """Verifica que el corte por artículo preserve la cabecera exacta para citas verificables."""
    muestra = (
        "Art. 97.3.- Régimen RIMPE. Se sujetan a este régimen los contribuyentes emprendedores y negocios populares.\n\n"
        "Art. 97.6.- Declaración y pago. Los contribuyentes presentarán declaración anual de impuesto a la renta.\n\n"
        "Art. 97.8.- Comprobantes de venta. Los negocios populares emitirán notas de venta."
    )
    meta = {
        "archivo": "lrti_test.pdf",
        "documento": "Ley de Régimen Tributario Interno",
        "vigente": True,
        "anio_fiscal": 2026,
        "jerarquia": "ley_ordinaria",
        "url": "https://sri.gob.ec"
    }
    chunks = fragmentar_por_articulos_o_secciones(muestra, meta)
    assert len(chunks) == 3

    for c in chunks:
        assert c["cabecera_verificable"] is True
        assert c["anio_fiscal"] == 2026
        assert c["vigente"] is True
        assert c["cita_oficial"].startswith("[Ley de Régimen Tributario Interno, Art.")

    articulos = [c["articulo_seccion"] for c in chunks]
    assert "Art. 97.3" in articulos
    assert "Art. 97.6" in articulos
    assert "Art. 97.8" in articulos


def test_archivo_rag_chunks_generado_correctamente():
    """Verifica que el archivo rag_chunks.json exista y contenga los metadatos requeridos."""
    assert CHUNKS_OUTPUT_FILE.exists()
    with open(CHUNKS_OUTPUT_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["total_fragmentos"] > 1000
    assert data["ejercicio_fiscal"] == 2026
    assert len(data["chunks"]) == data["total_fragmentos"]

    # Verificar que el 99%+ de los fragmentos tengan cabecera verificable
    verificables = sum(1 for c in data["chunks"] if c["cabecera_verificable"])
    porcentaje = (verificables / data["total_fragmentos"]) * 100
    assert porcentaje >= 99.0

    # Verificar que existan los artículos clave de la LRTI sobre RIMPE
    citas_lrti = [c["articulo_seccion"] for c in data["chunks"] if "LRTI" in c["documento"]]
    assert any("Art. 97.3" in cita or "97.3" in cita for cita in citas_lrti)
    assert any("Art. 97.6" in cita or "97.6" in cita for cita in citas_lrti)
