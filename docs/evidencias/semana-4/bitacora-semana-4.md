# Bitácora Técnica de Trabajo - Semana 4 (Fase 4)

- **Proyecto:** Calendario Tributario Personalizado con Recordatorios para Emprendedores RIMPE (Caso 11 - Grupo 11)
- **Fase:** Despliegue, validación y cierre documental
- **Integrantes:** Juan Lucumi (Desarrollador A) y Cristhian Pinos (Desarrollador B)
- **Rama de trabajo:** `main`
- **Periodo:** Noviembre de 2026 / Fase 4 – Semana 4
- **Estado:** Demostración pública y CI verificados; entrega formal a cargo del equipo.

---

## 1. Registro de tareas ejecutadas

### Paso 1: Contenedor y demostración pública

- Se preparó una imagen Docker multietapa que compila React y sirve frontend y API desde FastAPI con un usuario sin privilegios. `render.yaml` configura la comprobación `/health` y el despliegue automático después de aprobar CI.
- Render Free se eligió para **demostración** por su almacenamiento efímero. El calendario funciona sin guardar perfiles; el registro administrativo y el escaneo periódico permanecen desactivados. Esta configuración no promete persistencia de recordatorios.
- El [README](../../../README.md) reúne la URL, las instrucciones de ejecución, las pruebas y los límites de la demo. La justificación del alcance está en [decisiones-semana-4.md](decisiones-semana-4.md) y [ADR-007](../../09-decisiones.md).

### Paso 2: Flujo del contribuyente y recordatorio puntual

- Se retiraron los perfiles de carga rápida y la exigencia de operador. El usuario introduce manualmente los datos del contribuyente, genera el calendario y ve un resumen del perfil de la sesión. Los [15 perfiles ficticios](../../datos-prueba-perfiles.md) sirven para pruebas sin almacenar correos.
- Se mejoraron la lectura de eventos del calendario y los mensajes del simulador de renta. El modal deja el correo para el momento del envío, muestra los comprobantes pertinentes y ofrece declaración en cero solo para IVA semestral.
- El despacho puntual exige un código enviado al correo elegido y confirmación expresa. Mailjet usa HTTPS; Python determina la obligación y la fecha y escapa el texto variable del HTML. El usuario confirmó la recepción del código y del recordatorio desde el modal público. La aceptación de Mailjet y la recepción confirmada por el destinatario son evidencias distintas.

### Paso 3: IA, agente y fuentes normativas

