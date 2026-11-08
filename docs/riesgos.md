# Matriz de riesgos de la fase 4

**Fecha:** 7 de noviembre de 2026. **Alcance:** API, RAG, agente, despliegue de demostración y futura operación con recordatorios. La clasificación usa [OWASP Top 10 para aplicaciones LLM 2026](https://genai.owasp.org/resource/owasp-genai-llm-top-10-2026/) y [OWASP Top 10 para agentes 2026](https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/). Probabilidad e impacto son estimaciones del equipo, no incidencias observadas.

| Riesgo | Escenario en esta aplicación | Probabilidad / impacto | Controles actuales y prueba | Riesgo residual y acción |
| --- | --- | --- | --- | --- |
| LLM01:2026 Inyección de instrucciones | Una pregunta o fragmento normativo contiene órdenes para alterar fechas o la respuesta. | Media / alta | Fechas calculadas por Python; el RAG recupera documentos y no concede autoridad a la pregunta. Caso F4-16 y pruebas de inyección del agente. | El LLM aún puede redactar mal una explicación. Revisar corpus y respuestas en cada actualización. |
| LLM02:2026 Divulgación de información sensible | RUC, correo o clave aparece en logs, trazas o salida de error. | Media / alta | Middleware anonimiza rutas y mensajes; pruebas de privacidad; `.dockerignore` excluye `.env` y cola histórica. | SQLite conserva datos en claro por necesidad operativa. Para uso real, volumen privado y control de acceso al respaldo. |
| LLM03:2026 Agencia excesiva / ASI02 uso indebido de herramientas | El agente intenta enviar un correo sin consentimiento o aprobación humana. | Media / alta | Operador autenticado, consentimiento vigente, estado `PENDIENTE_CONFIRMACION` y reserva atómica; caso F4-14 y pruebas de autorización. | Un SMTP puede aceptar un correo y perder la respuesta. `ESTADO_INCIERTO` exige revisión manual antes de cualquier reintento. |
| LLM04:2026 Cadena de suministro | Una dependencia maliciosa entra en la imagen o el índice RAG empaquetado se altera. | Baja / alta | Instalación reproducible del frontend con `npm ci`; índice RAG versionado; CI ejecuta pruebas y evaluación. | Dependencias Python usan rangos mínimos. Fijar versiones y hashes tras validar la imagen, y revisar actualizaciones. |
| LLM06:2026 Consumo sin límite | Peticiones repetidas a Gemini o RAG agotan cuota, memoria o capacidad del plan Free. | Alta / media | Tamaño de entrada y `top_k` validados; Tenacity y catálogo de contingencia; Render Free limita recursos. | Falta limitación de peticiones por cliente. Añadir control de tasa y presupuesto antes de aceptar tráfico real. |

## Riesgo operativo fuera de la clasificación LLM

Render Free [pierde el sistema de archivos local](https://render.com/docs/free) cuando suspende, reinicia o redespliega el servicio. Por ello la demostración bloquea el registro de perfiles y mantiene desactivado el planificador. Para recordatorios reales se requiere almacenamiento duradero y verificación de recuperación tras reinicio.

## Criterio de seguimiento

Revisar esta matriz tras cambios de dependencias, modelo Gemini, corpus RAG o plataforma. Una prueba local satisfactoria no demuestra que una URL pública mantenga disponibilidad, ni que el proveedor SMTP entregue el mensaje a la bandeja final.
