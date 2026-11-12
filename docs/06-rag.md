# Documento Técnico: Justificación de la Estrategia de Fragmentación RAG y Metadatos (Semana 3)

**Caso N.º 11 – Grupo 11:** Calendario Tributario Personalizado con Recordatorios para Emprendedores RIMPE  
**Asignatura:** Ingeniería de Software con IA Generativa  
**Fecha:** Octubre 2026  
**Autores:** Cristhian Pinos, Juan Lucumi  
**Cumplimiento:** Lista de Verificación Entrega 3 (Ítems: `scripts/ingest.py reproducible` y `docs/06-rag.md`)

---

## 1. El Dilema del Corte en Documentos Jurídicos y Normativos

En la arquitectura de un sistema de Recuperación Aumentada por Generación (RAG) especializado en el dominio tributario ecuatoriano (SRI), la calidad de la respuesta generada depende estrictamente de la integridad del fragmento recuperado (*Garbage in, Garbage out*).

La elección de cortar por artículos evita parte de la pérdida de contexto de un corte fijo. No consta una medición reproducible de un índice alternativo por tamaño fijo; la tabla siguiente describe el diseño y el resultado observado del índice actual.

| Criterio | Corte por Tamaño Fijo (Fixed-Size Chunking) | Corte Estructural por Artículo (Structural Semantic Chunking) |
| :--- | :--- | :--- |
| **Mecánica** | División ciega cada 260 o 1,000 caracteres, sin considerar la sintaxis. | División por frontera natural de unidad de sentido (`Art. \d+`, `Disposición`). |
| **Preservación de cabecera** | Puede separar contenido y artículo; no se midió una línea base en este repositorio. | 1.498 de 1.507 fragmentos tienen cabecera verificable; los otros nueve no entran en la búsqueda. |
| **Cita producida** | Sin metadatos adicionales es difícil atribuir el texto. | La salida copia documento y sección del fragmento; esto prueba trazabilidad estructural, no pertinencia jurídica. |
| **Respuesta** | No se evaluó. | El RAG devuelve extractos de hasta dos fragmentos, precedidos por sus citas; no hace una síntesis generativa de la pregunta. |

---

## 2. Parámetros de Fragmentación Adoptados y Justificación

Para procesar los 7 documentos oficiales del SRI y leyes ecuatorianas ubicados en `data/raw/` (782 páginas combinadas), se implementó en `scripts/ingest.py` la siguiente configuración técnica:

### 2.1. Unidad Primaria: El Artículo de Ley
- **Patrón Regex de Frontera:**
  ```regex
  (?=(?:\n\s*|^)(?:Art[^\n\r\.\d]{0,8}(?:\.|\s*culo)?\s*\d+(?:\.\d+)?|Disposici[^\n\r\.\d]{0,6}\s+(?:General|Transitoria|Derogatoria)\s+[A-Z\d]+))
  ```
- **Justificación:** En el derecho tributario ecuatoriano (Código Tributario Art. 3 y LRTI), cada artículo constituye una **norma dispositiva autónoma** (contiene el supuesto de hecho, el sujeto pasivo, la obligación y la consecuencia jurídica). Fragmentar dentro de un artículo rompe la coherencia lógica de la norma.

### 2.2. Manejo de Artículos Extensos y Solapamiento Semántico (*Overlap*)
- **Umbral de Subdivisión:** 2,400 caracteres.
- **Tamaño de Subfragmento (*Chunk Size*):** Entre 1,200 y 1,800 caracteres.
- **Solapamiento (*Overlap*):** División por saltos de párrafo naturales (`\n\s*\n`), inyectando en la primera línea de cada bloque subsecuente el prefijo identificador:
  ```text
  [Art. 97.6 - Parte 2]
  [Art. 97.6 - Continuación]
  ```
- **Justificación:** El prefijo conserva la atribución cuando un artículo extenso se divide en párrafos. El índice actual usa BM25; no calcula embeddings.

---

## 3. Esquema de Metadatos Obligatorios

