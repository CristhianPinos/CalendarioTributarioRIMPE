# Seguimiento de observaciones de la revisión

**Proyecto:** Calendario Tributario RIMPE, Caso N.º 11 – Grupo 11  
**Integrantes:** Juan Lucumi (Desarrollador A) y Cristhian Pinos (Desarrollador B)  
**Fuente:** informe «Progreso del Proyecto Grupo 11.pdf» proporcionado por el equipo, revisión estática del repositorio del 7 de noviembre de 2026.  
**Corte de este seguimiento:** 12 de noviembre de 2026. Los cambios posteriores al commit público `84cc378` permanecen locales y no se presentan como publicados.

El informe solicita registrar las observaciones del tribunal de la sustentación oral. Ese detalle no figura en el PDF recibido. La tabla siguiente responde únicamente a las observaciones **escritas** comprobables; se completará la parte oral cuando el equipo aporte sus notas. No se atribuyen al tribunal comentarios inventados.

| Observación escrita | Acción y evidencia | Estado verificable |
| --- | --- | --- |
| Faltaba URL pública, `/health` y prueba contra Render. | La [demostración](https://calendario-rimpe-g11-demo.onrender.com/) se publicó después de la revisión; [README local](../../../README.md), [pruebas HTTP](../../08-pruebas.md) y [evaluación comparada](../../07-evaluacion.md#8-comparación-de-la-semana-4) registran la comprobación. | **URL y pruebas verificadas en Render** con el commit `84cc378`. La actualización del README sigue local y no se atribuye al repositorio publicado. Las mejoras posteriores requieren otro despliegue autorizado. |
| El agente seguía un orden fijo; Gemini no elegía la herramienta. | [ADR-012](../../09-decisiones.md#adr-012-selección-acotada-de-herramientas-por-gemini), `backend/services/agent_planner.py` y `backend/tests/test_agent_planner.py` describen y prueban selección acotada. | **Implementada y probada con Gemini real en local**, con una herramienta permitida y datos sintéticos. Falta repetir la verificación en Render tras publicar el nuevo modelo. El flujo de correo verificado conserva selección determinista por seguridad. |
| No había límite de tasa real para rutas que llaman al modelo. | `backend/services/rate_limit.py`, pruebas de cuota y [matriz de riesgos](../../riesgos.md) documentan `429` y `Retry-After`. | **Implementada localmente.** Los contadores son por proceso y se reinician; no está verificada en la demo pública anterior. |
| El texto variable del recordatorio entraba sin escape al HTML del correo. | `backend/services/agent_service.py` usa escape de HTML; las pruebas de correo comprueban el contenido. | **Corregida localmente.** El equipo confirmó recepción de código y recordatorio en pruebas locales; requiere nueva verificación tras publicación. |
| Faltaban declaración de IA, observaciones y presentación PDF. | [Declaración de uso de IA](../../declaracion-uso-ia.md), este seguimiento y [presentación](../../sustentacion-grupo11.pdf) con [guion de 12 minutos](../../guion-sustentacion.md). | **Documentación y PDF preparados localmente.** Las observaciones orales esperan las notas del equipo. El archivo aún no se ha entregado ni publicado. |

## Pendientes para cerrar la evidencia

1. Incorporar las observaciones concretas del tribunal de la sustentación oral, indicando para cada una la acción, la evidencia y si sigue pendiente.
2. Validar en Render el modelo Flash Lite tras publicarlo. El modelo anterior devolvió `fallback-determinista-sri` por HTTP 429/503; Flash Lite respondió en las pruebas locales con datos sintéticos.
3. Repetir las pruebas sobre el commit que se publique y actualizar las referencias de versión. Los resultados locales no prueban que la demo pública tenga esos cambios.
4. El usuario preparará y subirá el ZIP de entrega. Excluir secretos, entornos y datos personales. El PDF ya está listo en `docs/`; no se afirma una entrega realizada.
