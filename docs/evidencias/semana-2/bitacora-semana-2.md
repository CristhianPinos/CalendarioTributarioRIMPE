# Bitácora Técnica de Trabajo - Semana 2 (Fase 2)

**Proyecto:** Calendario Tributario Personalizado con Recordatorios para Emprendedores RIMPE  
**Fase:** Fase 2 – Construcción del MVP e integración con IA generativa (Semana 2)  
**Integrantes:**
- Desarrollador A: Líder de Frontend e Integración Web
- Cristhian Pinos (Desarrollador B): Líder de Backend Core, Arquitectura de IA & QA Lead  
**Rama de Trabajo:** `feature/frontend-spa` (Full-Stack Integrado)  
**Periodo:** Octubre 2026 / Fase 2 – Semana 2  

---

## 1. Registro Cronológico de Tareas del Backend Core y GenAI (Desarrollador B)

### Paso B1: Motor Determinista Tributario (`backend/services/calculator.py`)
- Implementación de la función `validar_ruc_persona_natural(ruc)` aplicando estrictamente el algoritmo Módulo 10 del SRI:
  - Validación de longitud (13 dígitos numéricos).
  - Código de provincia ecuatoriana (01 a 24).
  - Tercer dígito < 6.
  - Coeficientes `[2, 1, 2, 1, 2, 1, 2, 1, 2]`.
  - Sufijo de establecimiento `001`.
- Implementación de `es_dia_inhabil()` y `trasladar_al_siguiente_dia_habil()` para la prórroga obligatoria de fechas que coincidan con sábados, domingos o feriados nacionales (ej. 24 de mayo - Batalla de Pichincha).
- Implementación de `calcular_vencimientos(ruc, tipo_regimen, anio, tiene_actividades_excluidas)`:
  - RIMPE Emprendedor: 3 obligaciones (IVA Semestre 1 en julio, IVA Semestre 2 en enero, Renta en marzo).
  - RIMPE Negocio Popular: 1 obligación anual en mayo (sin IVA semestral periódico).
  - Condición Mixta: agregación automática de la obligación de IVA bajo Régimen General para actividades excluidas.
- Implementación de `simular_cuota_renta(ingresos_brutos, tipo_regimen)` con la escala oficial del Art. 23 de la Ley de Eficiencia Económica.

### Paso B2: Suite de Pruebas Unitarias del Motor (`backend/tests/test_calculator.py`)
- Instalación y registro de `pytest>=8.0.0` en `backend/requirements.txt`.
- Construcción de **64 pruebas unitarias automatizadas**:
  - 25 pruebas de validación de RUC (casos válidos de todas las provincias y novenos dígitos; rechazo de 12 causas de invalidez).
  - 10 pruebas de mapeo directo de los novenos dígitos (1 al 0 $\rightarrow$ días 10 al 28).
  - 4 pruebas de traslados de fechas (sábado a lunes, domingo a lunes, feriado Batalla de Pichincha y días hábiles).
  - 3 pruebas de diferenciación de obligaciones por régimen y condición mixta.
  - 19 pruebas del simulador progresivo de renta (escalas de $0 a $60 USD, alerta de transición para > $20.000 USD y tramos de Emprendedor).
  - 3 pruebas de control de excepciones y validación de entrada.
- Resultado: 64 passed en 0.11s.

### Paso B3: Esquemas Pydantic v2 del Dominio (`backend/schemas.py`)
- Instalación y registro de `email-validator>=2.0.0` para validación segura de correos electrónicos.
- Definición de Enums del dominio: `TipoRegimen` y `CategoriaObligacion`.
- Creación de modelos de datos:
  - `PerfilTributarioCreate` y `PerfilTributarioResponse`.
  - `CalculoVencimientosRequest` y `CalendarioTributarioResponse`.
  - `EventoCalendario` (compatible con FullCalendar).
  - `RecordatorioEstructurado` (contrato JSON estricto para Google Gemini).
  - `ExplicacionObligacionRequest` y `ExplicacionObligacionResponse`.
  - `SimulacionRentaRequest` y `SimulacionRentaResponse`.
- Creación de [`backend/tests/test_schemas.py`](../../../backend/tests/test_schemas.py) con **11 pruebas unitarias** certificando la captura de `ValidationError` (HTTP 422).
- Resultado: 75 passed en 0.48s.

