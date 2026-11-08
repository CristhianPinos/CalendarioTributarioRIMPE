# Pruebas funcionales de producción: pendientes de URL pública

La batería reproducible de 17 casos pasó contra un servidor local real. Consulte [el informe local](08-pruebas-local.md) para peticiones completas, resultados y latencias. **Estos resultados no se presentan como pruebas de producción.**

Cuando Render publique y confirme la URL, ejecutar:

```powershell
python scripts/production_checks.py --base-url https://SERVICIO.onrender.com --output docs/08-pruebas.md
```

El script usa perfiles sintéticos y no envía correos. El cambio hipotético de tarifa se comprueba en un YAML temporal mediante `test_tarifa_se_actualiza_desde_yaml_aislado`; nunca modifica la configuración pública.
