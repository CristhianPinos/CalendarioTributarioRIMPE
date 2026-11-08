# Bitácora de la semana 4

## 7 de noviembre de 2026

| Actividad | Evidencia y resultado |
| --- | --- |
| Lectura de la hoja de ruta y contraste con el código | Se detectó que el plan Free de Render pierde SQLite y que la prueba de tarifa no debe modificar la configuración pública. |
| Empaquetado | Se crearon `Dockerfile`, `.dockerignore`, `compose.yaml` y `render.yaml`. El frontend se sirve desde FastAPI en la imagen. |
| Seguridad de la demostración | Se activó el modo de solo lectura para perfiles y se mantuvo deshabilitado el planificador; no se incluyen secretos, cola JSON ni correo SMTP. |
| Pruebas de backend y frontend | El build de Vite terminó correctamente. Se ejecutaron pruebas de RAG, configuración aislada y persistencia. |
| Pruebas HTTP locales | La batería de 17 casos iniciales pasó contra Uvicorn local. Se añadió la comprobación de la interfaz HTML para el ciclo final. |
| Evaluación local | 10/10 perfiles, 23/23 fechas, Hit@3 16/16, citas 16/16 y F1 de abstención 100 %. El runner HTTP local obtuvo los mismos valores. |
| Docker local | `docker build` no pudo conectarse al motor Docker Desktop de este equipo. El build queda además integrado en CI. |
| Despliegue Render | Se abrió la página de acceso a Render. Pendiente de sesión de la cuenta para crear el servicio y obtener la URL verificable. |

La bitácora registra solo tareas realizadas u obstáculos observados. Las capturas del servicio público se incorporarán después de un despliegue real; no se sustituyen por imágenes simuladas.
