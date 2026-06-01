# PRTG Audit Dashboard

> Herramienta de auditoría técnica para infraestructuras PRTG — hasta 14 instancias desde un solo panel.

[![License: MIT](https://img.shields.io/badge/License-MIT-teal.svg)](LICENSE)
[![Python 3.8+](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/)
[![HTML estático](https://img.shields.io/badge/Dashboard-HTML%20estático-orange.svg)](#)
[![Sin dependencias frontend](https://img.shields.io/badge/Frontend-Sin%20dependencias-green.svg)](#)

---

## ¿Qué es?

Dos herramientas complementarias para auditar configuración y estado de servidores PRTG Network Monitor:

| Herramienta | Archivo | Uso |
|---|---|---|
| **Dashboard Web** | `prtg-audit-dashboard.html` | Revisión visual, presentaciones, modo Demo |
| **Script Python** | `scripts/prtg_audit.py` | Automatización, historial CSV, multi-sitio en batch |

---

## Requisitos del sistema

### Dashboard Web

| Requisito | Mínimo | Recomendado |
|---|---|---|
| Navegador | Chrome 90+, Firefox 88+, Edge 90+ | Chrome/Edge última versión |
| Red | Acceso HTTP/HTTPS al servidor PRTG | Red interna LAN/VPN |
| PRTG | Versión 18.x o superior | PRTG 23.x+ |
| Servidor web | No requerido (abrir HTML directo) | Nginx via Docker (resolver CORS) |

### Script Python

| Requisito | Detalle |
|---|---|
| Python | 3.8 o superior |
| Dependencia | `requests >= 2.31.0` (ver `requirements.txt`) |
| Red | Acceso TCP al servidor PRTG (puerto 80/443) |
| Permisos | Solo lectura en PRTG es suficiente |

---

## Arquitectura y persistencia

**El dashboard web es 100% estático** — corre en el browser sin servidor ni base de datos. Toda la configuración (instancias, credenciales, datos cargados) vive en la RAM del navegador durante la sesión. Al cerrar o recargar la pestaña, los datos desaparecen.

```
Browser (RAM)  ──fetch──▶  API PRTG (/api/table.json)
   │
   └── Exportar CSV ──▶  Disco local (historial manual)

Script Python  ──requests──▶  API PRTG
   │
   └── CSV con timestamp ──▶  Disco (historial automático acumulado)
```

**¿Por qué dos herramientas?**
El browser tiene restricción CORS: si PRTG no permite llamadas desde el origen del dashboard, las bloqueará. El script Python no pasa por el browser y no tiene esa restricción, por lo que siempre puede conectarse directamente.

---

## Inicio rápido

### Dashboard Web

```bash
# Opción 1 — abrir directamente (red interna sin CORS)
open prtg-audit-dashboard.html

# Opción 2 — servir con Docker (resuelve CORS via proxy Nginx)
docker compose up -d
# Accede en http://localhost:8080
```

1. Ve a la sección **Instancias** en el menú lateral.
2. Haz clic en **Editar** en cualquier slot y configura: nombre, host, usuario y passhash.
3. Selecciona la instancia en el selector del sidebar.
4. Haz clic en **Conectar y auditar**.

> **¿Cómo obtener el Passhash?**
> Dentro de PRTG: clic en tu nombre de usuario (esquina superior derecha) → **My Account** → sección **API / Passhash** → copiar el valor del campo *Passhash*.
> El passhash es más seguro que la contraseña porque es un token para la API que no expone tu contraseña real.

### Script Python

```bash
pip install -r requirements.txt

python scripts/prtg_audit.py \
  --host https://tu-prtg.empresa.com \
  --user auditoria \
  --passhash TU_PASSHASH \
  --site-name "GDL Principal" \
  --output ./reportes
```

**PRTG con certificado SSL autofirmado** (común en entornos internos):
```bash
python scripts/prtg_audit.py \
  --host https://prtg.local \
  --user auditoria \
  --passhash TU_PASSHASH \
  --site-name "GDL Principal" \
  --output ./reportes \
  --no-ssl-verify
```

> ⚠️ Usar `--no-ssl-verify` solo en redes internas de confianza.

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
- Parámetros: `--host`, `--user`, `--passhash`, `--site-name`, `--output`, `--timeout`, `--no-ssl-verify`, `--modules`

---

## Parámetros del script Python

| Parámetro | Obligatorio | Descripción | Ejemplo |
|---|---|---|---|
| `--host` | ✅ | URL base de PRTG | `https://prtg.empresa.com` |
| `--user` | ✅ | Nombre de usuario | `auditoria` |
| `--passhash` | ✅ | Passhash del usuario | `ABC123...` |
| `--site-name` | ❌ | Etiqueta para el reporte | `"CDMX-DC1"` |
| `--output` | ❌ | Carpeta de salida | `./reportes` (default: `.`) |
| `--timeout` | ❌ | Segundos de espera por llamada | `30` (default) |
| `--no-ssl-verify` | ❌ | Deshabilitar verificación SSL | (flag, sin valor) |
| `--modules` | ❌ | Módulos a ejecutar separados por coma | `sensors,users` |

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

**Score = (cumplidas / 8) × 100%** — 🟢 ≥80% · 🟡 60-79% · 🔴 <60%

---

## Estructura del repositorio

```
PRTG-Audit-Dashboard/
├── prtg-audit-dashboard.html   # Dashboard web estático (HTML all-in-one)
├── scripts/
│   └── prtg_audit.py           # Script Python CLI
├── docs/
│   └── MANUAL.md               # Manual completo de usuario
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
| PRTG con certificado SSL autofirmado | Script Python con `--no-ssl-verify` |

---

## Seguridad y buenas prácticas

- ✅ Crear una cuenta PRTG de solo lectura exclusiva para auditoría (`svc_auditoria`)
- ✅ Usar el **passhash** en lugar de la contraseña — es un token de API revocable
- ✅ Usar variables de entorno para el passhash en scripts de cron (`export PRTG_PASSHASH=...`)
- ✅ Los reportes CSV y el archivo `.env` están en `.gitignore` — no se sincronizan al repo
- ❌ No hardcodear el passhash en scripts ni archivos de configuración versionados
- ❌ No compartir el passhash por Slack/Teams/email

---

## Documentación

📖 [Manual completo de usuario](docs/MANUAL.md) — Guía detallada con arquitectura, persistencia, todos los módulos de auditoría, automatización con cron, resolución de problemas y glosario técnico.

---

## Contribución

¿Encontraste un bug o tienes una mejora?

1. Abre un [Issue](https://github.com/esiapti2-maker/PRTG-Audit-Dashboard/issues) describiendo el problema o la propuesta
2. Para cambios de código: fork → rama descriptiva → PR hacia `main`
3. Para bugs: incluye versión de PRTG, navegador/Python usado y pasos para reproducir
4. Para nuevos módulos de auditoría: describe el hallazgo que detecta y el endpoint de la API de PRTG que usaría

---

## Licencia

MIT — libre para uso interno, modificación y distribución.
