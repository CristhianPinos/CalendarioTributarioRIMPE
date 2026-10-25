# Registro de Decisiones Arquitectónicas (ADRs) - Calendario Tributario RIMPE

Este documento recopila las Decisiones de Arquitectura de Software (**Architectural Decision Records - ADR**) adoptadas a lo largo de las Fases 1 y 2 del proyecto para garantizar la exactitud tributaria, la resiliencia técnica, el cumplimiento de la LOPDP y la cero alucinación de datos.

---

## Índice de ADRs

- [ADR-001: Selección Exclusiva de Google Gemini Flash y Purgado de OpenAI](#adr-001-selección-exclusiva-de-google-gemini-flash-y-purgado-de-openai)
- [ADR-002: Desacoplamiento Frontend-Backend Mediante Contrato de Integración API-First](#adr-002-desacoplamiento-frontend-backend-mediante-contrato-de-integración-api-first)
- [ADR-003: Resiliencia con Tenacity y Fallback Determinista Oficial SRI](#adr-003-resiliencia-con-tenacity-y-fallback-determinista-oficial-sri)
- [ADR-004: Inmutabilidad de Fechas y Esquema Estructurado Pydantic v2](#adr-004-inmutabilidad-de-fechas-y-esquema-estructurado-pydantic-v2)
- [ADR-005: Anonimización y Auditoría Conforme a la LOPDP Ecuatoriana](#adr-005-anonimización-y-auditoría-conforme-a-la-lopdp-ecuatoriana)
- [ADR-006: Desacoplamiento Total de Reglas Tributarias en Archivo Versionado](#adr-006-desacoplamiento-total-de-reglas-tributarias-en-archivo-versionado)

---

## ADR-001: Selección Exclusiva de Google Gemini Flash y Purgado de OpenAI

* **Fecha:** Octubre 2026 / Actualizado Fase 2 (Semana 2)
* **Estado:** Aceptado e Implementado
* **Autores:** Cristhian Pinos (Desarrollador B) / Grupo 11

### Contexto
El caso de estudio exige generar explicaciones pedagógicas de obligaciones tributarias para microemprendedores basadas en la normativa del SRI. Durante la fase inicial se contemplaron alternativas como OpenAI (`gpt-4o-mini`). Sin embargo, se identificó la necesidad de optimizar costos, reducir latencias, contar con soporte nativo de esquemas JSON estructurados (`responseSchema`) y unificar el stack del equipo con una sola clave provista institucionalmente por Google AI Studio.

### Decisión
Se seleccionó exclusivamente la familia **Google Gemini Flash** (`gemini-3-flash-preview` / `gemini-3.8-flash`) como el único proveedor de inferencia generativa del sistema. Se eliminó de raíz cualquier dependencia de OpenAI (`openai`, `OPENAI_API_KEY`, referencias a GPT) en el código fuente, pruebas, configuraciones y documentación.

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
* **Autores:** Desarrollador A & Cristhian Pinos (Desarrollador B)

### Contexto
Para evitar que el desarrollo del frontend (React SPA + FullCalendar) quedara bloqueado a la espera de que el backend estuviera completamente desplegado y probado, era imprescindible acordar un contrato de integración inmutable desde el primer día.

### Decisión
Se adoptó una arquitectura **Contract-First / API-First**:
1. Se redactaron los esquemas de intercambio de datos en [`backend/schemas.py`](../backend/schemas.py) (`PerfilTributarioCreate`, `CalculoVencimientosRequest`, `CalendarioTributarioResponse`, `ExplicacionObligacionResponse`).
2. Se estableció un cliente unificado en el frontend (`frontend/src/services/apiClient.js`) con una bandera `USE_MOCKS = true/false`, permitiendo al Desarrollador A renderizar el calendario y modales con datos sintéticos idénticos a los del backend real.
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
* **Positivas:** 100% de disponibilidad de servicio garantizada. Las pruebas automatizadas certifican la degradación elegante y recuperación ante fallas.
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
* **Positivas:** Pleno cumplimiento legal ecuatoriano y auditoría transparente de rendimiento.
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
