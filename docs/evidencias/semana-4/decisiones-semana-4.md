# Evidencias Técnicas y Decisiones de la Semana 4 (Fase 4)

**Proyecto:** Calendario Tributario Personalizado con Recordatorios para Emprendedores RIMPE

**Fase:** Fase 4 – Preparación para Docker, despliegue y demostración pública (Semana 4)

**Periodo:** Noviembre de 2026 / Fase 4 – Semana 4

**Integrantes:** Juan Lucumi (Desarrollador A) y Cristhian Pinos (Desarrollador B)

**Estado:** Demostración y CI verificados; entrega formal pendiente.

---

## 1. Decisiones Técnicas de la Semana 4

La [bitácora](bitacora-semana-4.md#2-observaciones-de-la-revisión-y-respuesta-del-proyecto) reúne las observaciones recibidas y las mejoras aplicadas. El equipo confirmó que los comentarios de la revisión coinciden en lo esencial con el informe escrito; aquí se justifican las decisiones técnicas derivadas de ellos.

### Render Free como demostración

El responsable del proyecto eligió Render Free solo para demostración tras revisar que el plan pierde archivos locales al suspenderse o reiniciarse. `RIMPE_DEMO_READONLY=true` bloquea el alta de perfiles y `SCHEDULER_ENABLED=false` evita prometer recordatorios periódicos que no sobrevivirían a un reinicio. [ADR-007](../../09-decisiones.md) conserva la justificación técnica.

### Un origen para frontend y API

La imagen compila React y sirve sus archivos desde FastAPI. Esto evita una segunda plataforma de hosting y permite que el cliente use el mismo origen. El servidor Vite conserva un proxy local hacia el backend para desarrollo.

### Evidencia basada en comprobaciones observadas

Las mediciones locales se publican como **locales**. La URL y los resultados de Render se incorporan únicamente después de comprobar la respuesta pública. La prueba de una tarifa hipotética usa un YAML temporal; las reglas oficiales del repositorio permanecen intactas.

### Minimización de datos y rechazo de consultas de evasión

Las decisiones éticas se describen en [ADR-008 a ADR-012](../../09-decisiones.md). El calendario se calcula sin guardar un perfil; el envío puntual requiere un código recibido en el correo elegido y confirmación expresa. El registro administrativo y el escaneo periódico son parte del diseño histórico, sin rutas montadas en la aplicación actual. El RAG se abstiene ante solicitudes de evasión o falta de sustento. Las pruebas cubren casos concretos, sin presentar esos controles como garantías absolutas.

### Selección acotada de herramientas

La observación de que el agente seguía un orden fijo llevó a permitir que Gemini elija solo entre herramientas habilitadas por Python. La decisión se valida y se traza; ante fallos se conserva el recorrido seguro. El flujo de correo verificado permanece determinista después de consumir el código temporal. [ADR-012](../../09-decisiones.md) explica la separación y la cuota compartida.

### Protección de cuota y del contenido del correo

La revisión señaló la falta de un límite de tasa para las rutas de IA y el riesgo de insertar texto variable sin escape en el HTML del correo. Se añadieron contadores por cliente e instancia con `429` y `Retry-After`, se limitaron las entradas y los tokens, y se escapó el texto del mensaje. Los contadores se reinician con el proceso: escalar a varias instancias requeriría un almacén compartido. El destinatario sigue verificándose con un código y el despacho requiere confirmación expresa.

### CI antes del despliegue y evidencia por commit

`render.yaml` declara `autoDeployTrigger: checksPass`. Se añadió detección de secretos al flujo que ya ejecutaba pruebas, evaluación, frontend y Docker. Una prueba obsoleta bloqueó la primera corrida y se corrigió sin modificar las reglas tributarias. `/health` expone el SHA de Render para comprobar que la evaluación pública y la corrida verde corresponden al mismo código. El commit documental de cierre usó `[skip render]` para conservar desplegado el SHA evaluado.

### Explicaciones con contingencia y límites del RAG

Ante respuestas 429/503 de Gemini se conserva el catálogo determinista y se informa su origen. Flash Lite produjo una respuesta real en la demo, pero su disponibilidad futura no está garantizada. El RAG distingue cita formal de fuente pertinente. Para PREG-02 se decidió priorizar, solo en consultas de declaraciones de IVA de Negocio Popular, el fragmento verificado de LRTI art. 97.9 que ya supera los filtros de recuperación; también se muestra su oración pertinente y se advierte sobre actividades excluidas. La [evaluación local](../../07-evaluacion.md#11-corrección-local-de-la-consulta-preg-02) aprobó y falta comprobar esta revisión en Render. Estas decisiones no cambian las fechas ni los montos calculados por Python.

---

## 2. Estado de las Decisiones en el Despliegue

La primera demostración se verificó con el commit `84cc378`. La versión candidata posterior se comprobó con el commit `414bc44`: `/health` informó ese SHA antes y después de 18/18 casos HTTP y de la evaluación pública; la [corrida de CI](https://github.com/CristhianPinos/CalendarioTributarioRIMPE/actions/runs/43366345513) aprobó sus controles. El usuario confirmó la recepción del código y del recordatorio del flujo puntual. El registro de perfiles y el escaneo periódico siguen desactivados en Render Free. La [bitácora](bitacora-semana-4.md) y los informes enlazados conservan los resultados y sus límites.
