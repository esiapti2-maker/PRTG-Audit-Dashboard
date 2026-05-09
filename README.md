# PRTG Audit Dashboard

Herramienta de auditoría interna para instancias PRTG Network Monitor.
Genera reportes CSV con hallazgos de seguridad y operación listos para revisión.

---

## Estructura del Proyecto

Arquitectura **Híbrida Tipo + Feature** — combina la claridad de capas con la escalabilidad por funcionalidades:

```
PRTG-Audit-Dashboard/
├── src/
│   ├── core/                   # Lógica de negocio compartida
│   │   ├── client.py           #   Cliente HTTP para la API REST de PRTG
│   │   ├── auth.py             #   Manejo de autenticación (password / passhash)
│   │   └── exceptions.py       #   Excepciones personalizadas
│   │
│   ├── features/               # Módulos independientes por funcionalidad
│   │   ├── devices/
│   │   │   └── audit.py        #   Inventario de dispositivos
│   │   ├── sensors/
│   │   │   └── audit.py        #   Down, Warning, Sin umbrales, Pausados
│   │   ├── users/
│   │   │   └── audit.py        #   Usuarios y permisos
│   │   └── notifications/
│   │       └── audit.py        #   Alertas activas vs pausadas
│   │
│   └── shared/                 # Código reutilizable por toda la app
│       ├── exporter.py         #   Exportación a CSV
│       └── logger.py           #   Resúmenes y mensajes de consola
│
├── scripts/
│   └── prtg_audit.py           # Entry point CLI (orquestador)
│
├── dashboard/
│   └── prtg-audit-dashboard.html  # Dashboard interactivo (HTML)
│
├── .env.example                # Plantilla de variables de entorno
├── .gitignore
├── requirements.txt
└── README.md
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
# Con passhash (recomendado — Setup → My Account → Passhash en PRTG)
python scripts/prtg_audit.py \
  --host https://prtg.empresa.com \
  --user admin \
  --passhash TU_PASSHASH \
  --site-name Guadalajara \
  --output ./reportes

# Con contraseña en texto plano
python scripts/prtg_audit.py \
  --host https://prtg.empresa.com \
  --user admin \
  --pass MiPassword \
  --site-name Monterrey
```

### Auditoría multi-sitio

Edita la sección `SITES = [...]` en `scripts/prtg_audit.py` y ejecuta:

```bash
python scripts/prtg_audit.py --multi-site --output ./reportes
```

---

## Módulos de Auditoría

| Feature | Archivo | Hallazgo |
|---|---|---|
| **Dispositivos** | `features/devices/audit.py` | Inventario completo |
| **Sensores Down/Warning** | `features/sensors/audit.py` | CRÍTICO / ADVERTENCIA |
| **Sensores sin umbrales** | `features/sensors/audit.py` | RIESGO silencioso |
| **Sensores pausados** | `features/sensors/audit.py` | REVISIÓN >30 días |
| **Usuarios** | `features/users/audit.py` | Contraseñas por defecto |
| **Notificaciones** | `features/notifications/audit.py` | Alertas pausadas |

---

## Reporte CSV

Cada ejecución genera: `reports/prtg_audit_{sitio}_{YYYYMMDD_HHMMSS}.csv`

| Columna | Descripción |
|---|---|
| `sitio` | Nombre del sitio auditado |
| `tipo` | Categoría del hallazgo |
| `id` | ID del objeto en PRTG |
| `nombre` | Nombre del sensor/dispositivo |
| `dispositivo_host` | IP o hostname del dispositivo |
| `grupo` | Grupo o ubicación en PRTG |
| `estado` | Estado actual |
| `mensaje` | Mensaje de PRTG |
| `prioridad` | Prioridad configurada (1-5) |
| `ultimo_valor` | Último valor registrado |
| `hallazgo` | Descripción del hallazgo para auditoría |

---

## Extender el Proyecto

Para agregar un nuevo módulo de auditoría (ej. `groups`):

```
src/features/groups/
├── __init__.py
└── audit.py      ← clase GroupAudit con método run()
```

Luego importarlo en `scripts/prtg_audit.py` y agregarlo al orquestador `run_audit()`.

---

## Seguridad

- Usar **passhash** en lugar de contraseña en texto plano
- El `.gitignore` excluye archivos `.env`, reportes CSV y credenciales
- Las llamadas a la API usan `verify=False` para PRTG con certificados auto-firmados
