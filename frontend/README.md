# Interfaz del Calendario Tributario RIMPE

SPA en React 18 y Vite. El formulario recoge el perfil del contribuyente durante la sesión; FullCalendar muestra los vencimientos calculados por el backend. El modal de cada obligación presenta la explicación normativa y permite revisar un recordatorio, verificar el correo elegido y autorizar su envío. El simulador de renta consulta el cálculo de Python.

## Desarrollo local

Con el backend disponible en `http://localhost:8000`:

```powershell
npm ci
npm run dev
```

Vite sirve la interfaz en `http://localhost:5173` y redirige `/api` y `/health` al backend local. Los otros comandos son `npm run build` para compilar, `npm run lint` para revisar el código y `npm run preview` para examinar la compilación. En el despliegue, FastAPI sirve los archivos compilados junto con la API desde el mismo origen.

Véase el [README principal](../README.md) para la configuración del proyecto completo, Docker, despliegue y pruebas.
