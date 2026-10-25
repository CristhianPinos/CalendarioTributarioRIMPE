# Bitácora Técnica de Trabajo - Semana 1 (Fase 1)

**Proyecto:** Calendario Tributario Personalizado con Recordatorios para Emprendedores RIMPE (Caso 11 - Grupo 11)  
**Fase:** Fase 1 – Definición del problema y diseño de la solución inteligente (Semana 1)  
**Integrantes:**
- Desarrollador A: Líder de Frontend e Integración Web
- Cristhian Pinos (Desarrollador B): Líder de Backend Core, Arquitectura de IA y QA Lead  
**Rama Principal de Trabajo:** `main` (Inicialización de Repositorio y Arquitectura Base)  
**Periodo:** Octubre 2026 / Fase 1 – Semana 1  

---

## 1. Registro Cronológico de Tareas Ejecutadas

### Paso 1: Análisis del Problema y Redacción de la Propuesta Técnica ([docs/01-propuesta.md](../../01-propuesta.md))
- Investigación sobre la problemática tributaria del Régimen Simplificado para Emprendedores y Negocios Populares (RIMPE) en el Ecuador.
- Identificación de los dos arquetipos fundamentales de usuario:
  - **Negocio Popular:** Personas naturales con ingresos brutos anuales de hasta \$20.000 USD (artesanos, bazares, ferreterías barriales, minimarkets).
  - **Emprendedor:** Personas naturales y jurídicas con ingresos brutos anuales entre \$20.000,01 USD y \$300.000 USD.
- Delimitación del **alcance positivo**:
  - Registro de perfil con validación de RUC de persona natural ecuatoriana (algoritmo Módulo 10).
  - Visualización mensual en cuadrícula FullCalendar con diferenciación cromática de obligaciones.
  - Explicaciones pedagógicas generadas con Google Gemini Flash fundamentadas en los 7 PDFs del SRI.
  - Simulador didáctico de Impuesto a la Renta según la escala del Art. 23 de la Ley de Eficiencia Económica.
- Delimitación del **alcance negativo**:
  - El sistema no es un consultorio tributario general ni responde temas contables no previstos.
  - No realiza declaraciones automáticas ante el portal del SRI ni emite facturas electrónicas.
  - No fomenta ni responde consultas sobre evasión tributaria o elusión fiscal.
- Evaluación y justificación de **Google Gemini Flash** como modelo fundacional por costo, velocidad y soporte de esquemas JSON estructurados.

---

### Paso 2: Especificación Formal de Requisitos Funcionales y No Funcionales ([docs/02-requisitos.md](../../02-requisitos.md))
- Redacción de **10 Historias de Usuario (HU)** detalladas bajo el estándar de la industria, cada una con su narrativa y criterios de aceptación en formato Gherkin (`Dado... Cuando... Entonces...`):
  - `HU-01`: Registro y perfilamiento del contribuyente RIMPE con validación de RUC.
  - `HU-02`: Generación del calendario personalizado según noveno dígito y feriados de Ecuador.
  - `HU-03`: Explicación didáctica contextual de la obligación mediante panel modal.
  - `HU-04`: Alerta visual anticipada para obligaciones próximas (5 días antes).
  - `HU-05`: Generación y previsualización de recordatorio estructurado para correo.
  - `HU-06`: Compuerta de confirmación humana (*Human-in-the-Loop*) previa al envío.
  - `HU-07`: Simulación pedagógica de cuota del Impuesto a la Renta.
  - `HU-08`: Soporte para contribuyentes con actividades excluyentes (IVA semestral vs mensual).
  - `HU-09`: Resiliencia ante fallos de conectividad con reintentos y fallback determinista.
  - `HU-10`: Protección y privacidad de datos personales conforme a la LOPDP ecuatoriana.
- Definición de **7 Requisitos No Funcionales (RNF)** con métricas cuantitativas:
  - Latencia de respuesta del backend < 2.0 segundos (p95).
  - 0.0% de margen de error en fechas de vencimiento tributario.
  - Disponibilidad del servicio del 99.5%.
  - Anonimizador y enmascaramiento de PII conforme a la LOPDP.
  - Resiliencia con conmutación por error ante Rate Limit HTTP 429.
  - Interfaz accesible, responsive y visualizable en móviles y tablets.
  - 0% de constantes quemadas (*hardcoding*) en el código fuente.
- Diseño preliminar del modelo relacional de datos y esquemas de validación de entrada/salida.

---

### Paso 3: Diseño de Arquitectura C4 y Flujos de Secuencia ([docs/03-arquitectura.md](../../03-arquitectura.md))
- Elaboración de diagramas de arquitectura en Mermaid:
  - **Diagrama C4 Context (Nivel 1):** Interacción entre el Contribuyente RIMPE, la plataforma web del Calendario Tributario, el API de Google Gemini Flash y el servidor SMTP de correos.
  - **Diagrama C4 Container (Nivel 2):** Desacoplamiento de la Single Page Application (React + Tailwind CSS + FullCalendar), el Backend API en FastAPI (Python 3.10+), el motor de reglas deterministas (`calculator.py`), el servicio generativo (`llm.py`) y el almacén documental.
  - **Diagrama de Secuencia:** Flujo paso a paso del proceso de consulta de calendario, generación de recordatorio asistido y compuerta de aprobación humana (*HITL*) antes del despacho.
