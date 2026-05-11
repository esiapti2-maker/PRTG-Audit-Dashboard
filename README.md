# PRTG Audit Dashboard

Herramienta de auditoría para entornos PRTG Network Monitor. Incluye un script Python para extracción automatizada de datos vía API y un dashboard HTML interactivo para visualización y análisis de los resultados.

---

## Estructura del proyecto

```
PRTG-Audit-Dashboard/
├── prtg-audit-dashboard.html   ← Dashboard HTML interactivo (sin dependencias externas)
├── scripts/
│   └── prtg_audit.py           ← Script Python de auditoría vía API PRTG
├── src/
│   ├── core/                   ← Módulos base reutilizables
│   ├── features/               ← Módulos por funcionalidad
│   └── shared/                 ← Utilidades compartidas
├── requirements.txt
├── .env.example
└── .gitignore
```

---

## Opción 1 — Dashboard HTML interactivo

El archivo `prtg-audit-dashboard.html` es un dashboard standalone (sin dependencias de servidor ni npm). Abre directamente en el navegador o sirve con cualquier servidor estático.

### Características

- **Carga de CSV**: Importa los reportes generados por `prtg_audit.py` directamente desde el navegador
- **KPIs en tiempo real**: Total de dispositivos, sensores Down/Warning, pausados, sin umbrales
- **Gráficos interactivos**: Distribución por estado, sensores críticos por sitio, tendencia de alertas
- **Tabla filtrable**: Búsqueda y filtros por estado, sitio y tipo de sensor
- **Exportación**: Descarga el resultado filtrado como nuevo CSV
- **Modo oscuro / claro**: Toggle manual + respeta preferencia del sistema
- **100% offline**: No requiere internet ni dependencias externas

### Uso

```bash
# Opción A — abrir directamente
open prtg-audit-dashboard.html

# Opción B — servir localmente (evita restricciones CORS en algunos navegadores)
python3 -m http.server 8080
# Luego abre: http://localhost:8080/prtg-audit-dashboard.html
```

**Flujo de trabajo:**
1. Ejecuta `prtg_audit.py` para generar el CSV de auditoría (ver Opción 2)
2. Abre `prtg-audit-dashboard.html` en el navegador
3. Usa el botón **"Cargar CSV"** para importar el reporte
4. Filtra, analiza y exporta los resultados

### Estructura del CSV esperado

El dashboard espera el formato de salida de `prtg_audit.py`:

| Campo | Descripción |
|-------|-------------|
| `site` | Nombre del sitio / instancia PRTG |
| `device` | Nombre del dispositivo |
| `sensor` | Nombre del sensor |
| `status` | Estado: `Down`, `Warning`, `Up`, `Paused`, `Unknown` |
| `type` | Tipo de sensor |
| `last_value` | Último valor registrado |
| `has_threshold` | `True` / `False` |
| `paused_reason` | Razón de pausa (si aplica) |
| `timestamp` | Fecha/hora de la auditoría |

---

## Opción 2 — Script Python de auditoría

`scripts/prtg_audit.py` extrae datos directamente de la API REST de PRTG y genera reportes CSV estructurados.

### Requisitos

```bash
pip install -r requirements.txt
# Dependencias: requests>=2.31.0
```

### Configuración

Copia `.env.example` a `.env` y configura tus credenciales:

```bash
cp .env.example .env
```

```env
PRTG_HOST=https://prtg.tu-empresa.com
PRTG_USER=auditor
PRTG_PASSHASH=TU_PASSHASH_AQUI
PRTG_SITE_NAME=Guadalajara
```

> **Passhash**: Ve a *Setup → My Account → Passhash* en tu instancia PRTG. Es más seguro que usar la contraseña en texto plano.

### Uso básico

```bash
# Auditoría de un sitio
python scripts/prtg_audit.py \
  --host https://prtg.tu-empresa.com \
  --user auditor \
  --passhash TU_PASSHASH \
  --site-name Guadalajara \
  --output ./reportes

# Todos los módulos disponibles
python scripts/prtg_audit.py \
  --host https://prtg.empresa.com \
  --user admin \
  --passhash HASH \
  --site-name "Sitio Principal" \
  --modules inventory sensors_down sensors_warning no_threshold paused users notifications
```

### Módulos de auditoría disponibles

| Módulo | Descripción |
|--------|-------------|
| `inventory` | Inventario completo de dispositivos y sensores |
| `sensors_down` | Sensores en estado Down |
| `sensors_warning` | Sensores en estado Warning |
| `no_threshold` | Sensores activos sin umbrales configurados |
| `paused` | Sensores pausados (con razón de pausa) |
| `users` | Usuarios y permisos configurados |
| `notifications` | Reglas y canales de notificación |

### Multi-sitio

```python
from scripts.prtg_audit import run_multi_site_audit

sites = [
    {"host": "https://prtg-gdl.empresa.com", "user": "admin", "passhash": "HASH1", "site_name": "Guadalajara"},
    {"host": "https://prtg-mty.empresa.com", "user": "admin", "passhash": "HASH2", "site_name": "Monterrey"},
    {"host": "https://prtg-cdmx.empresa.com", "user": "admin", "passhash": "HASH3", "site_name": "CDMX"},
]

run_multi_site_audit(sites, output_dir="./reportes")
```

### Output

Los reportes se generan en el directorio especificado:

```
reportes/
└── prtg_audit_Guadalajara_20260511_120000.csv
```

Abre el CSV resultante en `prtg-audit-dashboard.html` para visualización interactiva.

---

## Checklist de auditoría PRTG

- [ ] Sensores Down sin ticket de incidente activo
- [ ] Sensores en Warning por más de 24 horas
- [ ] Sensores sin umbrales configurados (riesgo de alertas silenciosas)
- [ ] Sensores pausados sin razón documentada
- [ ] Usuarios con permisos de administrador sin justificación
- [ ] Canales de notificación sin destinatarios activos
- [ ] Dispositivos sin sensores asignados

---

## Seguridad

- El archivo `.env` está incluido en `.gitignore` — **nunca lo subas al repo**
- Los reportes CSV también están excluidos del repositorio por `.gitignore`
- Usa siempre `passhash` en lugar de contraseña en texto plano
- Revoca y rota el passhash periódicamente desde *Setup → My Account*

---

## Licencia

MIT — Libre para uso interno en entornos corporativos.
