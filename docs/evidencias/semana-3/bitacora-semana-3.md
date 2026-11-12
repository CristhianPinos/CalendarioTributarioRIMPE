# Bitácora Técnica de Trabajo - Semana 3 (Fase 3)

**Proyecto:** Calendario Tributario Personalizado con Recordatorios para Emprendedores RIMPE  
**Fase:** Fase 3 – Conocimiento especializado: RAG, agente y calidad (Semana 3)  
**Integrantes:**
- Juan Lucumi (Desarrollador A): Líder de Frontend e Integración Web
- Cristhian Pinos (Desarrollador B): Líder de Backend Core, Arquitectura de IA & QA Lead  
**Rama de Trabajo:** `main` (Full-Stack Integrado con RAG y Agente)  
**Periodo:** Octubre 2026 / Fase 3 – Semana 3  
**Estado General:** 100% Implementado, Evaluado y Verificado (Métricas al 100%, 0 Fugas de Seguridad)

---

## 1. Registro Cronológico de Tareas Desarrolladas

### Paso 1: Externalización Total de Parámetros Tributarios (`config/parametros.yaml`)
- Se implementó la configuración centralizada en `config/parametros.yaml` y `config/sri_rules_2026.json`:
  - Salario Básico Unificado (SBU): $460 USD.
  - Tarifas vigentes de IVA: 15% (general), 5% (materiales de construcción), 0% (canasta básica / servicios de salud y educación).
  - Umbrales de categorización RIMPE: hasta $20.000 USD (Negocio Popular) y hasta $300.000 USD (Emprendedor).
  - Escala de cuotas fijas progresivas del Impuesto a la Renta para Negocios Populares ($0 a $60 USD) según el Art. 23 de la Ley Orgánica de Eficiencia Económica y Generación de Empleo (R.O. 461).
  - Calendario oficial de feriados nacionales ecuatorianos 2026/2027.
  - Parámetros operativos del agente: máximo 5 iteraciones, antelación de recordatorios de 5 días hábiles.
- Implementación de `backend/services/config_loader.py` con caché en memoria y tipado estricto.
- Implementación de `backend/tests/test_config_loader.py` (**8 pruebas unitarias pasando**).
- **Cumplimiento:** 0% de tarifas o calendarios quemados en código o prompts.

### Paso 2: Pipeline de Ingesta y Fragmentación Semántica (`scripts/ingest.py`)
- Procesamiento y extracción reproducible de texto sobre los 7 documentos oficiales del SRI y Registro Oficial ubicados en `data/raw/` (782 páginas procesadas):
  1. *Ley de Régimen Tributario Interno (LRTI)* codificada.
  2. *Reglamento para la Aplicación de la LRTI (RLRTI)*.
  3. *Resolución SRI NAC-DGERCGC24-00000027* (normas para declaración y pago RIMPE 2024-2026).
  4. *Resolución SRI NAC-DGERCGC23-00000034* (tarifas y directrices RIMPE).
  5. *Ley Orgánica de Eficiencia Económica y Generación de Empleo* (R.O. Suplemento 461).
  6. *Guía para Contribuyentes RIMPE (SRI)*.
  7. *Código Tributario del Ecuador*.
- Implementación del algoritmo de corte semántico por **Artículo / Sección**:
  - Expresión regular robusta de detección jerárquica con prevención de fragmentos huérfanos.
  - Inyección de cabecera contextual obligatoria en cada fragmento: `[Documento | Artículo/Sección | Régimen | Vigencia: 2026 | URL Oficial]`.
  - Sub-fragmentación con solapamiento (*overlap*) de 100 caracteres únicamente cuando un artículo supera los 1,200 caracteres, preservando tablas y párrafos indivisibles.
- Generación de `data/processed/rag_chunks.json`: **1,513 fragmentos indexados**, 1,509 con cabecera de artículo estandarizada (99.74%).
- Redacción del documento técnico formal `docs/06-rag.md` con justificación técnica de la estrategia de partición.
- Implementación de `backend/tests/test_ingest.py` (**4 pruebas unitarias pasando**).

### Paso 3: Motor RAG con Pre-filtrado, Citas Obligatorias y Regla de Silencio (`backend/services/rag_service.py`)
- Implementación del motor de recuperación léxica BM25 (Okapi BM25 con $k_1 = 1.2$, $b = 0.75$) en memoria:
  - Pre-filtrado estricto por metadatos: exclusión de normas derogadas o no vigentes en el ejercicio fiscal 2026, y filtrado por compatibilidad de régimen (`RIMPE_NEGOCIO_POPULAR`, `RIMPE_EMPRENDEDOR`, `AMBOS`).
  - Formato estandarizado e inquebrantable de citas jurídicas: `[Documento, Art. X]`.
  - Doble compuerta de abstención (*Regla de Silencio*):
    - Detección y rechazo de consultas que solicitan asesoría para evasión fiscal, citando el Art. 15 del Código Tributario.
    - Detección de consultas sobre liquidaciones particulares o temas fuera de dominio (recetas, criptomonedas).
    - Silencio institucional formal ante score de recuperación inferior al umbral mínimo ($< 2.8$).
- Integración en la API mediante `backend/routers/rag_router.py` (`POST /api/rag/consultar`).
- Implementación de `backend/tests/test_rag_service.py` (**6 pruebas unitarias pasando**).