- Definición de la **Matriz de Segregación de Responsabilidades**:
  - Frontend: Captura de datos, renderizado de calendario mensual interactivo, modales didácticos y retroalimentación de estados de carga.
  - Backend: Validación matemática de RUC, cálculo determinista de vencimientos por noveno dígito y feriados, gobernanza de privacidad LOPDP.
  - Capa GenAI: Redacción pedagógica, extracción de citas de artículos normativos y formateo estructurado bajo JSON Schema.

---

### Paso 4: Descarga Íntegra e Inventario Oficial de Normativa en `data/raw/` ([docs/04-fuentes.md](../../04-fuentes.md))
- Descarga y archivado en el directorio [data/raw/](../../../data/raw/) de los **7 documentos PDF oficiales e íntegros** del SRI y del Registro Oficial:
  1. `01_resolucion_sri_nac_dgercgc24_00000027.pdf` – Resolución del SRI sobre retenciones en la fuente e IVA.
  2. `02_resolucion_sri_nac_dgercgc23_00000034_calendario.pdf` – Resolución del calendario de vencimientos por noveno dígito.
  3. `03_ley_organica_eficiencia_economica_registro_oficial_461.pdf` – Suplemento 461 del Registro Oficial con tarifas de RIMPE y reformas.
  4. `04_reglamento_aplicacion_lrti.pdf` – Reglamento para la Aplicación de la Ley de Régimen Tributario Interno.
  5. `05_ley_regimen_tributario_interno_lrti.pdf` – Ley de Régimen Tributario Interno (LRTI codificada).
  6. `06_codigo_tributario_ecuador.pdf` – Código Tributario de la República del Ecuador.
  7. `07_reglamento_comprobantes_venta_retencion.pdf` – Reglamento de Comprobantes de Venta, Retención y Documentos Complementarios.
- Catalogación minuciosa de cada documento: identificador normativo, denominación legal, emisor oficial, URL institucional de origen (SRI Alfresco / Registro Oficial), vigencia para el ejercicio fiscal 2026 y hash/peso en bytes.
- Diseño de la estrategia de fragmentación (*chunking*) semántica respetando la división por artículos, disposiciones transitorias y tablas anexas.

---

### Paso 5: Levantamiento Empírico de Preguntas Reales de Contribuyentes ([docs/levantamiento-preguntas.md](../../levantamiento-preguntas.md))
- Recolección de dudas e inquietudes frecuentes de microemprendedores ecuatorianos inscritos en RIMPE.
- Sistematización de **16 casos reales** (superando el mínimo de 15 requerido por la rúbrica):
  - Declaraciones semestrales de IVA vs. declaraciones en cero.
  - Obligatoriedad de facturación electrónica vs. notas de venta físicas de Negocio Popular.
  - Cálculo de cuota progresiva de Impuesto a la Renta según ingresos brutos anuales.
  - Coexistencia de actividades comerciales con actividades excluyentes (servicios profesionales, arriendos, comisiones).
  - Traslado de fechas límite cuando el vencimiento nominal coincide con feriados o fines de semana.
  - Sanciones, multas e intereses por presentación extemporánea.
- Mapeo técnico de cada una de las 16 consultas contra la base jurídica específica y el componente del sistema responsable de atenderla.

---

### Paso 6: Desacoplamiento de Reglas Tributarias en `config/sri_rules_2026.json`
- Creación del archivo de configuración central [config/sri_rules_2026.json](../../../config/sri_rules_2026.json) para garantizar un **0% de constantes quemadas en el código**:
  - Tabla de noveno dígito del RUC con día calendario asignado (dígito 1 $\rightarrow$ día 10, ..., dígito 0 $\rightarrow$ día 28).
  - Catálogo de feriados oficiales no recuperables del Ecuador para el año 2026 (Año Nuevo, Carnaval, Viernes Santo, Día del Trabajo, Batalla de Pichincha, Primer Grito de Independencia, Independencia de Guayaquil, Día de Difuntos, Independencia de Cuenca, Navidad).
  - Reglas de periodicidad por régimen (RIMPE Emprendedor: IVA semestral julio/enero + Renta marzo; Negocio Popular: Renta única mayo).
  - Tabla progresiva de Impuesto a la Renta de la Ley de Eficiencia Económica (escalas desde \$0 hasta \$60 USD para Negocios Populares y tramos porcentuales para Emprendedores).

---

### Paso 7: Implementación del Esqueleto Ejecutable de FastAPI ([backend/main.py](../../../backend/main.py))
- Creación del archivo inicial de la aplicación backend con FastAPI y ASGI Uvicorn.
- Configuración de `CORSMiddleware` para habilitar peticiones cross-origin desde el cliente web.
- Implementación del endpoint raíz `GET /` con metadatos del servicio y versión.
- Implementación del endpoint de monitoreo `GET /health` respondiendo estado operativo `{"status": "healthy", "service": "CalendarioTributarioRIMPE"}`.
- Especificación de librerías esenciales en [backend/requirements.txt](../../../backend/requirements.txt) (`fastapi`, `uvicorn`, `pydantic`, `httpx`).
- Verificación en local mediante ejecución del servidor y prueba de respuesta JSON HTTP 200.

