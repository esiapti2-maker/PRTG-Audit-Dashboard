# PRTG Audit Dashboard

Dashboard de auditoría para **PRTG Network Monitor** — aplicación HTML estática de una sola página complementada con un script Python CLI para escenarios multi-sitio o donde el navegador tenga restricciones de CORS.

## Qué incluye el repositorio

```
PRTG-Audit-Dashboard/
├── prtg-audit-dashboard.html   # Dashboard HTML estático ← AQUÍ
├── scripts/
│   └── prtg_audit.py           # Script CLI Python para auditoría
├── requirements.txt
├── .gitignore
└── README.md
```

## Dashboard HTML

### Características

- **KPIs automáticos** — dispositivos, sensores OK/Down, sensores sin umbrales y Score de Auditoría (0–100 %)
- **Sensores** — tabla completa con filtro por estado y búsqueda en tiempo real
- **Umbrales** — sensores con `limitmode=0` o sin `LimitMaxError`/`LimitMaxWarning` configurados
- **Usuarios & Accesos** — clasificación automática de riesgo (Alto/Medio/Bajo)
- **Notificaciones** — detecta notificaciones inactivas o sin disparadores
- **Checklist de auditoría** — 8 verificaciones automáticas con semáforo Cumple/Revisar
- **Scripts API** — ejemplos listos en cURL y Python
- **Exportación CSV** — hallazgos descargables directamente desde el navegador
- **Modo oscuro/claro** — toggle manual, respeta preferencia del sistema
- **Responsive** — funciona en móvil y desktop

### Uso

1. Abre `prtg-audit-dashboard.html` en cualquier navegador moderno.
2. Haz clic en **"Demo"** para explorar la interfaz sin conectarte a PRTG.
3. Para conectar a tu PRTG real: ingresa `Host`, `Usuario API` y `Passhash`.
   > El passhash se consulta en PRTG: **Setup → My Account → Show Passhash**.
4. Haz clic en **"Conectar y auditar"**.
5. Usa **"Exportar CSV"** para generar el reporte de hallazgos.

### Nota sobre CORS

La API HTTP de PRTG es stateless y puede consultarse con `username + passhash` o con `apitoken`. La conexión directa desde el navegador puede generar errores CORS si PRTG no tiene configurado el encabezado `Access-Control-Allow-Origin`. En ese caso, usa el script Python del repositorio, que no tiene esta limitación.

## Script Python CLI

### Instalación

```bash
pip install -r requirements.txt
```

### Ejemplo básico

```bash
python scripts/prtg_audit.py \
  --host https://prtg.miempresa.com \
  --user auditor \
  --passhash TU_PASSHASH \
  --site-name Corporativo \
  --output ./reportes
```

### Multi-sitio

Edita la lista `SITES` en `scripts/prtg_audit.py`:

```python
SITES = [
    {
        "name": "Sitio-GDL",
        "host": "https://prtg-gdl.empresa.com",
        "username": "auditor",
        "passhash": "1234567890",
    },
    {
        "name": "Sitio-DR",
        "host": "https://prtg-mty.empresa.com",
        "username": "auditor",
        "passhash": "0987654321",
    },
]
```

```bash
python scripts/prtg_audit.py --multi-site --output ./reportes
```

## Hallazgos cubiertos

| Hallazgo | Descripción | Acción recomendada |
|---|---|---|
| Sensor Down | Estado `Down` activo | Investigar causa raíz |
| Sensor Warning | Estado `Warning` activo | Revisar umbrales y dispositivo |
| Sin umbrales | `limitmode=0` o sin `LimitMaxError` | Definir límites de alerta |
| Sensor pausado | Pausa sin justificación documentada | Verificar o eliminar |
| Usuario alto riesgo | Cuenta admin o heredada | Revisar contraseñas y roles |
| Notificación inactiva | Sin disparador o desactivada | Activar o documentar excepción |

## Seguridad

> ⚠️ Nunca subas credenciales al repositorio. Usa variables de entorno o un archivo `.env` (ya incluido en `.gitignore`).

```bash
export PRTG_HOST=https://prtg.empresa.com
export PRTG_USER=auditor
export PRTG_PASSHASH=1234567890

python scripts/prtg_audit.py \
  --host $PRTG_HOST \
  --user $PRTG_USER \
  --passhash $PRTG_PASSHASH
```

## Referencias API PRTG

- [HTTP API Manual](https://www.paessler.com/manuals/prtg/http_api)
- [My Account / Passhash](https://www.paessler.com/manuals/prtg/my_account)
