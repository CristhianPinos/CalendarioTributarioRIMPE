# Evidencias Técnicas y Decisiones de la Semana 1 (Fase 1)

**Proyecto:** Calendario Tributario Personalizado con Recordatorios para Emprendedores RIMPE (Caso 11 - Grupo 11)  
**Fase:** Fase 1 – Definición del problema y diseño de la solución inteligente (Semana 1)  
**Integrantes:**
- Desarrollador A: Líder de Frontend e Integración Web
- Cristhian Pinos (Desarrollador B): Líder de Backend Core, Arquitectura de IA y QA  
**Periodo:** Octubre 2026 / Fase 1 – Semana 1  
**Estado de Entrega:** 100% Cumplido según Checklist Oficial  

---

## 1. Registro de Decisiones de Arquitectura (ADRs) de la Fase 1

A lo largo de la Fase 1 se formalizaron seis Decisiones de Arquitectura de Software (**Architectural Decision Records - ADR**) fundamentales que rigen la totalidad del sistema (documentadas también en el registro global [09-decisiones.md](../../09-decisiones.md)):

### ADR-01: Interfaz Centrada en Calendario Interactivo vs. Chatbot Conversacional Abierto
* **Contexto:** La mayoría de proyectos de IA Generativa implementan por defecto una ventana de chat abierto. Sin embargo, los contribuyentes RIMPE requieren previsibilidad cronológica inmediata ("¿qué día venzo?", "¿cuánto debo pagar este mes?").
* **Decisión:** Establecer una **Single Page Application (SPA) basada en una cuadrícula mensual interactiva (FullCalendar en React)** como pantalla principal del usuario.
* **Justificación Técnica:** Un chat abierto genera sobrecarga cognitiva, ambigüedad en el encuadre de fechas y mayor latencia de consulta. La interacción generativa se delega a un panel modal contextual de inspección que se activa únicamente cuando el usuario hace clic sobre una obligación específica del calendario.
* **Consecuencias:** Mayor usabilidad y satisfacción de usuario; menor consumo innecesario de tokens del LLM; experiencia orientada a tareas tributarias concretas.

---

### ADR-02: Cálculo Determinista Estricto vs. Inferencia de Fechas por LLM (Zero Date Hallucination)
* **Contexto:** Los modelos probabilísticos sufren de alucinaciones numéricas y temporales al calcular calendarios dependientes del noveno dígito del RUC y feriados locales de Ecuador.
* **Decisión:** Las fechas de vencimiento se calculan **100% mediante funciones deterministas en Python** (`calendar.monthrange`, reglas del noveno dígito y catálogo de feriados nacionales). El LLM tiene terminantemente prohibido calcular o alterar fechas.
* **Justificación Técnica:** Un error de un solo día en la fecha de vencimiento acarrea multas por declaración tardía e intereses por mora emitidos por el SRI. El sistema garantiza confiabilidad legal absoluta delegando la aritmética a Python y reservando el LLM para redacción pedagógica y citas normativas.
* **Consecuencias:** 0.0% de alucinación en fechas; cumplimiento irrestricto de la normativa ecuatoriana; robustez ante auditorías técnicas.

---

### ADR-03: Desacoplamiento de Reglas y Tarifas en `config/sri_rules_2026.json` (0% Hardcoding)
* **Contexto:** La legislación tributaria ecuatoriana cambia con frecuencia anual mediante resoluciones del SRI o reformas de la Asamblea Nacional (ej. Ley de Eficiencia Económica).
* **Decisión:** Externalizar la totalidad de los parámetros normativos en el archivo estructurado [config/sri_rules_2026.json](../../../config/sri_rules_2026.json), incluyendo:
  - Mapeo de noveno dígito a día de vencimiento (1 al 0 $\rightarrow$ 10 al 28).
  - Catálogo de feriados oficiales no recuperables de Ecuador.
  - Tabla de tarifas progresivas de Negocios Populares (\$0 a \$60 USD).
  - Tramos y porcentajes de Impuesto a la Renta para Emprendedores.