---

### Paso 8: Gobernanza de Git, Documentación de Traspaso y Cierre de Semana ([HANDOFF.md](../../../HANDOFF.md))
- Creación de `.gitignore` integral para proteger claves de API, entornos virtuales (`.venv`), archivos de caché de Python y carpetas pesadas.
- Elaboración de `.env.example` definiendo las variables requeridas (`GEMINI_API_KEY`, `GEMINI_MODEL`, `PORT`, `ENVIRONMENT`).
- Redacción del documento formal de traspaso [HANDOFF.md](../../../HANDOFF.md) detallando:
  - Contratos de integración de la API (JSON de entrada y salida para cálculo de calendario y explicaciones didácticas).
  - Asignación equitativa de responsabilidades para la Fase 2 (Desarrollador A en Frontend vs. Cristhian Pinos en Backend).
  - Identificación preventiva de riesgos (alucinaciones de fechas, rate limits HTTP 429, fallas de validación de RUC).
  - Estado de accesos (clave de Gemini confirmada y permisos de colaborador en GitHub).

---

## 2. Resumen de Comandos y Validaciones Técnicas Ejecutadas

Durante la ejecución de la Fase 1 se ejecutaron y verificaron los siguientes comandos en el entorno local:

```bash
# 1. Verificación del entorno de Python
python --version
# Salida: Python 3.14.x / 3.10+ compatible

# 2. Instalación de dependencias base del backend
pip install -r backend/requirements.txt

# 3. Prueba de arranque del servidor FastAPI
uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload

# 4. Verificación del endpoint de salud
curl -i http://127.0.0.1:8000/health
# HTTP/1.1 200 OK
# Content-Type: application/json
# {"status":"healthy","service":"CalendarioTributarioRIMPE"}

# 5. Verificación de integridad de los 7 PDFs oficiales
python -c "
import glob, os
pdfs = glob.glob('data/raw/*.pdf')
print(f'Total PDFs descargados: {len(pdfs)}')
for p in pdfs:
    print(f'- {os.path.basename(p)} ({os.path.getsize(p)} bytes)')
"
# Total PDFs descargados: 7 (todos con tamaño mayor a cero y válidos)

# 6. Verificación de sintaxis de la configuración tributaria JSON
python -c "
import json
with open('config/sri_rules_2026.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
print('Configuracion valida:', data['metadata']['ejercicio_fiscal'])
"
# Salida: Configuracion valida: 2026
```

---

## 3. Métricas de Cumplimiento y Estado al Cierre de la Semana 1

| Criterio Evaluado | Meta de Rúbrica | Estado Alcanzado | Observación |
| :--- | :---: | :---: | :--- |
| **Documentos de Diseño** | 4 documentos | **5 documentos** | `01-propuesta.md`, `02-requisitos.md`, `03-arquitectura.md`, `04-fuentes.md`, `09-decisiones.md`. |
| **Historias de Usuario** | $\ge$ 8 historias | **10 historias** | Con formato Gherkin y criterios de aceptación verificables. |
| **Requisitos No Funcionales** | Medibles | **7 RNF** | Con métricas de latencia, disponibilidad y privacidad LOPDP. |
| **Preguntas Reales de Contribuyentes** | $\ge$ 15 preguntas | **16 preguntas** | Con mapeo de artículos y leyes ecuatorianas. |
| **Cuerpos Normativos Oficiales** | Documentos íntegros | **7 PDFs oficiales** | Archivados íntegramente en `data/raw/`. |
| **Contratos de Integración** | Definidos | **100% acordados** | Modelos JSON listos para desarrollo en paralelo. |
| **Esqueleto Ejecutable** | Opcional | **Implementado** | FastAPI `/health` respondiendo HTTP 200 OK en local. |
| **Portabilidad de Enlaces** | 100% rutas relativas | **100% verificado** | Cero enlaces absolutos `file:///` en la documentación. |

---

## 4. Conclusiones de la Semana 1

1. **Fundamentos sólidos para desarrollo en paralelo:** La formalización de contratos de integración en [HANDOFF.md](../../../HANDOFF.md) y la separación de responsabilidades permitieron que el Desarrollador A (Frontend) y el Desarrollador B (Backend) puedan trabajar de manera independiente sin bloquearse mutuamente.
2. **Mitigación temprana del riesgo de alucinación:** Al definir en la arquitectura que las fechas se calculan de manera determinista en Python y nunca por inferencia del LLM, se erradicó de raíz la mayor causa de multas e inconformidad tributaria.
3. **Cumplimiento total de la rúbrica:** La totalidad de los entregables de la Semana 1 fueron completados, estructurados y versionados en el repositorio de manera profesional y auditable.