### Paso 4: Agente Tributario Determinista con 4 Herramientas y Límite de Iteraciones (`backend/services/agent_service.py`)
- Implementación del `AgenteTributarioRIMPE` con 4 herramientas formales tipadas con Pydantic v2:
  1. `tool_calcular_vencimientos`: cálculo determinista basado en el 9no dígito del RUC y traslado por feriados.
  2. `tool_calcular_iva`: cálculo determinista consumiendo tarifas desde `config/parametros.yaml`.
  3. `tool_redactar_recordatorio`: redacción estructurada con fundamento en fragmentos normativos del motor RAG.
  4. `tool_enviar_recordatorio`: compuerta humana (HITL) que retiene el mensaje en `PENDIENTE_CONFIRMACION` salvo autorización explícita (`confirmacion_usuario=True`).
- Límite estricto de ejecución de **máximo 5 iteraciones**, evitando bucles infinitos y registrando la traza auditable de cada herramienta invocada.
- Integración en la API mediante `backend/routers/agente_router.py` (`POST /api/agente/ejecutar`).
- Implementación de `backend/tests/test_agent_tools.py` (**12 pruebas unitarias pasando**, incluyendo pruebas de resiliencia ante inyección de prompts y construcción de recordatorios).

### Paso 5: Flujo Programado Diario y Cola de Confirmación Humana (`backend/services/scheduler.py`)
- Implementación del flujo de cinta diaria (`ejecutar_tarea_diaria_vencimientos`):
  - Escaneo automático de la base de contribuyentes.
  - Detección de obligaciones con vencimiento dentro de los próximos **5 días hábiles** usando el calendario de feriados del SRI.
  - Orquestación automática con el agente para redacción con citas RAG.
  - Encolamiento idempotente en estado `PENDIENTE_CONFIRMACION` (evita duplicidad de recordatorios para la misma fecha y obligación).
  - Despacho y generación de identificador de auditoría (`AUD-DISPATCH-XXX`) únicamente tras confirmación humana explícita.
- Integración en la API mediante `backend/routers/flujo_router.py` (`POST /api/flujo/ejecutar-tarea-diaria`, `GET /api/flujo/recordatorios-pendientes`, `POST /api/flujo/confirmar-recordatorio/{id}`).
- Elevación de versión del sistema a `3.2.0` en `backend/main.py`.
- Implementación de `backend/tests/test_scheduler.py` (**5 pruebas unitarias pasando**).

### Paso 6: Evaluación Formal de Calidad, Agente y RAG (`eval/run_eval.py` y `docs/07-evaluacion.md`)
- Creación del dataset de referencia `eval/dataset_evaluacion.json`:
  - **10 Perfiles Dorados** (dígitos 0 al 9, combinando Negocio Popular, Emprendedor y actividades excluidas, con 23 fechas esperadas y justificaciones legales de traslados).
  - **20 Preguntas Normativas** (16 consultas legítimas de deberes tributarios + 4 casos críticos de abstención).
- Implementación del arnés automatizado `eval/run_eval.py`:
  - Precisión de perfiles: **100.0%** (10/10).
  - Coincidencia de fechas: **100.0%** (23/23).
  - Hit@3 en preguntas legítimas: **100.0%** (16/16).
  - Tasa de citas obligatorias: **100.0%** (16/16).
  - Precisión, Recall y F1-Score de Abstención: **100.0%** (0 Fugas de Seguridad, 0 Falsos Rechazos).
- Exportación de resultados a `eval/resultados_evaluacion.json`.
- Redacción del reporte exhaustivo `docs/07-evaluacion.md` con análisis de fallos diagnosticados (recuperación vs. generación), matriz de confusión, tablas detalladas y reproducibilidad.

### Paso 7: Consolidación de Evidencias Técnicas (`docs/evidencias/semana-3/`)
- Creación de la bitácora técnica `docs/evidencias/semana-3/bitacora-semana-3.md`.
- Creación del registro formal de decisiones arquitectónicas y pruebas de seguridad en `docs/evidencias/semana-3/decisiones-semana-3.md`.
- Verificación de la suite de pruebas unitarias (35 pruebas en verde en menos de 1 segundo).
- Auditoría de enlaces: 100% rutas relativas portables, 0 enlaces absolutos locales.

---

## 2. Resumen Consolidado de Pruebas Unitarias (Fase 3)

| Suite de Prueba | Archivo de Prueba | Casos Ejecutados | Tiempo | Estado |
| :--- | :--- | :---: | :---: | :---: |
| Parámetros y Configuración | `backend/tests/test_config_loader.py` | 8 | 0.08s | **Aprobado** |
| Ingesta y Fragmentación | `backend/tests/test_ingest.py` | 4 | 0.22s | **Aprobado** |
| Motor RAG y Regla de Silencio | `backend/tests/test_rag_service.py` | 6 | 0.18s | **Aprobado** |
| Herramientas, HITL e Inyección | `backend/tests/test_agent_tools.py` | 12 | 0.25s | **Aprobado** |
| Flujo Programado Diario | `backend/tests/test_scheduler.py` | 5 | 0.19s | **Aprobado** |
| **Total Fase 3** | **5 archivos de prueba** | **35 casos** | **0.92s** | **100% Verde** |
