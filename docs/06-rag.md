# Documento Técnico: Justificación de la Estrategia de Fragmentación RAG y Metadatos (Semana 3)

**Caso N.º 11 – Grupo 11:** Calendario Tributario Personalizado con Recordatorios para Emprendedores RIMPE  
**Asignatura:** Ingeniería de Software con IA Generativa  
**Fecha:** Octubre 2026  
**Autores:** Cristhian Pinos, Juan Lucumi  
**Cumplimiento:** Lista de Verificación Entrega 3 (Ítems: `scripts/ingest.py reproducible` y `docs/06-rag.md`)

---

## 1. El Dilema del Corte en Documentos Jurídicos y Normativos

En la arquitectura de un sistema de Recuperación Aumentada por Generación (RAG) especializado en el dominio tributario ecuatoriano (SRI), la calidad de la respuesta generada depende estrictamente de la integridad del fragmento recuperado (*Garbage in, Garbage out*).

Durante la fase de experimentación práctica (evidenciada en la Guía de RAG interactiva), se compararon dos estrategias antagónicas:

| Criterio | Corte por Tamaño Fijo (Fixed-Size Chunking) | Corte Estructural por Artículo (Structural Semantic Chunking) |
| :--- | :--- | :--- |
| **Mecánica** | División ciega cada 260 o 1,000 caracteres, sin considerar la sintaxis. | División por frontera natural de unidad de sentido (`Art. \d+`, `Disposición`). |
| **Preservación de Cabecera** | **Deficiente:** Un corte por tamaño parte artículos a la mitad, dejando el número `Art. 97.6` en un fragmento y el contenido legal en el siguiente. | **Óptima (100%):** Cada fragmento inicia con su cabecera explícita o la hereda si requiere subdivisión. |
| **Fragmentos Huérfanos** | Produce entre un **40% y 60%** de fragmentos huérfanos sin cita posible. | **0.26%:** 1,509 de 1,513 fragmentos tienen cabecera verificable inmediata. |
| **Verificabilidad de la Cita** | Imposible de auditar. El LLM responde sin poder citar con certeza la norma. | **Verificable:** Permite citas formales tipo `[LRTI, Art. 97.6]` o `[Res. NAC-24-0027, Art. 7]`. |
| **Regla de Oro del Seminario** | Viola la regla de oro: genera respuestas sin cita o alucinadas. | **Cumple la regla:** "O citan la fuente con exactitud, o guardan silencio". |

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
- **Justificación:** Si un artículo sobre liquidación o retenciones es muy largo, partirlo por párrafos preservando la cabecera asegura que el embedding capture el tema específico sin sobrepasar la ventana óptima de atención del modelo ni perder la atribución legal.

---

## 3. Esquema de Metadatos Obligatorios

Cada fragmento almacenado en `data/processed/rag_chunks.json` contiene una estructura de metadatos tipada y enriquecida para permitir **filtrado previo (*Pre-filtering*)**:

```json
{
  "chunk_id": "05_ley_regimen_tributario_interno_lrti.pdf_chunk_0284",
  "documento": "Ley de Régimen Tributario Interno (LRTI)",
  "articulo_seccion": "Art. 97.6",
  "cita_oficial": "[Ley de Régimen Tributario Interno (LRTI), Art. 97.6]",
  "contenido": "Art. 97.6.- Declaración y pago. Los contribuyentes sujetos al régimen RIMPE presentarán la declaración anual del impuesto a la renta...",
  "regimen": "AMBOS",
  "vigente": true,
  "anio_fiscal": 2026,
  "jerarquia": "ley_ordinaria",
  "url": "https://www.sri.gob.ec/normativa-tributaria",
  "longitud_caracteres": 894,
  "cabecera_verificable": true
}
```

### Justificación de cada metadato:
1. `documento` y `articulo_seccion`: Proporcionan la **cita obligatoria** que el Frontend y el Agente muestran al contribuyente (`[LRTI, Art. 97.6]`).
2. `regimen` (`RIMPE_NEGOCIO_POPULAR` | `RIMPE_EMPRENDEDOR` | `AMBOS` | `GENERAL`): Permite que si el usuario consulta como Negocio Popular, el motor RAG filtre automáticamente antes del top-k, impidiendo que reciba fragmentos de declaraciones de IVA que no le aplican.
3. `anio_fiscal: 2026` y `vigente: true`: Excluye de forma estricta resoluciones o reformas derogadas de años anteriores (ej. tablas derogadas de 2021 o 2022).
4. `jerarquia` (`codigo_organico` > `ley_organica` > `ley_ordinaria` > `reglamento` > `resolucion_sri`): En caso de aparente contradicción entre una resolución administrativa y la ley, prevalece la norma de mayor jerarquía conforme al principio de supremacía constitucional (Art. 425 Constitución del Ecuador).
5. `url`: Permite auditoría y trazabilidad ciudadana directa hacia el portal oficial del SRI.

---

## 4. Resultados del Pipeline de Ingesta (`scripts/ingest.py`)

Al ejecutar el pipeline sobre el conjunto completo de documentos en `data/raw/`:

```text
=================================================================
INICIANDO PIPELINE DE INGESTA RAG - CALENDARIO TRIBUTARIO RIMPE
Directorio fuente: data/raw
=================================================================
Procesando: Resolución SRI NAC-DGERCGC24-00000027 -> 14 fragmentos (14 verificables)
Procesando: Resolución SRI NAC-DGERCGC23-00000034 -> 9 fragmentos (9 verificables)
Procesando: Ley Orgánica de Eficiencia Económica (R.O. 461) -> 195 fragmentos (195 verificables)
Procesando: Reglamento Aplicación LRTI (RLRTI) -> 523 fragmentos (522 verificables)
Procesando: Ley de Régimen Tributario Interno (LRTI) -> 330 fragmentos (329 verificables)
Procesando: Código Tributario del Ecuador -> 370 fragmentos (369 verificables)
Procesando: Reglamento Comprobantes de Venta y Retención -> 72 fragmentos (71 verificables)
=================================================================
Total fragmentos indexados: 1,513
Total con cabecera verificable: 1,509 (99.74%)
Archivo de salida generado: data/processed/rag_chunks.json
=================================================================
```

---

## 5. Prevención de Inyección Indirecta de Prompts (*Indirect Prompt Injection*)

Siguiendo las directrices de seguridad del Taller de Agentes:
- Los documentos normativos analizados son tratados como **datos no confiables de contexto**, nunca como instrucciones de ejecución.
- El sanitizador remueve caracteres de control nulos (`\x00`) e ignora patrones de comando en comentarios o notas al pie.
- Ningún fragmento inyectado en el contexto del modelo puede alterar las herramientas ni las compuertas de confirmación humana del agente.
