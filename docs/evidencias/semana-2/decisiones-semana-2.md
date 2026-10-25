# Evidencias Técnicas y Decisiones de la Semana 2 (Fase 2)

**Proyecto:** Calendario Tributario Personalizado con Recordatorios para Emprendedores RIMPE  
**Fase:** Fase 2 – Construcción del MVP e integración con IA generativa (Semana 2)  
**Integrantes:**
- Desarrollador A: Líder de Frontend e Integración Web
- Cristhian Pinos (Desarrollador B): Líder de Backend Core, Arquitectura de IA y QA  
**Periodo:** Octubre 2026 / Fase 2 – Semana 2  
**Estado:** 100% Implementado, Integrado y Testeado (120 Tests en Verde)

---

## 1. Resumen de Decisiones Técnicas Tomadas en la Semana 2

Durante la Semana 2 se materializaron las siguientes decisiones arquitectónicas críticas (documentadas formalmente en [09-decisiones.md](../../09-decisiones.md)):

1. **ADR-001 (Google Gemini Flash):** Consolidación de Google Gemini Flash (`gemini-3-flash-preview` / `gemini-3.8-flash`) como único motor generativo del proyecto, purgando cualquier rastro o dependencia de OpenAI.
2. **ADR-002 (Integración API-First):** Contrato desacoplado entre Frontend y Backend mediante esquemas Pydantic v2 y soporte de mocks (`USE_MOCKS = false` por defecto en vivo con opción de contingencia).
3. **ADR-003 (Resiliencia Tenacity & Fallback Determinista):** Manejo de errores HTTP 429 (Rate Limit) y 503 con retroceso exponencial de 3 intentos (`1s, 2s, 4s`) y conmutación automática al catálogo determinista del SRI para garantizar 100% de disponibilidad.
4. **ADR-004 (Inmutabilidad de Fechas):** Blindaje *Zero Date Hallucination* donde el LLM recibe las fechas calculadas matemáticamente por Python y tiene prohibido recalcularlas.
5. **ADR-005 (Observabilidad y Privacidad LOPDP):** Middleware asíncrono para enmascarar RUCs (`0923****001`) y correos electrónicos (`j***z@empresa.ec`), midiendo latencias con la cabecera `X-Process-Time-Ms`.
6. **ADR-006 (Desacoplamiento de Reglas Tributarias):** Parámetros normativos y feriados de Ecuador 2026 externalizados en `config/sri_rules_2026.json` (0% constantes quemadas).

---

## 2. Comparativa de Versiones del Prompt (v1, v2, v3)

Se realizaron pruebas exhaustivas comparando 3 iteraciones del prompt del sistema sobre una matriz benchmark de **10 casos reales de contribuyentes RIMPE** (ver detalle completo en [05-prompts.md](../../05-prompts.md)):

```text
Iteración 1 (system_v1.md):
- Enfoque: Naïve / Texto libre conversacional.
- Alucinación de fechas: 40.0% (intentaba calcular fechas sin considerar feriados locales).
- Adherencia JSON: 0.0% (texto plano no parseable).
- Estado: DEPRECADA.

Iteración 2 (system_v2.md):
- Enfoque: Intermedio / Bloque JSON en markdown.
- Alucinación de fechas: 10.0%.
- Adherencia JSON: 70.0% (requería regex para limpiar bloques ```json).
- Estado: DEPRECADA.

