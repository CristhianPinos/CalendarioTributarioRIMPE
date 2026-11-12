# Evidencias Técnicas y Decisiones de la Semana 4 (Fase 4)

**Proyecto:** Calendario Tributario Personalizado con Recordatorios para Emprendedores RIMPE

**Fase:** Fase 4 – Preparación para Docker, despliegue y demostración pública (Semana 4)

**Periodo:** Noviembre de 2026 / Fase 4 – Semana 4

**Estado:** Despliegue de demostración verificado; cierre de fase pendiente.

---

## 1. Decisiones Técnicas de la Semana 4

### Render Free como demostración

El responsable del proyecto eligió Render Free solo para demostración tras revisar que el plan pierde archivos locales al suspenderse o reiniciarse. `RIMPE_DEMO_READONLY=true` bloquea el alta de perfiles y `SCHEDULER_ENABLED=false` evita prometer recordatorios periódicos que no sobrevivirían a un reinicio. [ADR-007](../../09-decisiones.md) conserva la justificación técnica.

### Un origen para frontend y API

La imagen compila React y sirve sus archivos desde FastAPI. Esto evita una segunda plataforma de hosting y permite que el cliente use el mismo origen. El servidor Vite conserva un proxy local hacia el backend para desarrollo.

### Evidencia basada en comprobaciones observadas

Las mediciones locales se publican como **locales**. La URL y los resultados de Render se incorporan únicamente después de comprobar la respuesta pública. La prueba de una tarifa hipotética usa un YAML temporal; las reglas oficiales del repositorio permanecen intactas.

### Minimización de datos y rechazo de consultas de evasión

Las decisiones éticas se describen en [ADR-008 a ADR-012](../../09-decisiones.md). El calendario se calcula sin guardar un perfil; el envío puntual requiere un código recibido en el correo elegido y confirmación expresa. El registro administrativo y el escaneo periódico son parte del diseño histórico, sin rutas montadas en la aplicación actual. El RAG se abstiene ante solicitudes de evasión o falta de sustento. Las pruebas cubren casos concretos, sin presentar esos controles como garantías absolutas.

### Selección acotada de herramientas

El agente puede consultar a Gemini para elegir entre herramientas habilitadas por Python. La decisión se valida y se traza; ante fallos se conserva el recorrido seguro. El flujo de correo verificado permanece determinista después de consumir el código temporal. [ADR-012](../../09-decisiones.md) explica la separación y la cuota compartida.

---

## 2. Estado de las Decisiones en el Despliegue

El servicio Free se verificó en estado `Live` con el commit `84cc378`; `/health` confirmó el modo de solo lectura y el planificador deshabilitado. La [bitácora de la semana 4](bitacora-semana-4.md) resume el trabajo, las validaciones y sus límites; las fechas y resultados completos permanecen en los informes enlazados. Esta verificación no implica que la persistencia ni los envíos de recordatorios estén habilitados en la demostración.
