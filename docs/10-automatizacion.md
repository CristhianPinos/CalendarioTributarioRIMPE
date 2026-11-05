# Documento de Diseño: Flujo Automatizado y Programado (Semana 3)

**Proyecto:** Calendario Tributario Personalizado con Recordatorios para Emprendedores RIMPE  
**Módulo:** Automatización de Tareas Diarias y Notificaciones Programadas (`backend/services/scheduler.py`)  
**Fecha:** Octubre / Noviembre 2026  
**Estado:** Implementado, Probado e Integrado en API (`backend/routers/flujo_router.py`)  

---

## 1. Propósito y Alcance del Flujo

El objetivo del flujo automatizado es escanear periódicamente la base de contribuyentes del RIMPE, identificar las obligaciones tributarias que vencen en los próximos **5 días hábiles** (calculados con el calendario oficial de feriados del SRI y traslados por fines de semana), orquestar con el agente inteligente la redacción fundamentada del mensaje con citas normativas del RAG, y encolar el recordatorio bajo una **compuerta estricta de confirmación humana (Human-in-the-Loop - HITL)**.

---

## 2. Diagrama de la Arquitectura del Flujo

```
  ┌─────────────────────────────────────────────────────────────┐
  │                 Disparador Programado (Cron Diario)         │
  │               POST /api/flujo/ejecutar-tarea-diaria         │
  └──────────────────────────────┬──────────────────────────────┘
                                 │
                                 ▼
  ┌─────────────────────────────────────────────────────────────┐
  │       1. Escaneo de Base de Contribuyentes (RUCs SRI)       │
  │    Cálculo de vencimientos deterministas para el año 2026   │
  └──────────────────────────────┬──────────────────────────────┘
                                 │
                                 ▼
  ┌─────────────────────────────────────────────────────────────┐
  │       2. Filtro de Antelación: Próximos 5 Días Hábiles      │
  │    Considera feriados nacionales y traslados al día hábil   │
  └──────────────────────────────┬──────────────────────────────┘
                                 │
                                 ▼
  ┌─────────────────────────────────────────────────────────────┐
  │       3. Redacción del Recordatorio con Motor RAG           │
  │    Fundamentación jurídica oficial: [Documento, Art. X]     │
  └──────────────────────────────┬──────────────────────────────┘
                                 │
                                 ▼
  ┌─────────────────────────────────────────────────────────────┐
  │  4. Cola Persistente Idempotente (recordatorios_pendientes) │
  │        Estado inicial: PENDIENTE_CONFIRMACION               │
  └──────────────────────────────┬──────────────────────────────┘
                                 │
                                 ▼
  ┌─────────────────────────────────────────────────────────────┐
  │             5. Compuerta de Confirmación Humana             │
  │         El operador humano revisa y aprueba el envío        │
  │           POST /api/flujo/confirmar-recordatorio/{id}       │
  └──────────────┬──────────────────────────────┬───────────────┘
                 │ Aprobado                     │ Rechazado / Editado
                 ▼                              ▼
  ┌──────────────────────────────┐    ┌─────────────────────────┐
  │     Despacho Real: ENVIADO   │    │  Cancelado / Archivado  │
  │  Emisión: AUD-DISPATCH-XXX   │    │  Sin despacho al buzón  │
  └──────────────────────────────┘    └─────────────────────────┘
```

---

## 3. Decisiones de Diseño Clave

1. **Ventana de 5 Días Hábiles:**
   - La antelación de notificación no se cuenta en días calendario brutos, sino en **días hábiles laborales**, integrando los feriados de `config/parametros.yaml`. Esto evita notificar con retraso ante feriados puente (e.g. Carnaval, Semana Santa, Batalla de Pichincha).
2. **Idempotencia en la Cola de Recordatorios:**
   - Para evitar spam o duplicación de mensajes si la tarea se ejecuta varias veces en el mismo día, la clave de encolamiento combina `RUC + CODIGO_OBLIGACION + FECHA_VENCIMIENTO`. Si ya existe un recordatorio en estado `PENDIENTE_CONFIRMACION` o `ENVIADO`, no se vuelve a generar.
3. **Compuerta Humana Inviolable (HITL):**
   - El sistema tiene estrictamente prohibido despachar correos o mensajes a contribuyentes sin confirmación humana previa. El estado inicial es siempre `PENDIENTE_CONFIRMACION`.
4. **Trazabilidad y Auditoría LOPDP:**
   - Al confirmarse el despacho, el sistema genera un identificador único de auditoría `AUD-DISPATCH-<timestamp>` y anonimiza los datos personales en los logs de conformidad con la Ley Orgánica de Protección de Datos Personales.

---

## 4. Endpoints Expuestos en la API

- `POST /api/flujo/ejecutar-tarea-diaria`: Ejecuta el escaneo y prepara la cola de recordatorios.
- `GET /api/flujo/recordatorios-pendientes`: Lista los recordatorios pendientes de confirmación con su fundamentación RAG.
- `POST /api/flujo/confirmar-recordatorio/{id}`: Aprueba y despacha un recordatorio específico.
- `POST /api/flujo/confirmar-todos`: Aprueba en lote los recordatorios revisados por el supervisor.