### Paso B4: Servicio de IA con Google Gemini Flash y Tenacity (`backend/services/llm.py`)
- Conexión real con Google Gemini Flash mediante la clave segura `GEMINI_API_KEY` cargada desde `.env`.
- Integración de reintentos exponenciales con `Tenacity` (3 intentos: 1s, 2s, 4s) ante errores HTTP 429 y 503.
- Creación del catálogo determinista oficial de contingencia (`FALLBACK_OBLIGACIONES`) para las 5 obligaciones clave con citas legales de la LRTI y resoluciones SRI.
- Creación de [`backend/tests/test_llm_service.py`](../../../backend/tests/test_llm_service.py) con **10 pruebas unitarias**.
- Resultado: 85 passed en 5.04s.

### Paso B5: Ingeniería de Prompts (v1, v2, v3) y Matriz Benchmark (`docs/05-prompts.md`)
- Creación de las tres plantillas de prompt en `backend/prompts/`:
  - `system_v1.md`: Naïve / texto libre.
  - `system_v2.md`: Intermedia / JSON en markdown.
  - `system_v3.md`: Producción estructurada nativa con citas a los 7 PDFs del SRI y directiva *Zero Date Hallucination*.
- Evaluación de los 10 casos reales de contribuyentes en [05-prompts.md](../../05-prompts.md), demostrando reducción de alucinación de fechas del 40% al 0.0% y 100% de adherencia JSON.

### Paso B6: Routers de la API y Middleware LOPDP (`backend/routers/` & `backend/middleware/`)
- Creación de `backend/middleware/logging_lopdp.py` para enmascaramiento de RUCs (`0923****001`) y correos electrónicos (`j***z@empresa.ec`), e inyección de cabeceras de latencia `X-Process-Time-Ms`.
- Creación de `backend/routers/obligaciones_router.py`:
  - `POST /api/obligaciones/explicar`
  - `POST /api/simulador/renta`
  - `POST /api/test/simular-error-429`
  - `GET /api/obligaciones/catalogo`
- Actualización de `backend/main.py` a la versión 2.0.0.
- Creación de [`backend/tests/test_routers_and_middleware.py`](../../../backend/tests/test_routers_and_middleware.py) con **13 pruebas unitarias**.
- Resultado: 98 passed en 5.64s.

### Paso B7: Pruebas de Integración con Mocks Offline (`backend/tests/test_api_mock.py`)
- Creación de [`backend/tests/test_api_mock.py`](../../../backend/tests/test_api_mock.py) con **8 pruebas de integración de extremo a extremo**:
  - Happy Path con mock de IA y verificación de tokens.
  - Validación de errores HTTP 422 (campos requeridos, formato de fecha, régimen inválido, ingresos negativos).
  - Resiliencia ante error 429: verificación de los 3 reintentos de Tenacity y entrega del fallback determinista oficial.
  - Resiliencia ante error 503: recuperación automática en el segundo reintento.
  - Endpoint interactivo `/api/test/simular-error-429`.
- Resultado de la suite previa: **106 passed en 9.94s**.

### Paso B8: Documentación de Decisiones y Cierre Inicial
- Creación del registro formal de decisiones arquitectónicas en [09-decisiones.md](../../09-decisiones.md) (ADR-001 al ADR-006).
- Saneamiento total de rutas absolutas locales a enlaces relativos portables.

---

## 2. Registro Cronológico de Tareas del Frontend y Enlace de Integración

### Paso F1: Inicialización del Proyecto Frontend
- Creación de la rama dedicada `feature/frontend-spa`.
- Inicialización de la SPA en React 19 con Vite en la carpeta `frontend/`.
- Instalación de dependencias: `@fullcalendar/react`, `@fullcalendar/daygrid`, `@fullcalendar/interaction`, `lucide-react`, `tailwindcss` y `@tailwindcss/vite` (Tailwind CSS v4).
- Configuración de `vite.config.js` y personalización temática de FullCalendar en `src/index.css`.
- Verificación de compilación limpia de producción en 1.49s.

### Paso F2: Router de Calendario en Backend (`backend/routers/calendario_router.py`)
- Implementación de los endpoints:
  - `POST /api/perfil/calcular-vencimientos` y alias `POST /api/calendario/calcular`.
  - `POST /api/perfil/validar-ruc` (validación ultrarrápida de Módulo 10).
  - `GET /api/calendario/feriados` (catálogo oficial de festivos de Ecuador).
- Montaje directo en `backend/main.py`.
- Creación de [`backend/tests/test_calendario_router.py`](../../../backend/tests/test_calendario_router.py) con **9 pruebas automatizadas**.
- Resultado: 115 tests passed en 10.35s.

### Paso F3: Capa de Servicios y Cliente HTTP (`apiClient.js` & `rucValidator.js`)
- Implementación de `frontend/src/utils/rucValidator.js` con el algoritmo Módulo 10 del SRI en JavaScript para validación en tiempo real en el cliente.
- Prueba unitaria en Node.js certificando 8/8 casos de validación de RUC.
- Creación de `frontend/src/services/apiClient.js` con soporte para todos los endpoints de FastAPI (`USE_MOCKS = false` por defecto), captura de errores HTTP 422 y lectura de cabeceras LOPDP `X-Process-Time-Ms`.

