# Inventario de Fuentes Normativas y Estrategia de Fragmentación (RAG)

| Metadato | Detalle |
| :--- | :--- |
| **Documento** | Catálogo Oficial de Fuentes e Ingesta de Conocimiento |
| **Proyecto** | Calendario Tributario Inteligente para Emprendedores RIMPE (Caso 11) |
| **Fase / Semana** | Fase 1 – Semana 1 |
| **Ubicación de Fuentes Crudas** | `data/raw/` (rutas relativas al repositorio) |
| **Integridad Documental** | 100% Documentos Oficiales Íntegros en Formato PDF Original |
| **Fecha de Actualización** | Octubre 2024 |
| **Versión** | 3.0.0 (Cuerpos normativos íntegros en PDF original) |

---

## 1. Inventario Formal de Fuentes Oficiales Íntegras

La base de conocimiento de la aplicación está sustentada **exclusivamente en documentos jurídicos y resoluciones oficiales originales e íntegras** emitidas por el Servicio de Rentas Internas (**SRI**), la Presidencia de la República y la Asamblea Nacional del Ecuador.

Todos los documentos descargados se encuentran archivados en la carpeta relativa `data/raw/`, garantizando portabilidad multiplataforma e integridad probatoria:

| ID | Documento Oficial | Emisor Oficial | Enlace Web de Origen Oficial | Vigencia | Archivo Local Relativo | Extensión y Páginas | Tamaño |
| :---: | :--- | :--- | :--- | :---: | :--- | :---: | :---: |
| **F01** | **Resolución N.º NAC-DGERCGC24-00000027** *(Normas de aplicación del RIMPE, categorización, actividades excluidas y deberes formales)* | Servicio de Rentas Internas (SRI) | [SRI Alfresco - Res. 27](https://www.sri.gob.ec/o/sri-portlet-biblioteca-alfresco-internet/descargar?id=7c3fb8dc-31a6-4fe3-a6c0-abe1def2c78a&nombre=NAC-DGERCGC24-00000027.pdf) | Vigente (31 de julio 2024 - Presente) | `data/raw/01_resolucion_sri_nac_dgercgc24_00000027.pdf` | PDF Oficial (9 págs.) | ~300 KB |
| **F02** | **Resolución N.º NAC-DGERCGC23-00000034** *(Calendario tributario, noveno dígito de RUC, plazos para IVA semestral e Impuesto a la Renta)* | Servicio de Rentas Internas (SRI) | [SRI Alfresco - Res. 34](https://www.sri.gob.ec/o/sri-portlet-biblioteca-alfresco-internet/descargar/680d53fa-89af-4dbf-9715-b82d7555279e/NAC-DGERCGC23-00000034.pdf) | Vigente (13 de diciembre 2023 - Presente) | `data/raw/02_resolucion_sri_nac_dgercgc23_00000034_calendario.pdf` | PDF Oficial (6 págs.) | ~360 KB |
| **F03** | **Ley Orgánica de Eficiencia Económica y Generación de Empleo** *(Reformas sustanciales al RIMPE, tabla progresiva cuotas Negocio Popular \$0-\$60, remisión)* | Asamblea Nacional / Registro Oficial Suplemento 461 | [Registro Oficial del Ecuador](https://www.registroficial.gob.ec) | Vigente (20 de diciembre 2023 - Presente) | `data/raw/03_ley_organica_eficiencia_economica_registro_oficial_461.pdf` | PDF Oficial (80 págs.) | ~390 KB |
| **F04** | **Reglamento para la Aplicación de la Ley de Régimen Tributario Interno (RALRTI)** *(Desglose reglamentario de deberes formales, RIMPE, facturación y retenciones)* | Presidencia de la República / SRI | [SRI Alfresco - RALRTI](https://www.sri.gob.ec/o/sri-portlet-biblioteca-alfresco-internet/descargar/fe699a5c-a49a-42e1-a71f-61d66e752ed8/Reglamento%20para%20la%20aplicacion%20de%20la%20Ley%20de%20Regimen%20Tributario%20Interno.pdf) | Codificación Vigente | `data/raw/04_reglamento_aplicacion_lrti.pdf` | PDF Oficial | 1.48 MB |
| **F05** | **Ley de Régimen Tributario Interno (LRTI - Codificación Oficial)** *(Capítulo del RIMPE Arts. 97.1 al 97.17 y régimen sancionador general)* | Asamblea Nacional / SRI | [SRI Alfresco - LRTI](https://www.sri.gob.ec/o/sri-portlet-biblioteca-alfresco-internet/descargar/68811e77-7b9c-4061-a2b4-c6a99696b00e/LEY_DE_REGIMEN_TRIBUTARIO_INTERNO_LRTI.pdf) | Codificación Vigente | `data/raw/05_ley_regimen_tributario_interno_lrti.pdf` | PDF Oficial (158 págs.) | 1.32 MB |
| **F06** | **Código Tributario de la República del Ecuador** *(Reglas generales de cómputo de plazos, prórrogas por fines de semana/feriados e infracciones)* | Congreso Nacional / SRI | [SRI Alfresco - Cód. Tributario](https://www.sri.gob.ec/o/sri-portlet-biblioteca-alfresco-internet/descargar/ecfc5e70-e0cf-4f52-b2ba-8c4fc8035f68/Codigo_Tributario_20_junio_2023.pdf) | Codificación Vigente | `data/raw/06_codigo_tributario_ecuador.pdf` | PDF Oficial (99 págs.) | 758 KB |
| **F07** | **Reglamento de Comprobantes de Venta, Retención y Documentos Complementarios** *(Régimen de notas de venta físicas/electrónicas, facturas y sustentación de costos)* | Presidencia de la República / SRI | [SRI Alfresco - Comprobantes](https://www.sri.gob.ec/o/sri-portlet-biblioteca-alfresco-internet/descargar/f3650927-c9e2-4985-a138-2b9ca3194c06/REGLAMENTO+DE+COMPROBANTES+DE+VENTA+RETENCI%D3N+Y+DOCUMENTOS+COMPLEMENTARIOS.pdf) | Codificación Vigente | `data/raw/07_reglamento_comprobantes_venta_retencion.pdf` | PDF Oficial | ~196 KB |

---

## 2. Estrategia de Fragmentación e Ingesta RAG (*Chunking Strategy*)

Al contar con los **cuerpos documentales íntegros en PDF original**, el motor de indexación RAG procesa los documentos garantizando fidelidad semántica:

```mermaid
flowchart TD
    PDFs["7 Documentos PDF Oficiales Íntegros en data/raw/"] --> Extractor["Extractor Estructurado PDF con PyPDF2 / PyMuPDF<br>(Extracción limpia por página y encabezado)"]
    Extractor --> Normalizer["Filtro de Ruido (pies de página repetitivos, números de página)"]
    
    Normalizer --> Splitter{"Estrategia de Fragmentación"}
    Splitter -- "Artículos Legales de Leyes y Resoluciones" --> ChunkArt["Chunking Estructural por Artículo<br>(400 - 700 tokens, 80 tokens overlap)"]
    Splitter -- "Tablas Numéricas y Fechas (Res. 34, Ley 461)" --> ChunkTable["Chunking de Tablas Íntegras<br>(Preservación de filas con encabezados de columna)"]
    
    ChunkArt --> Metadata["Enriquecimiento con Metadatos"]
    ChunkTable --> Metadata
    
    Metadata --> Embedder["Generación de Vectores (text-embedding-004)"]
    Embedder --> Chroma["Base de Datos Vectorial (ChromaDB)"]
```

### 2.1. Parámetros Técnicos de Fragmentación:
* **Segmentación por Artículo:** Delimitadores regex `r"(?i)(Artículo|Art\.)\s+\d+(\.\d+)?"` para mantener artículos normativos autocontenidos.
* **Tamaño de chunk:** **400 a 700 tokens** (aprox. 1.600 a 2.800 caracteres).
* **Solapamiento (*Overlap*):** **80 tokens** (aprox. 320 caracteres) para asegurar que las excepciones o literales no pierdan la referencia al encabezado del artículo.
* **Preservación de tablas:** Las tablas de tarifas de la Ley de Eficiencia Económica (art. 23) y la tabla del noveno dígito de la Resolución 34 (art. 1) se indexan en fragmentos indivisibles con metadatos especiales `content_type: "tax_table"`.

---

## 3. Esquema de Metadatos para Filtrado Híbrido

Cada fragmento almacenado en la colección vectorial contendrá el siguiente esquema JSON de metadatos:

```json
{
  "chunk_id": "F03-ART-023",
  "source_doc": "data/raw/03_ley_organica_eficiencia_economica_registro_oficial_461.pdf",
  "document_title": "Ley Organica de Eficiencia Economica y Generacion de Empleo",
  "authority": "Asamblea Nacional del Ecuador",
  "legal_hierarchy": "Ley Organica",
  "target_regime": ["RIMPE_NEGOCIO_POPULAR", "RIMPE_EMPRENDEDOR"],
  "topic": "tabla_tarifas_cuotas_rimpe",
  "page_number": 18,
  "status": "vigente"
}
```

Este esquema asegura que ante una consulta de un usuario, el agente puede recuperar la evidencia normativa exacta filtrando por régimen y citar con precisión la fuente, el artículo y el número de página del documento oficial.
