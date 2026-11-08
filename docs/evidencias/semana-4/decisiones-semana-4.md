# Decisiones de la semana 4

## Render Free como demostración

El responsable del proyecto eligió Render Free solo para demostración tras revisar que el plan pierde archivos locales al suspenderse o reiniciarse. `RIMPE_DEMO_READONLY=true` bloquea el alta de perfiles y `SCHEDULER_ENABLED=false` evita prometer recordatorios periódicos que no sobrevivirían a un reinicio. [ADR-007](../../09-decisiones.md) conserva la justificación técnica.

## Un origen para frontend y API

La imagen compila React y sirve sus archivos desde FastAPI. Esto evita una segunda plataforma de hosting y permite que el cliente use el mismo origen. El servidor Vite conserva un proxy local hacia el backend para desarrollo.

## Evidencia honesta

Las mediciones locales se publican como **locales**. La URL, capturas y métricas de Render se añadirán únicamente después de una respuesta HTTP pública observada. La prueba de una tarifa hipotética usa un YAML temporal; las reglas oficiales del repositorio permanecen intactas.
