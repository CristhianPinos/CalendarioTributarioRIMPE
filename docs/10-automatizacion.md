# Documento de Diseño: Flujo Automatizado y Programado (Semana 3)

> **Estado al 11 de noviembre de 2026:** este documento describe el diseño histórico de la semana 3. Las rutas `/api/perfiles` y `/api/flujo` y el planificador no se montan en la aplicación pública actual. El flujo activo es el envío puntual con código temporal de correo y confirmación; no requiere operador ni guarda perfiles tributarios. Véase ADR-010 en `docs/09-decisiones.md`.

**Proyecto:** Calendario Tributario Personalizado con Recordatorios para Emprendedores RIMPE  
**Módulo:** Automatización de Tareas Diarias y Notificaciones Programadas (`backend/services/scheduler.py`)  
**Fecha:** Octubre / Noviembre 2026  
**Estado:** Diseño histórico implementado y probado; su router y el planificador no están montados en la aplicación actual.

**Disparador diario del diseño histórico:** `backend/services/periodic_scan.py` puede habilitarse en una instalación que vuelva a integrar el planificador y la persistencia, pero `backend/main.py` no lo inicia actualmente. Los parámetros `SCHEDULER_ENABLED`, `SCHEDULER_CRON_HOUR`, `SCHEDULER_CRON_MINUTE` y `TIMEZONE` no activan por sí solos este flujo en la aplicación actual. La ruta manual de `flujo_router.py` tampoco está montada.

El disparador es interno a un proceso: habilitarlo en una sola instancia para evitar escaneos duplicados. SQLite impone unicidad de `RUC + obligación + fecha`; la confirmación reserva la fila atómicamente antes del SMTP. Tras un fallo se registra el tipo de error y se espera el siguiente horario; la ruta manual permite una recuperación supervisada. El planificador solo prepara elementos `PENDIENTE_CONFIRMACION` y no aprueba ni despacha correos.

**Persistencia:** `backend/services/storage.py` abre SQLite de forma diferida en `RIMPE_DB_PATH` (por defecto `data/processed/rimpe.sqlite3`). En el primer acceso, importa una sola vez la cola JSON anterior, crea `recordatorios_pendientes.json.bak` y conserva el JSON original. La importación no crea perfiles ni consentimiento: esos recordatorios antiguos no se pueden despachar hasta que un operador registre un perfil con autorización para el mismo RUC y correo. Se recomienda respaldar la base con la API `SQLiteStore.backup_to()` y restaurarla con la aplicación detenida. La base y su respaldo contienen datos personales; deben almacenarse en un volumen privado con acceso restringido. El estado `EN_PROCESO` después de una interrupción se muestra en revisión y no puede reenviarse automáticamente.

**Registro del diseño histórico:** `perfiles_router.py` implementa alta y consulta de perfiles para una instalación persistente, pero esas rutas no están expuestas por la aplicación actual. El formulario público no ofrece registro y generar el calendario no guarda datos. La reactivación del registro y del escaneo requeriría volver a definir consentimiento, autorización y almacenamiento duradero.

**Interfaz de despacho histórica:** La etapa 5 exigía autorización de operador y consentimiento persistido. ADR-010 sustituyó este flujo: el modal actual solicita un código temporal al correo elegido, exige confirmación explícita y despacha un recordatorio puntual sin registrar un perfil. ADR-011 sustituyó el transporte SMTP del flujo puntual por la API HTTPS de Mailjet.

---

## 1. Propósito y Alcance del Flujo

El objetivo del flujo automatizado es escanear periódicamente la base de contribuyentes del RIMPE, identificar las obligaciones tributarias que vencen en los próximos **5 días hábiles** (calculados con el calendario oficial de feriados del SRI y traslados por fines de semana), orquestar con el agente inteligente la redacción fundamentada del mensaje con citas normativas del RAG, y encolar el recordatorio bajo una **compuerta estricta de confirmación humana (Human-in-the-Loop - HITL)**.

---

## 2. Diagrama de la Arquitectura del Flujo

```
  ┌─────────────────────────────────────────────────────────────┐
  │        PeriodicScanRunner (hora local configurable)         │
  │   Ruta manual: POST /api/flujo/ejecutar-tarea-diaria         │
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
  │  4. Cola SQLite Idempotente (rimpe.sqlite3)                  │
  │        Estado inicial: PENDIENTE_CONFIRMACION               │
  └──────────────────────────────┬──────────────────────────────┘
                                 │
                                 ▼
  ┌─────────────────────────────────────────────────────────────┐
  │             5. Compuerta de Confirmación Humana             │
  │         El operador humano revisa y aprueba el envío        │
  │           POST /api/flujo/confirmar-recordatorio/{id}       │
  └──────────────────────────────┬───────────────────────────────┘
                                 │ Aprobado y consentimiento vigente
                                 ▼
                    ┌──────────────────────────────┐
                    │ SMTP: ENVIADO, SIMULADO,      │
                    │ ERROR_ENVIO o ESTADO_INCIERTO │
                    └──────────────────────────────┘
```

---

## 3. Decisiones de Diseño Clave

1. **Ventana de 5 Días Hábiles:**
   - La antelación de notificación no se cuenta en días calendario brutos, sino en **días hábiles laborales**, integrando los feriados de `config/parametros.yaml`. Esto evita notificar con retraso ante feriados puente (e.g. Carnaval, Semana Santa, Batalla de Pichincha).
2. **Idempotencia en la Cola de Recordatorios:**
   - Para evitar spam o duplicación de mensajes si la tarea se ejecuta varias veces en el mismo día, la clave de encolamiento combina `RUC + CODIGO_OBLIGACION + FECHA_VENCIMIENTO`. Si ya existe un recordatorio, no se vuelve a generar.
   - Tras la aprobación, `ENVIADO` significa aceptación del mensaje por SMTP. Sin configuración de correo queda `SIMULADO`; un fallo previo a la transmisión queda `ERROR_ENVIO`. Si la respuesta se pierde durante la transmisión queda `ESTADO_INCIERTO`, visible en `/api/flujo/recordatorios-en-revision` y bloqueado para reintento automático o confirmación repetida.
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
- `GET /api/flujo/recordatorios-en-revision`: Muestra `ESTADO_INCIERTO` y `EN_PROCESO` para verificación manual.