Iteración 3 (system_v3.md):
- Enfoque: Producción / Generación estructurada nativa + Blindaje inmutable + Citas a los 7 PDFs del SRI.
- Alucinación de fechas: 0.0% (Cero alucinación).
- Alucinación de montos: 0.0% (Tarifas acordes a la Ley de Eficiencia Económica).
- Adherencia JSON: 100.0% (Parseo directo en RecordatorioEstructurado).
- Precisión normativa: 95.0% de citas verificables de la LRTI y resoluciones vigentes.
- Estado: ACTIVA EN PRODUCCIÓN.
```

---

## 3. Estado de la Suite de Pruebas Automatizadas (QA)

La suite de pruebas con `pytest` alcanzó un total de **120 pruebas unitarias, de integración y E2E**, ejecutadas al 100% en verde:

| Módulo de Prueba | Cantidad | Alcance Técnico |
| :--- | :---: | :--- |
| [`test_calculator.py`](../../../backend/tests/test_calculator.py) | 64 | Algoritmo Módulo 10 de RUC, 10 novenos dígitos, traslados por fin de semana, feriados del SRI y simulación de renta progresiva. |
| [`test_schemas.py`](../../../backend/tests/test_schemas.py) | 11 | Validación de esquemas Pydantic v2, tipos de régimen, email y `RecordatorioEstructurado`. |
| [`test_llm_service.py`](../../../backend/tests/test_llm_service.py) | 10 | Servicio LLM, 5 plantillas del catálogo determinista, reintentos Tenacity y parsing estructurado. |
| [`test_routers_and_middleware.py`](../../../backend/tests/test_routers_and_middleware.py) | 13 | Endpoints FastAPI, anonimización LOPDP de RUC y correo, cabeceras `X-Process-Time-Ms`. |
| [`test_api_mock.py`](../../../backend/tests/test_api_mock.py) | 8 | Pruebas de integración de la API con mocks offline (Happy Path, HTTP 422, HTTP 429 y HTTP 503). |
| [`test_calendario_router.py`](../../../backend/tests/test_calendario_router.py) | 9 | Endpoints de cálculo de calendario, feriados oficiales de Ecuador y validación rápida de RUC. |
| [`test_e2e_integration.py`](../../../backend/tests/test_e2e_integration.py) | 5 | Pruebas de integración End-to-End de los 4 flujos de usuario e integridad del build de producción del frontend. |
| **TOTAL** | **120** | **100% Aprobados (Green) en ~10.8s** |

---

## 4. Endpoints Expuestos y Documentación de la API

El backend expone en [http://localhost:8000/docs](http://localhost:8000/docs) los siguientes servicios:
- `POST /api/perfil/calcular-vencimientos`: Cálculo determinista de vencimientos ajustados por días hábiles.
- `POST /api/calendario/calcular`: Ruta alias para cálculo de calendario.
- `POST /api/perfil/validar-ruc`: Validación sintáctica y Módulo 10 rápida de RUC de persona natural.
- `GET /api/calendario/feriados`: Catálogo de feriados oficiales no recuperables del Ecuador.
- `POST /api/obligaciones/explicar`: Inferencia pedagógica estructurada con Google Gemini Flash.
- `POST /api/simulador/renta`: Cálculo matemático de cuotas de impuesto a la renta según Ley de Eficiencia Económica.
- `GET /api/obligaciones/catalogo`: Catálogo normativo oficial de contingencia.
- `POST /api/test/simular-error-429`: Simulación forzada de saturación de cuota para pruebas de resiliencia.
- `GET /health`: Verificación de salud y estado de la API.

---

## 5. Decisiones de Diseño e Integración del Frontend (SPA)

1. **Interfaz Centrada en FullCalendar (ADR-01 y ADR-02):**
   - En lugar de un chatbot conversacional que genera ambigüedad, la pantalla principal presenta una cuadrícula mensual interactiva (`CalendarView.jsx`) con código de colores según régimen y alertas de prórroga.
2. **Validación Client-Side Inmediata (Módulo 10):**
   - El archivo `rucValidator.js` ejecuta en cliente el mismo algoritmo Módulo 10 del backend, ofreciendo retroalimentación visual instantánea (insignias verdes con el 9.º dígito y día de vencimiento).
3. **Compuerta Human-in-the-Loop (HITL) en UI:**
   - En `ExplanationModal.jsx`, el usuario debe marcar de forma expresa una casilla de confirmación para habilitar el botón de programación de recordatorios por correo, previniendo despachos desatendidos.
4. **Simulador de Renta Interactivo:**
   - En `TaxSimulatorModal.jsx`, los microempresarios pueden evaluar en tiempo real su cuota estimada de impuesto a la renta con alertas pedagógicas si superan el límite de Negocio Popular (\$20k) o de RIMPE (\$300k).
