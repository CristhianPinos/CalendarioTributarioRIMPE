# Bitácora Técnica de Trabajo - Semana 4 (Fase 4)

**Proyecto:** Calendario Tributario Personalizado con Recordatorios para Emprendedores RIMPE

**Fase:** Preparación, despliegue y validación del producto

**Periodo:** Noviembre de 2026
**Estado:** Demostración pública y CI de la versión candidata verificados.

---

## 1. Trabajo principal de la fase

### Contenedor y demostración pública

- Se preparó una imagen Docker multietapa que compila React, instala el backend y ejecuta FastAPI sin privilegios. `render.yaml` configura el servicio Free y la comprobación `/health`.
- Render Free se usa solo como **demostración**, debido a su almacenamiento efímero. La versión candidata pública corresponde al commit `414bc44`, informa `3.3.0` y mantiene desactivados el registro de perfiles y el escaneo periódico. No demuestra persistencia de recordatorios.
- El [README](../../../README.md) incorpora la URL pública, instrucciones de ejecución, resultados y límites.

### Pruebas, evaluación y protección de datos

- La [primera batería funcional](../../08-pruebas.md) contra Render terminó con **18/18 casos aprobados**, incluida una inyección de prompt. La [evaluación histórica](../../07-evaluacion.md#8-comparación-de-la-semana-4) conservó 10/10 perfiles, 23/23 fechas, Hit@3 16/16, citas 16/16 y F1 de abstención del 100 % en el conjunto usado. Esas cifras corresponden al commit `84cc378`; la evaluación de la versión candidata figura más adelante.
- Se comprobaron el build de Render, `/health`, la interfaz y una [corrida verde de CI](https://github.com/CristhianPinos/CalendarioTributarioRIMPE/actions/runs/42435193745). Las claves se configuran fuera de la imagen y del repositorio. Las decisiones sobre almacenamiento y minimización de datos constan en [ADR](../../09-decisiones.md) y [riesgos](../../riesgos.md).
- Una llamada real de explicación en la demo terminó en el catálogo determinista tras errores del proveedor. La presencia de la clave no demuestra que Gemini genere explicaciones en vivo.

### Mejoras posteriores a la primera demostración

- Se sustituyó el registro de perfiles con operador por un flujo puntual: el contribuyente genera el calendario sin guardar el perfil y, si solicita un recordatorio, verifica el correo mediante un código y confirma el envío. El transporte usa Mailjet por HTTPS. El usuario confirmó la recepción local del código y del recordatorio. Las rutas administrativas de perfiles y cola y el planificador no se montan en la aplicación actual.
- El formulario pide los datos manualmente y deja el correo para el modal. Hay [15 perfiles ficticios](../../datos-prueba-perfiles.md) para pruebas. El calendario aparece después del cálculo, con un resumen del perfil de la sesión. También se mejoraron la legibilidad de los eventos y la validación del simulador.
- El modal muestra la explicación de Gemini cuando está disponible y etiqueta la contingencia cuando no lo está. Se añadieron los comprobantes pertinentes y se limitó la opción de declaración en cero al IVA semestral. El correo usa la obligación y fecha calculadas por Python, y escapa el texto variable antes de incorporarlo al HTML. La interfaz incluye un aviso sobre el apoyo de IA y enlaces normativos revisados.
- Al cotejar la renta de Emprendedor persona natural con el art. 8 de la [resolución SRI NAC-DGERCGC24-00000027](https://www.sri.gob.ec/o/sri-portlet-biblioteca-alfresco-internet/descargar?id=7c3fb8dc-31a6-4fe3-a6c0-abe1def2c78a&nombre=NAC-DGERCGC24-00000027.pdf), se corrigió su mes a mayo en el cálculo y la configuración. La corrección quedó incorporada al despliegue posterior.
- Se añadió una cuota en memoria a la ruta que llama a Gemini, con límites por IP e instancia y respuesta `429` con `Retry-After`. La entrada variable y los tokens de salida se acotaron. El calendario, el RAG local y el simulador no consumen esta cuota. La protección se incorporó al despliegue posterior.
- El agente de demostración ahora admite selección de herramientas por Gemini entre acciones autorizadas por Python, con máximo de pasos, trazas de origen y retorno al flujo seguro ante fallos. El envío verificado conserva su secuencia determinista y su compuerta humana; la selección generativa no decide destinatarios, cálculos ni despachos.
- Se auditó el índice RAG y se corrigió la atribución de considerandos y disposiciones en las resoluciones. La evaluación local distingue cita formal de fuente pertinente: 15/16 artículos y 4/5 pares documento–artículo en la muestra curada. Se documentó una consulta de IVA cuyo artículo directo no aparece en el top 3; las métricas históricas de la demo no describen este estado local.
- Se incorporaron la [declaración de uso de IA](../../declaracion-uso-ia.md) y el [seguimiento de la revisión escrita](observaciones-revision.md). Las evidencias distinguen los fallos iniciales de Gemini y la respuesta real obtenida después con Flash Lite. Las observaciones orales quedan pendientes de las notas del equipo.
- Se preparó la [presentación de sustentación](../../sustentacion-grupo11.pdf) con la plantilla de UNIANDES proporcionada por el equipo y un [guion de 12 minutos](../../guion-sustentacion.md). El PDF se revisó visualmente antes de incorporarlo; aún no se ha entregado.
- Tras comprobar que el modelo anterior devolvía contingencia por 429/503, se probó y publicó `gemini-3.5-flash-lite`. Respondió en casos locales de IVA, declaración en cero y renta; en Render generó una explicación real y seleccionó tres herramientas permitidas sin autorizar el envío. Python fija la fecha textual. La batería HTTP pública aprobó 18/18 casos. El usuario completó el flujo del modal con un código nuevo y confirmó la recepción del recordatorio en Gmail.
- Se añadió detección de secretos al flujo de CI. Una prueba antigua que esperaba otra referencia legal bloqueó la primera corrida y se corrigió sin alterar el catálogo tributario. La [corrida verde](https://github.com/CristhianPinos/CalendarioTributarioRIMPE/actions/runs/43366345513) aprobó 235 pruebas, evaluación, frontend e imagen Docker. `/health` identificó el mismo commit antes y después de las pruebas públicas: 18/18 casos HTTP, 10/10 perfiles, 23/23 fechas, Hit@3 de 15/16 y abstención TP/TN/FP/FN de 4/16/0/0.

---

## 2. Línea base para el cierre

| Ámbito | Evidencia comprobada | Límite |
| --- | --- | --- |
| Demo Render | `/health` informó el commit `414bc44`; 18/18 casos HTTP y la evaluación actual aprobaron sobre ese despliegue | La evaluación comparada histórica corresponde al commit `84cc378`. La disponibilidad futura de Gemini no está garantizada. |
| Backend y CI | Versión `3.3.0`; 235 pruebas de backend aprobaron en CI con Python 3.12 | La suite completa local se bloqueó con `TestClient` en Python 3.14; no se presenta como aprobada en ese entorno. |
| Frontend local | `npm run build` aprobó; `npm run lint` terminó sin errores | El linter mantiene advertencias en calendario y modal. Falta una inspección visual de la versión final. |
| Integración externa | Flash Lite respondió en Render; el usuario recibió en Gmail un código solicitado desde el modal y el recordatorio posterior | Mailjet confirmó aceptación; la entrega final se conoce por la confirmación del destinatario, no por un acuse técnico del proveedor. |

Los resultados detallados permanecen en [pruebas](../../08-pruebas.md) y [evaluación](../../07-evaluacion.md). Esta bitácora recoge las conclusiones principales de la fase.

## 3. Pendientes para completar la entrega

- Si el servicio pasa a varias instancias, mover los contadores de cuota a un almacén compartido. La implementación actual es deliberadamente local al proceso único y se reinicia al arrancar.
- Revisar periódicamente la cuota y disponibilidad de Gemini; la contingencia determinista sigue siendo necesaria ante fallos del proveedor.
- Revisar visualmente la versión candidata antes de la entrega; la batería HTTP y la evaluación ya se repitieron contra el commit identificado en Render.
- Incorporar las observaciones orales de la sustentación cuando el equipo aporte sus notas. El usuario preparará el paquete final sin secretos ni datos personales y realizará la entrega.