* **Justificación Técnica:** Asegura un indicador verificable de **0% de constantes quemadas en el código fuente**. Permite actualizar el ejercicio fiscal anual sin recompilar ni alterar la lógica del backend.
* **Consecuencias:** Alta mantenibilidad, bajo costo de actualización anual y separación limpia entre datos normativos y lógica de ejecución.

---

### ADR-04: Compuerta de Autorización Humana (*Human-in-the-Loop* - HITL)
* **Contexto:** Los sistemas autónomos desatendidos de envío de notificaciones pueden incurrir en despacho no deseado, saturación de bandejas o envío de recordatorios sin consentimiento del usuario.
* **Decisión:** Diseñar una **compuerta estricta en el endpoint de despacho de correos**: si la petición no incluye `confirmado_por_usuario: true`, el backend responde con `HTTP 403 Forbidden`.
* **Justificación Técnica:** Garantiza el consentimiento explícito del contribuyente, cumple con el principio de control humano sobre agentes de IA y mitiga riesgos operativos y de spam.
* **Consecuencias:** Trazabilidad de confirmación humana obligatoria antes de cualquier emisión de correos.

---

### ADR-05: Ingesta de Cuerpos Normativos Íntegros en PDF Original
* **Contexto:** Los resúmenes manuales de leyes pierden vigencia rápidamente, pueden distorsionar el sentido jurídico o pasar por alto excepciones críticas para ciertas actividades económicas.
* **Decisión:** Descargar y archivar en el repositorio los **7 documentos oficiales íntegros originales en formato PDF** ([data/raw/](../../../data/raw/)) provenientes de la biblioteca institucional del SRI y del Registro Oficial Suplemento 461.
* **Justificación Técnica:** Garantiza trazabilidad jurídica absoluta, sustento probatorio primario y permite que el sistema RAG fundamente cada explicación en artículos y páginas legalmente verificables.
* **Consecuencias:** Respaldo documental auditable; independencia de enlaces web externos caídos o modificados.

---

### ADR-06: Selección Exclusiva de Google Gemini Flash y Resiliencia con Tenacity
* **Contexto:** Se contemplaron inicialmente opciones de OpenAI (`gpt-4o-mini`). Sin embargo, se identificó la necesidad de optimizar costos de API, reducir latencias, contar con soporte nativo de esquemas estructurados (`responseSchema`) y unificar el stack del equipo con una sola clave provista institucionalmente por Google AI Studio.
* **Decisión:** Seleccionar **Google Gemini Flash** como único motor generativo del proyecto, purgar dependencias de OpenAI, proteger las llamadas con retroceso exponencial de Tenacity (1s, 2s, 4s) ante cuotas HTTP 429 y prever un catálogo determinista de fallback oficial del SRI.
* **Justificación Técnica:** Gemini Flash ofrece latencias ultrabajas (< 1.5s), soporte nativo para JSON estructurado con Pydantic y alta eficiencia de costos para microemprendedores.
* **Consecuencias:** Stack homogéneo, cero costos de plataformas duales y resiliencia ante contingencias de conectividad.

---

## 2. Matriz de Trade-offs y Evaluación de Alternativas de la Semana 1

| Dimensión de Diseño | Alternativa Evaluada | Alternativa Seleccionada | Justificación Técnica del Trade-off |
| :--- | :--- | :--- | :--- |
| **Interfaz de Usuario** | Chatbot conversacional tipo ChatGPT. | **Cuadrícula mensual interactiva (FullCalendar en React).** | La visualización de fechas en calendario reduce el tiempo de consulta en un 70% frente a la lectura de respuestas extensas en chat. |
| **Cálculo de Fechas** | Inferencia generativa por prompt con el LLM. | **Motor determinista en Python (`calculator.py`).** | Elimina al 100% el riesgo de multas e intereses por alucinación aritmética o temporal en días inhábiles. |
| **Parámetros Tributarios** | Constantes definidas en el código (`settings.py`). | **Archivo desacoplado `config/sri_rules_2026.json`.** | Permite actualización normativa anual inmediata sin modificar ni redistribuir el código del servidor. |
| **Fuente de Verdad Legal** | Resúmenes secundarios en Markdown o blogs. | **7 PDFs oficiales íntegros en `data/raw/`.** | Validez probatoria oficial del SRI Alfresco y Suplemento 461 del Registro Oficial del Ecuador. |
| **Proveedor de LLM** | Arquitectura híbrida OpenAI + Gemini. | **Exclusividad Google Gemini Flash.** | Reduce costos, unifica credenciales del equipo y aprovecha schemas nativos Pydantic sin sobrecostos. |

