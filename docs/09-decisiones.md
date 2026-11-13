# Registro de Decisiones Arquitectónicas (ADRs) - Calendario Tributario RIMPE

Este documento recopila las Decisiones de Arquitectura de Software (**Architectural Decision Records - ADR**) adoptadas durante el desarrollo y el despliegue de demostración. Describe los controles implementados y sus límites observables; no constituye certificación legal ni garantía absoluta de disponibilidad.

---

## Índice de ADRs

- [ADR-001: Selección Exclusiva de Google Gemini Flash y Purgado de OpenAI](#adr-001-selección-exclusiva-de-google-gemini-flash-y-purgado-de-openai)
- [ADR-002: Desacoplamiento Frontend-Backend Mediante Contrato de Integración API-First](#adr-002-desacoplamiento-frontend-backend-mediante-contrato-de-integración-api-first)
- [ADR-003: Resiliencia con Tenacity y Fallback Determinista Oficial SRI](#adr-003-resiliencia-con-tenacity-y-fallback-determinista-oficial-sri)
- [ADR-004: Inmutabilidad de Fechas y Esquema Estructurado Pydantic v2](#adr-004-inmutabilidad-de-fechas-y-esquema-estructurado-pydantic-v2)
- [ADR-005: Anonimización y Auditoría Conforme a la LOPDP Ecuatoriana](#adr-005-anonimización-y-auditoría-conforme-a-la-lopdp-ecuatoriana)
- [ADR-006: Desacoplamiento Total de Reglas Tributarias en Archivo Versionado](#adr-006-desacoplamiento-total-de-reglas-tributarias-en-archivo-versionado)
- [ADR-007: Render Free como demostración sin persistencia](#adr-007-render-free-como-demostración-sin-persistencia)
- [ADR-008: Minimización de datos y consentimiento para recordatorios](#adr-008-minimización-de-datos-y-consentimiento-para-recordatorios)
- [ADR-009: Abstención ante consultas de evasión y falta de sustento](#adr-009-abstención-ante-consultas-de-evasión-y-falta-de-sustento)
- [ADR-010: Envío puntual verificado sin operador ni perfil persistido](#adr-010-envío-puntual-verificado-sin-operador-ni-perfil-persistido)
- [ADR-011: Transporte de correo por API HTTPS de Mailjet](#adr-011-transporte-de-correo-por-api-https-de-mailjet)
- [ADR-012: Selección acotada de herramientas por Gemini](#adr-012-selección-acotada-de-herramientas-por-gemini)

---

## ADR-001: Selección Exclusiva de Google Gemini Flash y Purgado de OpenAI

* **Fecha:** Octubre 2026 / Actualizado Fase 2 (Semana 2)
* **Estado:** Aceptado e Implementado
* **Autores:** Cristhian Pinos (Desarrollador B) / Grupo 11

### Contexto
El caso de estudio exige generar explicaciones pedagógicas de obligaciones tributarias para microemprendedores basadas en la normativa del SRI. Durante la fase inicial se contemplaron alternativas como OpenAI (`gpt-4o-mini`). Sin embargo, se identificó la necesidad de optimizar costos, reducir latencias, contar con soporte nativo de esquemas JSON estructurados (`responseSchema`) y unificar el stack del equipo con una sola clave provista institucionalmente por Google AI Studio.

### Decisión
Se seleccionó exclusivamente la familia **Google Gemini Flash** (`gemini-3-flash-preview` / `gemini-3.8-flash`) como el único proveedor de inferencia generativa del sistema. Se eliminó de raíz cualquier dependencia de OpenAI (`openai`, `OPENAI_API_KEY`, referencias a GPT) en el código fuente, pruebas, configuraciones y documentación.

**Actualización de fase 4:** el proveedor sigue siendo Gemini, pero el modelo predeterminado pasó a `gemini-3.5-flash-lite` tras observar errores 429/503 del modelo anterior. La aplicación mantiene el catálogo determinista cuando el proveedor falla; véase [evaluación](07-evaluacion.md).

### Consecuencias
* **Positivas:** 
  - Latencia promedio de inferencia inferior a 1,500 ms con tokens suficientes para citas normativas extensas.
  - Generación estructurada nativa garantizando 100% de compatibilidad con esquemas Pydantic v2.
  - Cero costos operativos en entorno de desarrollo académico mediante el tier gratuito de Google AI Studio.
* **Negativas / Desafíos:**
  - El tier gratuito está sujeto a límites de cuota (15 RPM / 1M TPM), lo cual obligó a implementar el mecanismo de resiliencia del [ADR-003](#adr-003-resiliencia-con-tenacity-y-fallback-determinista-oficial-sri).

---

## ADR-002: Desacoplamiento Frontend-Backend Mediante Contrato de Integración API-First

* **Fecha:** Octubre 2026 (Fase 2 - Semana 2)
* **Estado:** Aceptado e Implementado
* **Autores:** Juan Lucumi (Desarrollador A) y Cristhian Pinos (Desarrollador B)

### Contexto
Para evitar que el desarrollo del frontend (React SPA + FullCalendar) quedara bloqueado a la espera de que el backend estuviera completamente desplegado y probado, era imprescindible acordar un contrato de integración inmutable desde el primer día.

### Decisión
Se adoptó una arquitectura **Contract-First / API-First**:
1. Se redactaron los esquemas de intercambio de datos en [`backend/schemas.py`](../backend/schemas.py) (`PerfilTributarioCreate`, `CalculoVencimientosRequest`, `CalendarioTributarioResponse`, `ExplicacionObligacionResponse`).
2. Se estableció un cliente unificado en el frontend (`frontend/src/services/apiClient.js`) con una bandera `USE_MOCKS = true/false`, permitiendo a Juan Lucumi (Desarrollador A) renderizar el calendario y modales con datos sintéticos idénticos a los del backend real.
3. Se asignaron ramas independientes en Git (`feature/frontend-spa` y `feature/backend-core-llm`).

### Consecuencias
* **Positivas:** Desarrollo paralelo 100% independiente con cero dependencias bloqueantes y cero conflictos de archivos en Git.
* **Negativas:** Obliga a mantener sincronizados los modelos Pydantic y las interfaces de JavaScript en caso de modificaciones del contrato.

---

## ADR-003: Resiliencia con Tenacity y Fallback Determinista Oficial SRI

* **Fecha:** Octubre 2026 (Fase 2 - Semana 2)
* **Estado:** Aceptado e Implementado
* **Autores:** Cristhian Pinos (Desarrollador B)

### Contexto
Las APIs de modelos generativos están expuestas a saturación transitoria de cuota (HTTP 429 *Too Many Requests*) o interrupciones de servicio temporales (HTTP 503 *High Demand / Spikes*). Una aplicación orientada a trámites tributarios del SRI no puede mostrar pantallas de error 500 al usuario cuando consulta una obligación fiscal.

### Decisión
Se implementó una política de resiliencia de dos niveles en [`backend/services/llm.py`](../backend/services/llm.py):
1. **Nivel 1 - Reintentos Exponenciales con Tenacity:** Ante errores HTTP 429, HTTP 503 o timeouts de red, se ejecutan hasta **3 reintentos automáticos** con retroceso exponencial (`1s, 2s, 4s`).
2. **Nivel 2 - Fail-Safe / Fallback Determinista Oficial:** Si tras los 3 reintentos la API externa no responde o el entorno se encuentra completamente sin conexión a internet, el sistema activa automáticamente un catálogo de contingencia oficial preconstruido con base en las Resoluciones SRI NAC-24-0027, NAC-23-0034 y la LRTI, entregando la explicación pedagógica y cita legal con HTTP 200 y cero tiempo de inactividad.

### Consecuencias
* **Positivas:** El catálogo de contingencia permite responder a determinadas fallas del proveedor generativo; las pruebas automatizadas verifican ese flujo en los casos cubiertos. No demuestra disponibilidad continua del servicio completo.
* **Negativas:** La respuesta de fallback, aunque normativamente precisa, es estática y no incluye respuestas personalizadas al campo `contexto_adicional` del usuario.

---

## ADR-004: Inmutabilidad de Fechas y Esquema Estructurado Pydantic v2

* **Fecha:** Octubre 2026 (Fase 2 - Semana 2)
* **Estado:** Aceptado e Implementado
* **Autores:** Cristhian Pinos (Desarrollador B)

### Contexto
Los Modelos de Lenguaje Grande (LLMs) son sistemas probabilísticos susceptibles a alucinaciones temporales y aritméticas. En la legislación tributaria ecuatoriana, un error de un solo día en el vencimiento genera multas de al menos \$30 USD e intereses diarios por mora.

### Decisión
1. **Separación de Responsabilidades:** El cálculo de fechas y montos se delega estrictamente al motor determinista en Python ([`backend/services/calculator.py`](../backend/services/calculator.py)) que evalúa el noveno dígito del RUC, fines de semana y feriados del SRI.
2. **Regla Zero Date Hallucination:** La fecha calculada se inyecta como hecho inmutable en el prompt (`backend/prompts/system_v3.md`), prohibiendo taxativamente al modelo recalcular o modificar el plazo.
3. **Validación Estricta:** La salida se valida mediante `RecordatorioEstructurado` de Pydantic v2. Si falta cualquier campo legal o pedagógico, la respuesta es rechazada en origen.

### Consecuencias
* **Positivas:** Tasa de alucinación de fechas y montos reducida al **0.0%** en la matriz benchmark de 10 casos reales.
* **Negativas:** El modelo tiene menor libertad creativa en la redacción de plazos, limitándose a explicar pedagógicamente la fecha fijada.

---

## ADR-005: Anonimización y Auditoría Conforme a la LOPDP Ecuatoriana

* **Fecha:** Octubre 2026 (Fase 2 - Semana 2)
* **Estado:** Aceptado e Implementado
* **Autores:** Cristhian Pinos (Desarrollador B)

### Contexto
La Ley Orgánica de Protección de Datos Personales (LOPDP) de Ecuador (Registro Oficial Suplemento 459) impone severas sanciones por el tratamiento y registro indebido de datos personales de personas naturales (RUC, nombres, correos electrónicos).

### Decisión
Se desarrolló el middleware asíncrono [`backend/middleware/logging_lopdp.py`](../backend/middleware/logging_lopdp.py):
1. **Enmascaramiento de PII:** Todos los RUCs de 13 dígitos se enmascaran conservando solo los primeros 4 dígitos y el sufijo (`0923****001`). Los correos electrónicos se truncan (`j***z@empresa.ec`).
2. **Métricas de Rendimiento:** Inyecta en cada cabecera HTTP la latencia de procesamiento en milisegundos (`X-Process-Time-Ms`) y el sello `X-Data-Protection: LOPDP-Ecuador-Compliant`.
3. **Cero Fuga en Logs:** Ni el servidor uvicorn ni los archivos de auditoría almacenan identificadores en texto claro.

### Consecuencias
* **Positivas:** Menor exposición de identificadores en logs y trazas cubiertos por las pruebas, con latencia de procesamiento observable. El control no equivale a una certificación de cumplimiento de la LOPDP.
* **Negativas:** Requiere decodificación manual autorizada en caso de soporte técnico forense a contribuyentes individuales.

---

## ADR-006: Desacoplamiento Total de Reglas Tributarias en Archivo Versionado

* **Fecha:** Octubre 2026 (Fase 1 / Semana 1)
* **Estado:** Aceptado e Implementado
* **Autores:** Grupo 11

### Contexto
Las reformas tributarias en Ecuador son frecuentes (ej. Ley Orgánica de Eficiencia Económica aprobada en diciembre de 2023 que reformó las cuotas del RIMPE a partir de 2024). Incrustar coeficientes y fechas fijas en el código de Python (*hardcoding*) hace imposible el mantenimiento del software a largo plazo.

### Decisión
Todos los parámetros tributarios se extrajeron a [`config/sri_rules_2026.json`](../config/sri_rules_2026.json):
- Calendario del noveno dígito (1 $\rightarrow$ 10, ..., 0 $\rightarrow$ 28).
- Meses de declaración de IVA y Renta para personas naturales y sociedades.
- Tramos de la tabla progresiva de Negocio Popular (\$0 a \$20.000 USD) y Emprendedor (\$20.000 a \$300.000 USD).
- Catálogo oficial de feriados nacionales ecuatorianos inamovibles.

### Consecuencias
* **Positivas:** 0% de coeficientes "quemados" en el código fuente. La actualización anual solo requiere editar el archivo JSON sin tocar la lógica de negocio.
* **Negativas:** El backend debe validar la existencia e integridad del JSON al arrancar (implementado en el endpoint `/health`).
## ADR-007: Render Free como demostración sin persistencia

**Fecha:** 7 de noviembre de 2026. **Estado:** Aprobada para la demostración de fase 4.

### Contexto

La hoja de ruta pide Render Free. La etapa 5 trasladó perfiles y cola a SQLite para preservar consentimiento y estados. [Render documenta](https://render.com/docs/free) que el sistema de archivos del plan Free se pierde al reiniciar, redesplegar o suspender el servicio; además, lo suspende tras un período de inactividad. Un despliegue Free con registro de contribuyentes daría una falsa expectativa de persistencia y no ejecutaría de forma fiable el escaneo diario.

### Decisión

Se ofrece una demostración pública **sin perfiles persistentes ni escaneo periódico**: `render.yaml` configura `RIMPE_DEMO_READONLY=true` y `SCHEDULER_ENABLED=false`. El envío puntual sí está disponible mediante verificación del correo y confirmación humana (ADR-010), con Mailjet por HTTPS (ADR-011); las claves se guardan solo en el entorno del servicio. El cálculo tributario continúa en Python, el índice RAG se empaqueta en la imagen y Gemini sigue encargado de las explicaciones cuando exista una clave configurada. Frontend y API se sirven desde un solo origen en el contenedor. `Dockerfile` usa un usuario sin privilegios y no copia el archivo `.env` ni la cola JSON histórica.

Para operar recordatorios periódicos con datos personales se necesitaría almacenamiento duradero, una sola instancia del planificador y un nuevo diseño de consentimiento y autorización antes de volver a montar las rutas históricas. Un [disco persistente](https://render.com/docs/disks) sería parte de esa infraestructura. Esa opción no forma parte de la demostración Free autorizada.

### Consecuencias y controles

- La URL Free permite pruebas públicas de calendario, RAG, respuestas, salud y envío puntual con buzón de prueba. No permite demostrar permanencia de perfiles o cola tras reinicio.
- El contenedor empaqueta `rag_chunks.json`, que se recupera en cada arranque sin escribir datos personales.
- El mismo Dockerfile admite un volumen privado persistente, pero eso por sí solo no reactiva el registro ni el escaneo: se necesitan rutas, consentimiento y autorización revisados.
- Se conserva el nombre **ADR-007** porque `ADR-003` ya identifica la estrategia de resiliencia; la numeración `ADR-0003` de la hoja de ruta habría colisionado.

### Decisiones éticas relacionadas

La minimización de datos de la etapa 3 y la aprobación HITL de la etapa 1 se aplican a cualquier despliegue persistente. Las consultas de evasión se rechazan por la compuerta del RAG con cita del Código Tributario. Estas medidas son controles verificables del software; no sustituyen una revisión jurídica ni una auditoría independiente.

---

## ADR-008: Minimización de datos y consentimiento para recordatorios

**Fecha:** Noviembre de 2026. **Estado:** Decisión histórica de la etapa 5; reemplazada para la aplicación pública por ADR-010.

### Contexto

El cálculo del calendario necesita un RUC y parámetros tributarios, pero no requiere guardar un perfil. En cambio, un recordatorio periódico necesita conservar el destinatario, el consentimiento y el estado de aprobación. Los logs y trazas pueden revelar identificadores si registran cuerpos, rutas dinámicas o excepciones.

### Decisión

- El calendario se puede calcular sin registrar el perfil. El alta persistente es una acción separada, autenticada y bloqueada por `RIMPE_DEMO_READONLY=true` en la demostración.
- El consentimiento para notificaciones empieza desactivado, puede revocarse y se vuelve a comprobar antes del despacho. Las rutas de perfiles y cola requieren operador autenticado; el envío exige confirmación humana.
- La auditoría registra método, plantilla de ruta, estado y latencia; no registra cuerpos de petición. Las trazas del agente reducen RUC, correo y contenido de mensajes. Los errores de validación no repiten valores recibidos.
- La base SQLite y sus respaldos se tratan como datos privados. Solo un entorno con almacenamiento duradero y control de acceso puede activar el flujo persistente.

### Consecuencias y evidencia

La demostración permite consultas sin crear registros de perfiles. Esta decisión describe el flujo persistente histórico de la etapa 5, que quedó inactivo por ADR-010. El enmascaramiento de logs no cifra una base; si se reactiva la persistencia, deberá protegerse el volumen y los respaldos. Las pruebas actuales de almacenamiento, verificación de correo y privacidad están en [`backend/tests/test_storage.py`](../backend/tests/test_storage.py), [`backend/tests/test_correo_verificado.py`](../backend/tests/test_correo_verificado.py) y [`backend/tests/test_privacy_boundaries.py`](../backend/tests/test_privacy_boundaries.py).

---

## ADR-009: Abstención ante consultas de evasión y falta de sustento

**Fecha:** Noviembre de 2026. **Estado:** Implementada y evaluada en el conjunto de referencia.

### Contexto

Una respuesta generativa sobre obligaciones fiscales puede resultar perjudicial si inventa una fecha, cita un artículo irrelevante o instruye al usuario para ocultar ingresos o facturas. La recuperación léxica también puede confundir preguntas fuera del alcance del corpus.

### Decisión

- [`backend/services/rag_service.py`](../backend/services/rag_service.py) aplica una compuerta previa a preguntas que solicitan evasión o fraude y devuelve abstención con la cita usada por el código, sin instrucciones para ejecutar la conducta.
- Para preguntas sin sustento suficiente en los fragmentos vigentes, el RAG se abstiene y orienta al usuario hacia el SRI o un profesional. Las respuestas normativas admitidas incluyen citas estructuradas.
- Los cálculos de fechas y montos permanecen en Python. Gemini se limita a explicaciones y recibe las fechas calculadas; el texto de una pregunta no autoriza modificar reglas ni despachar recordatorios.

### Consecuencias y evidencia

La [evaluación comparada](07-evaluacion.md#8-comparación-de-la-semana-4) obtuvo TP=4, TN=16, FP=0 y FN=0 sobre 20 preguntas. El [caso F4-15](08-pruebas.md#f4-15-consulta-orientada-a-omitir-facturas) verificó la abstención en la URL pública; [`backend/tests/test_rag_service.py`](../backend/tests/test_rag_service.py) cubre más ejemplos. El filtro por términos y el conjunto evaluado son limitados: deben ampliarse y revisarse al actualizar el corpus, sin presentar el resultado como inmunidad general frente a evasión o inyección.

---

## ADR-010: Envío puntual verificado sin operador ni perfil persistido

**Fecha:** 11 de noviembre de 2026. **Estado:** Implementado y verificado en la demostración pública.

El usuario pidió retirar cuentas de operador y perfiles guardados del flujo público. Mantener el despacho SMTP abierto a cualquier correo permitiría abuso de la cuenta de salida. Se sustituyó la autorización de operador por un código de seis dígitos enviado al mismo destinatario, válido diez minutos y consumido una sola vez. El usuario confirma expresamente el envío. Se limitan solicitudes por correo y globalmente; códigos y contadores se guardan solo en memoria, sin registrar perfiles tributarios ni códigos en logs.

Las rutas públicas antiguas de perfiles y cola no se montan; las rutas directas del agente rechazan el despacho sin verificación. El código histórico de escaneo y almacenamiento queda inactivo para no publicar una cola sin control de acceso. Python sigue calculando las obligaciones y el agente prepara el recordatorio. El diseño inicial usaba SMTP; ADR-011 lo sustituyó por Mailjet mediante HTTPS, compatible con Render Free. La aceptación del proveedor, el fallo y el resultado incierto se distinguen en la respuesta. Un reinicio invalida códigos pendientes y reinicia los contadores en memoria; para varias instancias se necesita un limitador compartido.

---

## ADR-011: Transporte de correo por API HTTPS de Mailjet

**Fecha:** 11 de noviembre de 2026. **Estado:** Implementado y comprobado con el código y el recordatorio recibidos en la demostración pública.

Render Free bloquea los puertos SMTP habituales. El remitente institucional individual se validó en Mailjet sin administrar el DNS universitario; esta validación no garantiza aceptación por las políticas del dominio ni entrega en la bandeja. Para el flujo puntual de ADR-010 se sustituyó SMTP por la API HTTPS de Mailjet. `MAILJET_API_KEY`, `MAILJET_SECRET_KEY` y `MAILJET_FROM_EMAIL` se leen únicamente en el servidor. El código de verificación y el recordatorio usan el mismo transporte; se conserva la confirmación HITL y el cálculo en Python.

`ENVIADO` significa que Mailjet devolvió un `MessageID` aceptado, no que el destinatario recibió o leyó el mensaje. Una respuesta HTTP rechazada queda `ERROR_ENVIO`; una pérdida de respuesta o una respuesta sin confirmación queda `ESTADO_INCIERTO`. El código temporal conserva su validez si la respuesta del proveedor es incierta. Las pruebas automatizadas simulan aceptación, rechazo y timeout; además, el usuario confirmó la recepción real del código y del recordatorio en Gmail desde la demo. Esa prueba puntual no garantiza entregas futuras. ADR-010 describe el diseño inicial con SMTP y queda actualizado por esta decisión.

---

## ADR-012: Selección acotada de herramientas por Gemini

**Fecha:** Noviembre de 2026. **Estado:** Implementado y comprobado en Render con datos sintéticos, sin despacho desde la ruta del agente.

La revisión académica observó que el bucle del agente seguía un orden fijo decidido por `if/elif`, aunque la documentación lo llamaba selección dinámica. En la ruta `/api/agente/ejecutar`, Gemini puede proponer la siguiente herramienta entre las que Python habilita según las dependencias del estado. Python verifica que la propuesta pertenezca a esa lista, construye los parámetros y ejecuta las herramientas. No se envían al selector la instrucción libre ni RUC, nombre, correo o importes. Ante una respuesta inválida, falta de clave o error del proveedor, se usa el orden seguro comprobado. Las trazas registran herramienta, candidatas y origen de la selección; no el razonamiento libre del modelo.

El agente tiene máximo de iteraciones y la ruta comparte la cuota generativa, reservando cuatro llamadas posibles por ejecución. La ruta del agente rechaza envíos; el envío real conserva el código de un solo uso y la confirmación en `/api/correo`. Ese flujo usa el orden determinista para que una caída de Gemini no desperdicie un código ya consumido. La selección del modelo no calcula fechas ni montos y no puede autorizar un destinatario. Las pruebas cubren elección válida, elección prohibida, fallo de Gemini, orden alternativo, cuota y compuerta HITL. En Render, una ejecución sintética registró tres herramientas elegidas con origen `gemini` y dejó el envío pendiente de confirmación.
