# Seguimiento de observaciones de la revisión

**Proyecto:** Calendario Tributario RIMPE, Caso N.º 11 – Grupo 11  
**Integrantes:** Juan Lucumi (Desarrollador A) y Cristhian Pinos (Desarrollador B)  
**Fuente:** informe «Progreso del Proyecto Grupo 11.pdf» proporcionado por el equipo, revisión estática del repositorio del 7 de noviembre de 2026.  
**Corte de este seguimiento:** 12 de noviembre de 2026 en Ecuador. Las pruebas públicas posteriores identificaron el commit `414bc44`; las cifras históricas del commit `84cc378` se mantienen diferenciadas.

El informe solicita registrar las observaciones del tribunal de la sustentación oral. Ese detalle no figura en el PDF recibido. La tabla siguiente responde únicamente a las observaciones **escritas** comprobables; se completará la parte oral cuando el equipo aporte sus notas. No se atribuyen al tribunal comentarios inventados.

| Observación escrita | Acción y evidencia | Estado verificable |
| --- | --- | --- |
| Faltaba URL pública, `/health` y prueba contra Render. | La [demostración](https://calendario-rimpe-g11-demo.onrender.com/) se publicó después de la revisión; [README](../../../README.md), [pruebas HTTP](../../08-pruebas.md) y [evaluación actual](../../07-evaluacion.md#10-evaluación-de-la-versión-candidata-en-render) registran la comprobación. | **URL y pruebas verificadas en Render** con `/health` identificando `414bc44`; 18/18 casos HTTP y evaluación sobre ese commit. |
| El agente seguía un orden fijo; Gemini no elegía la herramienta. | [ADR-012](../../09-decisiones.md#adr-012-selección-acotada-de-herramientas-por-gemini), `backend/services/agent_planner.py` y `backend/tests/test_agent_planner.py` describen y prueban selección acotada. | **Implementada y probada con Gemini real en local y en Render** con datos sintéticos. Las tres herramientas de la ejecución pública registraron origen `gemini`; el despacho permaneció pendiente de confirmación. El flujo de correo verificado conserva selección determinista por seguridad. |
| No había límite de tasa real para rutas que llaman al modelo. | `backend/services/rate_limit.py`, pruebas de cuota y [matriz de riesgos](../../riesgos.md) documentan `429` y `Retry-After`. | **Implementada y publicada.** Los contadores son por proceso y se reinician; la suite aprobó en CI. |
| El texto variable del recordatorio entraba sin escape al HTML del correo. | `backend/services/agent_service.py` usa escape de HTML; las pruebas de correo comprueban el contenido. | **Corregida y publicada.** El usuario confirmó recepción de código y recordatorio desde el modal público. |
| Faltaban declaración de IA, observaciones y presentación PDF. | [Declaración de uso de IA](../../declaracion-uso-ia.md), este seguimiento y [presentación](../../sustentacion-grupo11.pdf) con [guion de 12 minutos](../../guion-sustentacion.md). | **Documentación y PDF incluidos en el repositorio.** Las observaciones orales esperan las notas del equipo; la entrega formal sigue a cargo del equipo. |

## Pendientes para cerrar la evidencia

1. Incorporar las observaciones concretas del tribunal de la sustentación oral, indicando para cada una la acción, la evidencia y si sigue pendiente.
2. Seguir observando la disponibilidad de Gemini. Flash Lite respondió en Render con datos sintéticos; el modelo anterior había devuelto `fallback-determinista-sri` por HTTP 429/503. La contingencia continúa siendo necesaria.
3. Mantener las pruebas ligadas al SHA publicado en nuevas entregas; la verificación actual de `414bc44` no garantiza futuros despliegues.
4. El usuario preparará y subirá el ZIP de entrega. Excluir secretos, entornos y datos personales. El PDF ya está listo en `docs/`; no se afirma una entrega realizada.