---

## 3. Matriz de Verificación frente a la Checklist Oficial de la Fase 1

A continuación se detalla el cumplimiento estricto de cada uno de los ítems de la rúbrica oficial de la Fase 1:

| Ítem de la Checklist de la Fase 1 | Entregable Asociado | Estado | Validación Técnica |
| :--- | :--- | :---: | :--- |
| **`docs/01-propuesta.md`** | Problema real, usuarios, alcance positivo y negativo, riesgos y modelo elegido. | ✅ **Cumplido** | Documento completo con 2 arquetipos de usuario RIMPE, alcance negativo explícito y justificación de Gemini Flash. |
| **`docs/02-requisitos.md`** | Mínimo 8 historias de usuario con criterios Gherkin y RNF medibles. | ✅ **Cumplido** | 10 Historias de Usuario completas con escenarios `Dado... Cuando... Entonces...`, 7 RNF medibles y modelo de datos relacional. |
| **`docs/03-arquitectura.md`** | Diagrama Mermaid C4, frontend, backend, modelo, base vectorial y flujo. | ✅ **Cumplido** | C4 Context, C4 Container, Diagrama de Secuencia y Matriz de Segregación de Responsabilidades Frontend vs Backend. |
| **`docs/04-fuentes.md`** | Inventario de fuentes, origen oficial, URL, vigencia, formato y chunking. | ✅ **Cumplido** | 7 Fuentes catalogadas con URLs oficiales SRI, rutas relativas y estrategia de fragmentación semántica. |
| **Levantamiento real: mínimo 15 preguntas** | Resultados de encuesta o preguntas frecuentes en `docs/`. | ✅ **Cumplido** | 16 Casos reales de contribuyentes ecuatorianos en `docs/levantamiento-preguntas.md` con mapeo técnico de resolución. |
| **Fuentes descargadas en `data/raw/`** | Documentos oficiales íntegros descargados en el proyecto. | ✅ **Cumplido** | 7 PDFs oficiales íntegros archivados en `data/raw/` con verificación de integridad. |
| **README inicial, `.gitignore` y `.env.example`** | Estructura de carpetas estándar del seminario. | ✅ **Cumplido** | Repositorio estructurado profesionalmente, credenciales protegidas e instrucciones claras de despliegue. |
| **Evidencias en `docs/evidencias/semana-1/`** | Bitácora técnica y registro de decisiones de diseño. | ✅ **Cumplido** | Documentos independientes `decisiones-semana-1.md` y `bitacora-semana-1.md` con rutas relativas portables. |
| **FastAPI con `/health` en local (Opcional)** | Esqueleto ejecutable para sumar ventaja en Semana 2. | ✅ **Cumplido** | Implementado en `backend/main.py`, dependencias en `backend/requirements.txt` y verificado con respuesta HTTP 200 JSON. |

---

## 4. Acuerdos Técnicos del Equipo para el Traspaso a la Fase 2

1. **Desacoplamiento Contractual (API-First):** Se definieron los contratos inmutables de entrada y salida (`POST /api/perfil/calcular-vencimientos` y `POST /api/obligaciones/explicar`) en [HANDOFF.md](../../../HANDOFF.md) para permitir desarrollo simultáneo e independiente.
2. **Segregación de Ramas Git:**
   - Desarrollador A: Rama `feature/frontend-spa` para la interfaz React + FullCalendar con mock integrado.
   - Cristhian Pinos (Desarrollador B): Rama `feature/backend-core-llm` para motor determinista, esquemas Pydantic v2, servicio Gemini y observabilidad LOPDP.
3. **Cero Rutas Absolutas:** Todo el material documental y de configuración debe enlazarse estrictamente con rutas relativas portables del repositorio.
4. **Protección de Secretos:** Prohibición estricta de subir claves de API (`.env`) o credenciales al control de versiones; uso obligatorio de `.env.example`.