- Se limitó el consumo de Gemini por cliente e instancia y se acotaron las entradas y los tokens de salida. El agente de demostración permite a Gemini elegir entre herramientas autorizadas por Python, con trazas y máximo de pasos; el envío verificado mantiene una secuencia segura y la compuerta humana.
- Los errores 429/503 del modelo anterior activaron el catálogo de contingencia. Tras probar `gemini-3.5-flash-lite`, la demo produjo una explicación real y el agente seleccionó tres herramientas permitidas en una ejecución sintética sin autorización de envío. Python conserva el control de las fechas, incluso del texto de fecha que devuelve el modelo.
- Se corrigió a mayo el vencimiento de renta para Emprendedor persona natural después de cotejar el art. 8 de la [resolución SRI NAC-DGERCGC24-00000027](https://www.sri.gob.ec/o/sri-portlet-biblioteca-alfresco-internet/descargar?id=7c3fb8dc-31a6-4fe3-a6c0-abe1def2c78a&nombre=NAC-DGERCGC24-00000027.pdf). La revisión del índice RAG mejoró la atribución de considerandos y disposiciones. Posteriormente se corrigió la recuperación de la fuente directa para la consulta sobre IVA de Negocio Popular, verificada también en Render.

### Paso 4: Verificación y documentación de la entrega

- CI incorpora detección de secretos, pruebas de backend, evaluación, compilación React y construcción Docker. Una prueba que esperaba una referencia legal antigua impidió la primera corrida verde; se actualizó la prueba sin cambiar el catálogo tributario.
- El endpoint `/health` identifica el commit servido por Render. El commit inicial `414bc44` y la versión corregida `37d3c07` cuentan con [corridas de CI](https://github.com/CristhianPinos/CalendarioTributarioRIMPE/actions/runs/43518880462) y pruebas públicas diferenciadas. Los resultados detallados están en [pruebas](../../08-pruebas.md) y [evaluación](../../07-evaluacion.md#12-verificación-pública-de-la-corrección-preg-02).
- Se revisó visualmente la versión local y luego la pública en móvil, tableta y escritorio con un perfil ficticio. Se ajustaron la cabecera y los pasos del formulario en pantallas estrechas, y se hizo desplazable el calendario para conservar la lectura del vencimiento completo. La comprobación pública adicional a 320 px detectó un leve desbordamiento y proximidad entre el formulario y el botón de cierre del modal; se corrigieron y verificaron tras el despliegue.
- Se incorporaron la [declaración de uso de IA](../../declaracion-uso-ia.md), la [matriz de riesgos](../../riesgos.md) y la [presentación PDF](../../sustentacion-grupo11.pdf). La entrega del archivo final sigue a cargo del equipo.

---

## 2. Observaciones de la revisión y respuesta del proyecto

La fuente de esta sección es «Progreso del Proyecto Grupo 11.pdf», entregado por el equipo. El usuario confirmó que los comentarios recibidos en la revisión coinciden en lo esencial con ese informe; no hay una lista oral adicional que documentar. La revisión examinó el repositorio del 7 de noviembre y su diagnóstico corresponde a esa versión, no al código posterior. La tabla registra cada observación y la mejora aplicada, con su límite comprobable.

| Observación escrita | Acción realizada y decisión relacionada | Evidencia y estado |
| --- | --- | --- |
| Faltaba URL pública, `/health` y una batería en Render. | Se publicó la demo Free y se delimitó su uso a consultas sin perfiles persistidos. Véanse [decisiones de despliegue](decisiones-semana-4.md#render-free-como-demostración) y [ADR-007](../../09-decisiones.md). | `/health` identificó `414bc44`; [18/18 casos HTTP](../../08-pruebas.md#verificación-de-la-versión-candidata) y [evaluación pública](../../07-evaluacion.md#10-evaluación-de-la-versión-candidata-en-render) sobre ese commit. |
| Pipeline CI/CD, documentación de instalación y pruebas públicas estaban a medias. | Se configuró el despliegue tras CI aprobado, se añadió detección de secretos y se actualizó el README con ejecución local, Docker, Render y reproducción de pruebas. | [CI aprobado](https://github.com/CristhianPinos/CalendarioTributarioRIMPE/actions/runs/43366345513); 18/18 casos HTTP en Render. La disponibilidad sostenida no se infiere de una corrida. |
| El agente seguía un orden fijo; Gemini no elegía herramientas. | Se añadió una selección acotada a herramientas permitidas por Python, con retorno al flujo seguro. El envío con código conserva la selección determinista. Véanse [decisión de la semana](decisiones-semana-4.md#selección-acotada-de-herramientas) y [ADR-012](../../09-decisiones.md). | En Render, tres herramientas registraron origen `gemini` con datos sintéticos; el envío quedó pendiente de confirmación. |
| No había límite de tasa real en las rutas de IA. | Se implantaron límites por cliente e instancia, respuesta `429` con `Retry-After` y límites de entrada y salida. | Las [pruebas de cuota](../../../backend/tests/test_explanation_rate_limit.py) aprobaron en CI; los contadores siguen siendo locales al proceso. |
| El texto variable del correo no se escapaba al generar HTML. | Se aplicó escape de HTML y se mantuvo la verificación del destinatario y la confirmación humana. Véase [decisión de minimización](decisiones-semana-4.md#minimización-de-datos-y-rechazo-de-consultas-de-evasión). | Las [pruebas de correo](../../../backend/tests/test_correo_verificado.py) aprobaron en CI; el usuario confirmó la recepción pública del recordatorio. |
| El envío se había protegido con operador y estados SMTP, pero ese flujo dificultaba el uso público y SMTP no funcionó desde Render Free. | Se retiraron las credenciales de operador del flujo activo y el registro de perfiles; se sustituyó SMTP **solo en el envío puntual** por Mailjet HTTPS. El código al destinatario y la confirmación expresa conservan la compuerta humana. El transporte SMTP y SQLite permanecen como implementación histórica sin rutas públicas. Véanse [ADR-010 y ADR-011](../../09-decisiones.md). | El usuario recibió el código y el recordatorio desde Render; la respuesta `ENVIADO` por sí sola acredita aceptación del proveedor, no entrega. No se comprobó persistencia tras reinicio. |
| El índice RAG, las citas y el conjunto de evaluación requerían mayor precisión. | Se documentó la recuperación por artículo, se separó presencia de cita de pertinencia jurídica y se añadieron controles de abstención y de fuente y artículo. La consulta PREG-02 se corrigió después de la primera evaluación pública. | [Evaluación pública anterior](../../07-evaluacion.md#10-evaluación-de-la-versión-candidata-en-render): 15/16 Hit@3 y 4/5 fuente y artículo; [nueva evaluación en Render](../../07-evaluacion.md#12-verificación-pública-de-la-corrección-preg-02): 16/16 y 5/5 sobre `37d3c07`. |
| Faltaban declaración de IA, respuesta a observaciones y presentación. | Se incorporaron la declaración, esta respuesta a la revisión y el PDF de sustentación. | Material preparado en `docs/`; la entrega formal del paquete corresponde al equipo. |

---

## 3. Resumen de validaciones de la semana

| Ámbito | Resultado verificado | Límite de la evidencia |
| --- | --- | --- |
| Primera demostración (`84cc378`) | 18/18 casos HTTP; evaluación histórica de 10/10 perfiles, 23/23 fechas y Hit@3 de 16/16 | Usa el evaluador y el corpus de aquel commit; no describe el estado actual del RAG. |
| Versión candidata (`414bc44`) | CI verde: 235 pruebas de backend, evaluación local, escaneo de secretos, compilación React e imagen Docker. Render: 18/18 casos HTTP y `/health` con el mismo SHA. | La suite completa local con Python 3.14 se bloqueó en `TestClient`; el resultado completo corresponde a CI con Python 3.12. |
| Evaluación anterior en Render | 10/10 perfiles, 23/23 fechas, Hit@3 de 15/16, citas coherentes 16/16, fuente y artículo 4/5; abstención TP/TN/FP/FN de 4/16/0/0 | Una cita formal no garantiza pertinencia jurídica. PREG-02 no recuperaba entonces la fuente directa entre las tres primeras. |
| Versión corregida (`37d3c07`) | [CI aprobado](https://github.com/CristhianPinos/CalendarioTributarioRIMPE/actions/runs/43518880462), `/health` con el mismo SHA, 18/18 casos HTTP; Hit@3 de 16/16 y fuente y artículo 5/5 en [Render](../../07-evaluacion.md#12-verificación-pública-de-la-corrección-preg-02). | La muestra curada y las pruebas sintéticas no constituyen una auditoría jurídica completa. |
| Revisión visual pública | Se comprobó el perfil, el calendario, el desplazamiento horizontal del vencimiento y su modal en escritorio, tableta y móviles de 390 y 320 px. El ajuste `30fab35` pasó [CI](https://github.com/CristhianPinos/CalendarioTributarioRIMPE/actions/runs/43521418406) y `/health` identificó ese SHA en Render. | La revisión cubre esos tamaños y un perfil ficticio; no equivale a probar todos los dispositivos ni proveedores de correo. |
| Integraciones externas | Flash Lite produjo una explicación real en Render; el usuario recibió el código y el recordatorio en Gmail. | La disponibilidad futura de Gemini y la entrega futura de Mailjet no quedan garantizadas por una prueba puntual. |

La [evaluación detallada](../../07-evaluacion.md) conserva por separado las mediciones históricas y el [resultado JSON de la versión corregida](../../../eval/resultados_37d3c07_render.json). El despliegue `37d3c07` sustituyó a `414bc44` tras aprobar CI; ambos tienen evidencias vinculadas a su propio SHA.
