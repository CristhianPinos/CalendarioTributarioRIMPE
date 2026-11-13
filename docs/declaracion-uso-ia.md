# Declaración de uso de inteligencia artificial

**Proyecto:** Calendario Tributario RIMPE, Caso N.º 11 – Grupo 11  
**Integrantes:** Juan Lucumi (Desarrollador A) y Cristhian Pinos (Desarrollador B)  
**Estado:** documentación del código local al 12 de noviembre de 2026; la versión pública de Render puede diferir.

## Uso en la aplicación

- **Gemini** está integrado para redactar explicaciones pedagógicas de obligaciones y, en la ruta de demostración del agente, proponer la siguiente herramienta entre las que Python habilita. El backend valida la selección y limita los pasos. Las fechas, montos y obligaciones provienen del cálculo determinista en Python, no del modelo.
- **RAG** recupera extractos de siete PDF normativos locales mediante BM25 y adjunta citas estructuradas. Una cita presente no demuestra que la fuente responda la pregunta: la [auditoría local](07-evaluacion.md#9-auditoría-local-del-rag-posterior-a-la-revisión-de-fuentes) identificó una consulta de IVA sin la fuente directa entre los tres primeros resultados.
- **Contingencia:** si Gemini no responde, el modal usa el catálogo `fallback-determinista-sri` y muestra su origen. El commit anterior `2444cb3` activó este modo ante 429/503 de Google. Con `b674bfd`, `gemini-3.5-flash-lite` produjo una explicación estructurada y seleccionó herramientas permitidas en Render con datos ficticios. Una respuesta satisfactoria no garantiza disponibilidad futura.
- **Correo:** el envío puntual requiere que la persona confirme la acción y pruebe acceso al correo destinatario mediante un código. El recorrido de herramientas de este envío usa selección segura de Python, aunque la interfaz muestre una bitácora ReAct. La aceptación por Mailjet no demuestra entrega final; el usuario confirmó recepción en pruebas locales.

## Uso de IA durante el desarrollo

Se utilizó asistencia de IA para analizar documentación, proponer cambios de código y pruebas, revisar inconsistencias y redactar borradores técnicos. El equipo mantiene la responsabilidad de revisar los cambios, ejecutar las pruebas, verificar las fuentes normativas y decidir qué publicar. El uso de herramientas de IA no se presenta como prueba de exactitud legal ni sustituye la revisión humana de una obligación tributaria.

## Datos, límites y verificación

- La explicación puede contener errores o ser genérica cuando actúa la contingencia. Debe contrastarse con el SRI antes de realizar una declaración.
- El formulario no guarda perfiles en el flujo público actual; el correo se solicita al enviar un recordatorio. Los códigos de verificación se conservan temporalmente en memoria. Los logs aplican anonimización de identificadores en los casos cubiertos por las pruebas.
- La demostración Render Free usa almacenamiento efímero. No ofrece escaneo periódico fiable ni persistencia de perfiles o cola. Las mejoras locales no se atribuyen a la versión pública anterior hasta desplegar y verificar un nuevo commit.
- Las claves de Gemini y Mailjet se configuran como secretos de entorno. No deben incluirse en el repositorio, capturas, informes ni paquete de entrega.

**Evidencia:** [arquitectura](03-arquitectura.md), [decisiones](09-decisiones.md), [evaluación](07-evaluacion.md), [riesgos](riesgos.md) y [bitácora de semana 4](evidencias/semana-4/bitacora-semana-4.md).
