# Declaración de uso de inteligencia artificial

**Proyecto:** Calendario Tributario RIMPE, Caso N.º 11 – Grupo 11  
**Integrantes:** Juan Lucumi (Desarrollador A) y Cristhian Pinos (Desarrollador B)  
**Estado:** documentación del cierre de fase 4; las verificaciones locales y públicas se identifican por separado en los informes de pruebas.

## Uso en la aplicación

- **Gemini** está integrado para redactar explicaciones pedagógicas de obligaciones y, en la ruta de demostración del agente, proponer la siguiente herramienta entre las que Python habilita. El backend valida la selección y limita los pasos. Las fechas, montos y obligaciones provienen del cálculo determinista en Python, no del modelo.
- **RAG** recupera extractos de siete PDF normativos locales mediante BM25 y adjunta citas estructuradas. Una cita presente no demuestra que la fuente responda la pregunta: la [auditoría local](07-evaluacion.md#9-auditoría-local-del-rag-posterior-a-la-revisión-de-fuentes) identificó una consulta de IVA sin la fuente directa entre los tres primeros resultados. Esa consulta se corrigió y la [evaluación pública posterior](07-evaluacion.md#12-verificación-pública-de-la-corrección-preg-02) obtuvo 16/16 en Hit@3 y 5/5 en fuente y artículo dentro de su muestra.
- **Contingencia:** si Gemini no responde, el modal usa el catálogo `fallback-determinista-sri` y muestra su origen. El commit anterior `2444cb3` activó este modo ante 429/503 de Google. Con `b674bfd`, `gemini-3.5-flash-lite` produjo una explicación estructurada y seleccionó herramientas permitidas en Render con datos ficticios. Una respuesta satisfactoria no garantiza disponibilidad futura.
- **Correo:** el envío puntual requiere que la persona confirme la acción y pruebe acceso al correo destinatario mediante un código. El recorrido de herramientas de este envío usa selección segura de Python, aunque la interfaz muestre una bitácora ReAct. SMTP se sustituyó por Mailjet HTTPS para este flujo. La aceptación por Mailjet no demuestra entrega final; el usuario confirmó recepción del código y del recordatorio tanto en pruebas locales como en la demostración pública.

## Uso de IA durante el desarrollo

Se utilizó **Gemini 3.8 Flash hasta la fase 3** del proyecto y **GPT-6 Sol durante la fase 4** como asistencia para analizar documentación, proponer cambios de código y pruebas, revisar inconsistencias y redactar borradores técnicos. Estos modelos asistieron al equipo en el desarrollo; son distintos del modelo Gemini integrado en la aplicación para generar explicaciones. El equipo mantiene la responsabilidad de revisar los cambios, ejecutar las pruebas, verificar las fuentes normativas y decidir qué publicar. El uso de herramientas de IA no se presenta como prueba de exactitud legal ni sustituye la revisión humana de una obligación tributaria.

## Datos, límites y verificación

- La explicación puede contener errores o ser genérica cuando actúa la contingencia. Debe contrastarse con el SRI antes de realizar una declaración.
- El formulario no guarda perfiles en el flujo público actual; el correo se solicita al enviar un recordatorio. Los códigos de verificación se conservan temporalmente en memoria. Los logs aplican anonimización de identificadores en los casos cubiertos por las pruebas.
- La demostración Render Free usa almacenamiento efímero y no ofrece persistencia de perfiles ni cola individual. El planificador histórico de correos personales está desactivado. Un escaneo diario **general**, sin datos personales ni envío automático, se dispara desde GitHub Actions; se verificó una ejecución manual. Render Free y GitHub Actions no garantizan la puntualidad de cada ejecución programada. Las mejoras se atribuyen a la versión pública solo después de desplegar y verificar el commit correspondiente.
- Las claves de Gemini y Mailjet se configuran como secretos de entorno. No deben incluirse en el repositorio, capturas, informes ni paquete de entrega.

**Evidencia:** [arquitectura](03-arquitectura.md), [decisiones](09-decisiones.md), [evaluación](07-evaluacion.md), [riesgos](riesgos.md) y [bitácora de semana 4](evidencias/semana-4/bitacora-semana-4.md).
