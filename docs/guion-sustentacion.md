# Guion breve de sustentación (12 minutos)

**Presentación:** [sustentacion-grupo11.pdf](sustentacion-grupo11.pdf)  
**Expositores:** Cristhian Pinos y Juan Lucumi  
**Duración total prevista:** 12 minutos, incluida una demostración local de dos minutos.

| Diapositiva | Tiempo | Idea que debe explicarse |
| --- | ---: | --- |
| 1. Portada | 0:30 | Presentar el caso y a ambos integrantes. |
| 2. Problema y objetivo | 1:10 | Explicar por qué la fecha cambia con régimen, RUC y días inhábiles. |
| 3. Recorrido | 1:15 | Mostrar que el calendario nace tras completar el perfil y que el correo se introduce después. |
| 4. Arquitectura | 1:20 | Separar interfaz, API, cálculo Python, RAG, Gemini y Mailjet. |
| 5. Seguridad | 1:15 | Explicar código temporal, confirmación humana y límites del agente. |
| 6. IA y RAG | 1:15 | Distinguir explicación de cálculo y cita formal de fuente pertinente. |
| 7. Pruebas | 1:10 | Citar cifras locales y públicas con sus versiones y muestras respectivas. |
| 8. Demostración | 2:00 | En local: introducir un perfil ficticio, abrir un vencimiento y mostrar la compuerta de correo con un buzón de prueba. No mostrar códigos ni secretos en pantalla compartida. |
| 9. Límites | 1:10 | Indicar contingencia de Gemini, hallazgo RAG y almacenamiento efímero de Render Free. |
| 10. Equipo | 0:45 | Describir los aportes verificables de cada integrante. |
| 11. Cierre | 0:10 | Concluir y abrir preguntas. |

La demostración pública consultada usa el commit `2444cb3` y la versión `3.3.0`. Mailjet aceptó una solicitud de código de prueba en ese despliegue, pero aún no hay confirmación de recepción ni del envío posterior para esa sesión. Las explicaciones públicas comprobadas mostraron `fallback-determinista-sri` por respuestas 429/503 de Gemini. La mejora a Flash Lite generó explicaciones y una selección de herramienta solo en pruebas locales; no atribuir esos resultados a Render hasta verificar un nuevo despliegue.
