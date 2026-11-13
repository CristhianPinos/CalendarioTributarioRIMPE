# Bitácora Técnica de Trabajo - Semana 4 (Fase 4)

**Proyecto:** Calendario Tributario Personalizado con Recordatorios para Emprendedores RIMPE

**Fase:** Preparación, despliegue y validación del producto

**Periodo:** Noviembre de 2026
**Estado:** Demostración pública verificada; mejoras posteriores locales, aún sin publicar.

---

## 1. Trabajo principal de la fase

### Contenedor y demostración pública

- Se preparó una imagen Docker multietapa que compila React, instala el backend y ejecuta FastAPI sin privilegios. `render.yaml` configura el servicio Free y la comprobación `/health`.
- Render Free se usa solo como **demostración**, debido a su almacenamiento efímero. La versión pública comprobada corresponde al commit `84cc378`, informa `3.2.0` y mantiene desactivados el registro de perfiles y el escaneo periódico. No demuestra persistencia de recordatorios ni envío de correo.
- El [README](../../../README.md) local incorpora la URL pública, instrucciones de ejecución, resultados y límites. Su versión publicada en GitHub sigue siendo anterior a estas mejoras.

### Pruebas, evaluación y protección de datos

- La [batería funcional](../../08-pruebas.md) contra Render terminó con **18/18 casos aprobados**, incluida una inyección de prompt. La [evaluación comparada](../../07-evaluacion.md#8-comparación-de-la-semana-4) conservó 10/10 perfiles, 23/23 fechas, Hit@3 16/16, citas 16/16 y F1 de abstención del 100 % en el conjunto usado. Las cifras corresponden al commit desplegado, no a las mejoras locales posteriores.
- Se comprobaron el build de Render, `/health`, la interfaz y una [corrida verde de CI](https://github.com/CristhianPinos/CalendarioTributarioRIMPE/actions/runs/42435193745). Las claves se configuran fuera de la imagen y del repositorio. Las decisiones sobre almacenamiento y minimización de datos constan en [ADR](../../09-decisiones.md) y [riesgos](../../riesgos.md).
- Una llamada real de explicación en la demo terminó en el catálogo determinista tras errores del proveedor. La presencia de la clave no demuestra que Gemini genere explicaciones en vivo.

### Mejoras realizadas localmente

- Se sustituyó el registro de perfiles con operador por un flujo puntual: el contribuyente genera el calendario sin guardar el perfil y, si solicita un recordatorio, verifica el correo mediante un código y confirma el envío. El transporte usa Mailjet por HTTPS. El usuario confirmó la recepción local del código y del recordatorio. Las rutas administrativas de perfiles y cola y el planificador no se montan en la aplicación actual.
- El formulario pide los datos manualmente y deja el correo para el modal. Hay [15 perfiles ficticios](../../datos-prueba-perfiles.md) para pruebas. El calendario aparece después del cálculo, con un resumen del perfil de la sesión. También se mejoraron la legibilidad de los eventos y la validación del simulador.
- El modal muestra la explicación de Gemini cuando está disponible y etiqueta la contingencia cuando no lo está. Se añadieron los comprobantes pertinentes y se limitó la opción de declaración en cero al IVA semestral. El correo usa la obligación y fecha calculadas por Python, y escapa el texto variable antes de incorporarlo al HTML. La interfaz incluye un aviso sobre el apoyo de IA y enlaces normativos revisados.
- Al cotejar la renta de Emprendedor persona natural con el art. 8 de la [resolución SRI NAC-DGERCGC24-00000027](https://www.sri.gob.ec/o/sri-portlet-biblioteca-alfresco-internet/descargar?id=7c3fb8dc-31a6-4fe3-a6c0-abe1def2c78a&nombre=NAC-DGERCGC24-00000027.pdf), se corrigió su mes a mayo en el cálculo y la configuración locales. La demo pública todavía usa el commit anterior.
- Se añadió una cuota en memoria a la ruta que llama a Gemini, con límites por IP e instancia y respuesta `429` con `Retry-After`. La entrada variable y los tokens de salida se acotaron. El calendario, el RAG local y el simulador no consumen esta cuota. La protección se ha probado localmente; aún no se ha publicado.
- El agente de demostración ahora admite selección de herramientas por Gemini entre acciones autorizadas por Python, con máximo de pasos, trazas de origen y retorno al flujo seguro ante fallos. El envío verificado conserva su secuencia determinista y su compuerta humana; la selección generativa no decide destinatarios, cálculos ni despachos.
- Se auditó el índice RAG y se corrigió la atribución de considerandos y disposiciones en las resoluciones. La evaluación local distingue cita formal de fuente pertinente: 15/16 artículos y 4/5 pares documento–artículo en la muestra curada. Se documentó una consulta de IVA cuyo artículo directo no aparece en el top 3; las métricas históricas de la demo no describen este estado local.
- Se incorporaron la [declaración de uso de IA](../../declaracion-uso-ia.md) y el [seguimiento de la revisión escrita](observaciones-revision.md). Las evidencias diferencian el despliegue anterior de los cambios locales y registran que Gemini sigue mostrando contingencia en la prueba manual. Las observaciones orales quedan pendientes de las notas del equipo.
- Se preparó la [presentación de sustentación](../../sustentacion-grupo11.pdf) con la plantilla de UNIANDES proporcionada por el equipo y un [guion de 12 minutos](../../guion-sustentacion.md). El PDF se revisó visualmente antes de incorporarlo; aún no se ha entregado.
- Tras publicar `2444cb3`, se comprobó `/health` con versión `3.3.0` y la aceptación de un código de prueba por Mailjet en Render. Las explicaciones públicas seguían en contingencia: los logs mostraron 429/503 de Gemini. Se probó localmente `gemini-3.5-flash-lite` con explicaciones de IVA, declaración en cero y renta, además de una selección de herramienta; respondió en los casos ensayados. El modelo predeterminado se cambió localmente y la fecha textual quedó fijada por Python.

---

## 2. Línea base para el cierre

| Ámbito | Evidencia comprobada | Límite |
| --- | --- | --- |
| Demo Render | El commit `2444cb3` informó `/health` HTTP 200, versión `3.3.0`; Mailjet aceptó la solicitud de un código de prueba | El resultado de 18/18 pruebas HTTP y la evaluación comparada corresponden al commit anterior `84cc378`. La aceptación del código no prueba recepción ni el envío completo en esta versión. |
| Backend local | Versión `3.3.0`; 212 pruebas recolectadas y 116 pruebas unitarias y directas aprobadas en esta comprobación | La suite completa se detuvo al comenzar una prueba HTTP con `TestClient` en Python 3.14; no se considera aprobada. |
| Frontend local | `npm run build` aprobó; `npm run lint` terminó sin errores | El linter mantiene advertencias en calendario y modal. Falta una inspección visual de la versión final. |
| Integración externa | Recepción local del código y recordatorio confirmada por el usuario; Flash Lite generó explicaciones y selección en pruebas locales; Render aceptó una solicitud de código | Falta confirmar recepción del código público y verificar Flash Lite después de publicar el cambio de modelo. |

Los resultados detallados permanecen en [pruebas](../../08-pruebas.md) y [evaluación](../../07-evaluacion.md). Esta bitácora recoge las conclusiones principales de la fase.

## 3. Pendientes para completar la entrega

- Si el servicio pasa a varias instancias, mover los contadores de cuota a un almacén compartido. La implementación actual es deliberadamente local al proceso único y se reinicia al arrancar.
- Verificar en Render la selección y la explicación con Flash Lite después de publicar el cambio local. Las pruebas reales locales usaron datos ficticios y no autorizaron correos.
- Repetir pruebas, evaluación y revisión visual sobre la versión candidata y, tras una publicación autorizada, contra esa misma versión en Render. Actualizar README y evidencias con el commit verificado.
- Incorporar las observaciones orales de la sustentación cuando el equipo aporte sus notas. El usuario preparará el paquete final sin secretos ni datos personales y realizará la entrega.
