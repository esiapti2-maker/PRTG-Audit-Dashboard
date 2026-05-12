# PRTG Audit Dashboard

> Herramienta de auditoría técnica para infraestructuras PRTG — hasta 14 instancias desde un solo panel.

[![License: MIT](https://img.shields.io/badge/License-MIT-teal.svg)](LICENSE)
[![Python 3.8+](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/)
[![HTML estático](https://img.shields.io/badge/Dashboard-HTML%20est%C3%A1tico-orange.svg)](#)

---

## ¿Qué es?

Dos herramientas complementarias para auditar configuración y estado de servidores PRTG:

| Herramienta | Archivo | Uso |  
|---|---|---|
| **Dashboard Web** | `prtg-audit-dashboard.html` | Revisión visual, presentaciones, modo Demo |
| **Script Python** | `scripts/prtg_audit.py` | Automatización, historial CSV, multi-sitio en batch |

---

## Arquitectura y persistencia

**El dashboard web es 100% estático** — corre en el browser sin servidor ni base de datos. Toda la configuración (instancias, credenciales, datos cargados) vive en la RAM del navegador durante la sesión. Al cerrar o recargar la pestaña, los datos desaparecen.

```
Browser (RAM)  ──fetch──▶  API PRTG (/api/table.json)
   │
   └── Exportar CSV ──▶  Disco local (historial manual)

Script Python  ──requests──▶  API PRTG
   │
   └── CSV con timestamp ──▶  Disco (historial automático)
```

**¿Por qué dos herramientas?**  
El browser tiene restricción CORS: si PRTG no permite llamadas desde el origen del dashboard, las bloqueará. El script Python no pasa por el browser y no tiene esa restricción, por lo que siempre puede conectarse directamente.

---

## Inicio rápido

### Dashboard Web

```bash
# Opción 1 — abrir directamente (red interna sin CORS)
open prtg-audit-dashboard.html

# Opción 2 — servir con Docker
docker compose up -d
# Accede en http://localhost:8080
```

1. Ve a la sección **Instancias** en el menú lateral.
2. Haz clic en **Editar** en cualquier slot y configura: nombre, host, usuario y passhash.
3. Selecciona la instancia en el selector del sidebar.
4. Haz clic en **Conectar y auditar**.

> El passhash se obtiene en PRTG: *Setup → My Account → Passhash*.

### Script Python

```bash
pip install -r requirements.txt

python scripts/prtg_audit.py \
  --host https://tu-prtg.empresa.com \
  --user auditor \
  --passhash TU_PASSHASH \
  --site-name "GDL Principal" \
  --output ./reportes
```

---

## Funcionalidades

### Dashboard Web

- **Gestión de hasta 14 instancias** — slots configurables con nombre, host, usuario y passhash
- **KPIs en tiempo real** — dispositivos, sensores OK/Down, sin umbrales, score de auditoría 0-100%
- **Tabla de sensores** — filtro por estado y búsqueda de texto libre en tiempo real
- **Detección de sensores sin umbrales** — sensores con `limitmode=0` que nunca generarán alertas
- **Clasificación de riesgo de usuarios** — Alto / Medio / Bajo según tipo de cuenta
- **Revisión de notificaciones** — plantillas inactivas o sin disparador configurado
- **Checklist automático** — 8 verificaciones con score final
- **Modo Demo** — datos de ejemplo sin necesitar acceso a PRTG
- **Exportar CSV** — evidencia descargable con todos los hallazgos y el checklist
- **Tema claro/oscuro** — toggle manual + respeta `prefers-color-scheme`

### Script Python

- Auditoría desde CLI sin restricción CORS
- Exporta CSV con timestamp por instancia (historial acumulable)
- Soporte multi-sitio via archivo JSON de configuración
- Compatible con cron para auditorías programadas
- Parámetros: `--host`, `--user`, `--passhash`, `--site-name`, `--output`, `--no-verify-ssl`

---

## Checklist de auditoría — 8 verificaciones

| # | Verificación | Criterio |
|---|---|---|
| 1 | Sin sensores en estado Down | 0 sensores Down |
| 2 | Warnings controlados | < 5 sensores Warning |
| 3 | Sin sensores sin umbrales | 0 sensores sin `LimitMaxError` |
| 4 | Sin sensores pausados | 0 sensores Pausados |
| 5 | Todas las notificaciones activas | 0 plantillas inactivas |
| 6 | Sin usuarios de alto riesgo | 0 cuentas Admin no controladas |
| 7 | Inventario poblado | Al menos 1 dispositivo |
| 8 | Cobertura mínima | Al menos 5 sensores |

**Score = (cumplidas / 8) × 100%** — verde ≥80%, naranja 60-79%, rojo <60%

---

## Estructura del repositorio

```
PRTG-Audit-Dashboard/
├── prtg-audit-dashboard.html   # Dashboard web estático (HTML all-in-one)
├── scripts/
│   └── prtg_audit.py           # Script Python CLI
├── docs/
│   └── manual.md               # Manual completo de usuario
├── proxy/                      # Config Nginx (resolver CORS con Docker)
├── Dockerfile
├── docker-compose.yml
├── requirements.txt            # requests>=2.31.0
├── .env.example                # Plantilla de variables de entorno
└── .gitignore                  # Excluye reportes CSV y archivos .env
```

---

## CORS — Cuándo usar cada herramienta

| Escenario | Herramienta recomendada |
|---|---|
| Browser en red interna, PRTG accesible directamente | Dashboard Web |
| Browser con error "CORS policy" | Script Python |
| Auditoría programada / cron | Script Python |
| Demo sin acceso a PRTG | Dashboard Web (modo Demo) |
| Presentación de hallazgos | Dashboard Web + Exportar CSV |

---

## Documentación

📖 [Manual completo de usuario](docs/manual.md) — Guía detallada con arquitectura, persistencia, todos los módulos, automatización con cron, resolución de problemas y glosario técnico.

---

## Licencia

MIT — libre para uso interno, modificación y distribución.