### Paso F4: Componente Formulario de Perfil (`frontend/src/components/ProfileForm.jsx`)
- Formulario interactivo con validación visual en tiempo real de RUC de persona natural.
- Presets rápidos de prueba con RUCs reales verificados (Guayas 8, Pichincha 6, Azuay/Mixto 0).
- Selector de régimen tributario (Emprendedor vs Negocio Popular) e interruptor de actividades excluidas.
- Control de estados de carga (`cargando`) y deshabilitación inteligente de envíos erróneos.

### Paso F5: Vista de Calendario Interactivo (`frontend/src/components/CalendarView.jsx`)
- Cuadrícula mensual FullCalendar (`dayGridMonth`) en idioma español.
- Renderizado de eventos con código de colores oficial y distintivo de prórroga (`PRÓRROGA` en ámbar).
- Barra de resumen con RUC, noveno dígito y leyenda de colores.
- Panel lateral de próximos vencimientos ordenado cronológicamente.
- Evento de clic (`eventClick`) conectado a la apertura del modal explicativo de IA.

### Paso F6: Modal Didáctico GenAI y Compuerta HITL (`frontend/src/components/ExplanationModal.jsx`)
- Consulta automática en vivo a `POST /api/obligaciones/explicar` con Google Gemini Flash.
- Desglose estructurado de `RecordatorioEstructurado`: resumen didáctico, formulario SRI, comprobantes autorizados, advertencia en cero y base legal de la LRTI.
- Toggle de Declaración en Cero para consultar directrices en caso de no registrar ventas ni compras.
- Compuerta de confirmación humana (*Human-in-the-Loop* - ADR-04) con casilla obligatoria de consentimiento para programar recordatorios por correo.

### Paso F7: Modal Simulador de Impuesto a la Renta (`frontend/src/components/TaxSimulatorModal.jsx`)
- Conexión con `POST /api/simulador/renta` aplicando el Art. 23 de la Ley de Eficiencia Económica.
- Selector de régimen y 5 botones de ejemplo rápido (\$1.500, \$15.000, \$35.000, \$85.000, \$220.000).
- Desglose de impuesto causado, cuota fija, tasa marginal y alerta pedagógica de transición.

### Paso F8: Ensamble General y Diseño Responsive
- Creación de `Navbar.jsx` con monitor de salud de la API en vivo (`/health`) y botón directo al simulador.
- Creación de `Footer.jsx` con citas jurídicas y declaración de cumplimiento de la LOPDP.
- Integración en `App.jsx` con carga inicial automática y banner de transparencia de IA.
- Configuración de `index.html` con metadatos descriptivos en español y favicon vectorial.
- Verificación de compilación de producción con Vite en 423ms.

### Paso F9: Pruebas de Integración E2E (`backend/tests/test_e2e_integration.py`)
- Creación de 5 pruebas de integración End-to-End validando los 4 flujos principales de usuario y la integridad física del build de producción del frontend.
- Resultado final de la suite de pruebas: **120 pruebas aprobadas (100% Green)** en 10.89s.

### Paso F10: Documentación y Guía de Puesta en Marcha
- Actualización de [README.md](../../../README.md), [03-arquitectura.md](../../03-arquitectura.md) y evidencias de la Semana 2.
- Preparación del entorno para verificación y ejecución local por parte del usuario.

---

## 3. Resumen Métrico Consolidado de la Fase 2

- **Total de Pruebas Automatizadas:** 120 tests (100% aprobados en verde).
- **Módulos Desarrollados:**
  - **Backend Core:** `calculator.py`, `llm.py`, `schemas.py`, `logging_lopdp.py`, `calendario_router.py`, `obligaciones_router.py`.
  - **Frontend SPA:** `ProfileForm.jsx`, `CalendarView.jsx`, `ExplanationModal.jsx`, `TaxSimulatorModal.jsx`, `Navbar.jsx`, `Footer.jsx`, `apiClient.js`, `rucValidator.js`.
  - **Prompts:** `system_v1.md`, `system_v2.md`, `system_v3.md` (benchmark de 10 casos en `docs/05-prompts.md`).
- **Garantías de Calidad:**
  - 0.0% de alucinación de fechas (cálculo puramente determinista en Python).
  - 100% adherencia JSON estructurado bajo Pydantic v2.
  - Cumplimiento de la LOPDP (enmascaramiento PII en logs y cabeceras de latencia).
  - Compuerta HITL obligatoria para despacho de notificaciones.
