# PRTG Audit Dashboard

Herramienta de auditoría interna para servidores **PRTG Network Monitor**.
Genera reportes CSV detallados sobre el estado de dispositivos, sensores, usuarios y notificaciones.

---

## Estructura del proyecto

Estructura **Híbrida: Tipo + Feature** — combina claridad por capas con escalabilidad por funcionalidades.

```
PRTG-Audit-Dashboard/
│
├── scripts/
│   └── prtg_audit.py        ← CLI entry point (orquestador)
│
├── src/
│   ├── core/                ← Lógica compartida de infraestructura
│   │   ├── client.py        ← Cliente HTTP para la API de PRTG
│   │   ├── constants.py     ← Constantes, endpoints, columnas
│   │   └── exceptions.py    ← Jerarquía de excepciones
│   │
│   ├── features/            ← Módulos independientes por funcionalidad
│   │   ├── devices/
│   │   │   ├── audit.py     ← Inventario de dispositivos
│   │   │   └── types.py     ← TypedDict para DeviceRecord
│   │   ├── sensors/
│   │   │   ├── audit.py     ← Down / Warning / Sin umbrales / Pausados
│   │   │   └── types.py
│   │   ├── users/
│   │   │   ├── audit.py     ← Listado de cuentas y permisos
│   │   │   └── types.py
│   │   └── notifications/
│   │       ├── audit.py     ← Alertas activas vs pausadas
│   │       └── types.py
│   │
│   └── shared/              ← Código reutilizable por todos los features
│       ├── exporter.py      ← Exportador CSV multi-sección
│       └── logger.py        ← Logger de consola
│
├── prtg-audit-dashboard.html  ← Dashboard visual (HTML standalone)
├── requirements.txt
├── .env.example
└── .gitignore
```

---

## Instalación

```bash
git clone https://github.com/esiapti2-maker/PRTG-Audit-Dashboard
cd PRTG-Audit-Dashboard
pip install -r requirements.txt
```

---

## Uso

### Auditoría de un solo sitio

```bash
# Con passhash (recomendado — Setup → My Account → Passhash)
python scripts/prtg_audit.py \
  --host https://prtg.empresa.com \
  --user admin \
  --passhash TU_PASSHASH \
  --site-name "Guadalajara" \
  --output ./reportes

# Con contraseña en texto plano
python scripts/prtg_audit.py \
  --host https://prtg.empresa.com \
  --user admin \
  --pass MiPassword \
  --site-name "CDMX"
```

### Auditoría multi-sitio

Edita la lista `SITES` en `scripts/prtg_audit.py`:

```python
SITES = [
    {
        "name":     "Guadalajara",
        "host":     "https://prtg-gdl.empresa.com",
        "username": "auditor",
        "passhash": "1234567890",
    },
    {
        "name":     "CDMX-DR",
        "host":     "https://prtg-cdmx.empresa.com",
        "username": "auditor",
        "passhash": "0987654321",
    },
]
```

Luego ejecuta:

```bash
python scripts/prtg_audit.py --multi-site --output ./reportes
```

---

## Reporte CSV generado

El archivo se guarda como `prtg_audit_{sitio}_{timestamp}.csv` con las siguientes secciones:

| Sección | Descripción |
|---|---|
| `INVENTARIO` | Todos los dispositivos y su estado actual |
| `SENSOR DOWN` | Sensores caídos con mensaje de error |
| `SENSOR WARNING` | Sensores en estado de advertencia |
| `SIN UMBRALES` | Sensores sin límites configurados |
| `SENSOR PAUSADO` | Sensores pausados manualmente o por horario |
| `USUARIO` | Cuentas de usuario activas y sus grupos |
| `NOTIF PAUSADA` | Notificaciones/alertas desactivadas |

---

## Extender con un nuevo feature

1. Crear carpeta `src/features/mi_feature/`
2. Agregar `audit.py` con clase `MiFeatureAudit(client).run()` → retorna `list[dict]`
3. Agregar `types.py` con `TypedDict` del resultado
4. Importar y llamar desde `scripts/prtg_audit.py`
5. Agregar método `add_mi_feature()` en `src/shared/exporter.py`

---

## Seguridad

- Usa siempre `--passhash` en lugar de `--pass` para evitar contraseñas en texto plano en el historial de shell.
- El archivo `.env.example` muestra las variables recomendadas; copia a `.env` y **nunca lo subas al repo** (está en `.gitignore`).
- Los reportes CSV también están en `.gitignore` para evitar filtrar datos de producción.