Cada fragmento almacenado en `data/processed/rag_chunks.json` contiene una estructura de metadatos tipada y enriquecida para permitir **filtrado previo (*Pre-filtering*)**:

```json
{
  "chunk_id": "05_ley_regimen_tributario_interno_lrti.pdf_chunk_0258",
  "documento": "Ley de Régimen Tributario Interno (LRTI)",
  "articulo_seccion": "Art. 97.6",
  "cita_oficial": "[Ley de Régimen Tributario Interno (LRTI), Art. 97.6]",
  "contenido": "Art. 97.6 Tarifa del impuesto. - Los sujetos pasivos dentro del régimen RIMPE pagarán el Impuesto a la Renta conforme a las siguientes tablas progresivas...",
  "regimen": "AMBOS",
  "vigente": true,
  "anio_fiscal": 2026,
  "jerarquia": "ley_ordinaria",
  "url": "https://www.sri.gob.ec/o/sri-portlet-biblioteca-alfresco-internet/descargar/68811e77-7b9c-4061-a2b4-c6a99696b00e/LEY_DE_REGIMEN_TRIBUTARIO_INTERNO_LRTI.pdf",
  "longitud_caracteres": 1523,
  "cabecera_verificable": true
}
```

### Justificación de cada metadato:
1. `documento` y `articulo_seccion` atribuyen el extracto recuperado; el número de artículo no demuestra por sí solo que responda a la pregunta.
2. `regimen` se infiere por términos del fragmento. El filtro evita ciertas incompatibilidades entre Negocio Popular y Emprendedor, pero esta inferencia no sustituye la revisión del RUC ni de la fuente.
3. `anio_fiscal: 2026` y `vigente: true` son etiquetas del catálogo de ingesta, no una comprobación automática de vigencia jurídica. Deben revisarse cuando cambie la normativa.
4. `jerarquia` se conserva como metadato, pero el ranking BM25 no prioriza por jerarquía legal.
5. `url` enlaza el PDF directo para las dos resoluciones, la LRTI y el Código Tributario; otras fuentes conservan enlaces generales y deben verificarse manualmente.

---

## 4. Resultados del Pipeline de Ingesta (`scripts/ingest.py`)

Al ejecutar el pipeline sobre el conjunto completo de documentos en `data/raw/`:

```text
=================================================================
INICIANDO PIPELINE DE INGESTA RAG - CALENDARIO TRIBUTARIO RIMPE
Directorio fuente: data/raw
=================================================================
Procesando: Resolución SRI NAC-DGERCGC24-00000027 -> 12 fragmentos (12 verificables)
Procesando: Resolución SRI NAC-DGERCGC23-00000034 -> 5 fragmentos (5 verificables)
Procesando: Ley Orgánica de Eficiencia Económica (R.O. 461) -> 195 fragmentos (190 verificables)
Procesando: Reglamento Aplicación LRTI (RLRTI) -> 523 fragmentos (522 verificables)
Procesando: Ley de Régimen Tributario Interno (LRTI) -> 330 fragmentos (329 verificables)
Procesando: Código Tributario del Ecuador -> 370 fragmentos (369 verificables)
Procesando: Reglamento Comprobantes de Venta y Retención -> 72 fragmentos (71 verificables)
=================================================================
Total fragmentos indexados: 1,507
Total con cabecera verificable: 1,498 (99.40%)
Archivo de salida generado: data/processed/rag_chunks.json
=================================================================
```

---

## 5. Prevención de Inyección Indirecta de Prompts (*Indirect Prompt Injection*)

En la implementación actual, el RAG usa recuperación léxica y devuelve extractos; no envía los fragmentos al selector de herramientas del agente. La normalización retira `\x00` y algunos caracteres de formato, pero no detecta instrucciones maliciosas dentro de los PDF. Python controla cálculos y autorizaciones; esto limita los efectos de una inyección, sin probar inmunidad general. [La auditoría local](07-evaluacion.md#9-auditoría-local-del-rag-posterior-a-la-revisión-de-fuentes) distingue cita formal, fuente y contenido.
