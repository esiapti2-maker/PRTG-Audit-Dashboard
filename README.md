# PRTG Audit Dashboard

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://python.org)
[![PRTG](https://img.shields.io/badge/PRTG-Network%20Monitor-orange.svg)](https://www.paessler.com/prtg)

Herramienta de auditoría técnica para instancias de **PRTG Network Monitor**. Detecta brechas de configuración, sensores sin cobertura real, cuentas con privilegios excesivos y notificaciones inoperantes.

---

## Índice

- [Componentes](#componentes)
- [Inicio rápido — Dashboard Web](#inicio-rápido--dashboard-web)
- [Inicio rápido — Script Python](#inicio-rápido--script-python)
- [Módulos de auditoría](#módulos-de-auditoría)
- [¿Dónde se guardan los datos?](#dónde-se-guardan-los-datos)
- [Despliegue con Docker](#despliegue-con-docker)
- [Estructura del proyecto](#estructura-del-proyecto)
- [Seguridad](#seguridad)
- [Documentación completa](#documentación-completa)

---

## Componentes

| Archivo | Descripción | Cuándo usar |
|---|---|---|
| `prtg-audit-dashboard.html` | Dashboard web interactivo, sin instalación | Revisión visual, presentaciones, demo |
| `scripts/prtg_audit.py` | Script CLI para automatización y multi-sitio | Cron, multi-sitio, redes con CORS |

---

## Inicio rápido — Dashboard Web

1. Descargar o clonar el repositorio
2. Abrir `prtg-audit-dashboard.html` en el navegador (doble clic, sin servidor)
3. Ingresar la URL de tu PRTG, usuario y **passhash**
4. Presionar **"Ejecutar Auditoría"**
5. Exportar el reporte con **"Exportar CSV"**

> **¿Cómo obtener el passhash?**  
> PRTG → tu usuario (esquina superior derecha) → **My Account** → sección **API** → copiar el valor *Passhash*

> **Nota sobre CORS:** Si el browser bloquea la conexión a PRTG, usa el script Python o el [proxy Docker incluido](#despliegue-con-docker).

---

## Inicio rápido — Script Python

```bash
git clone https://github.com/esiapti2-maker/PRTG-Audit-Dashboard.git
cd PRTG-Audit-Dashboard
pip install -r requirements.txt

python scripts/prtg_audit.py \
  --host https://tu-prtg.empresa.com \
  --user auditoria \
  --passhash TU_PASSHASH \
  --site-name Guadalajara \
  --output ./reportes
```

Genera: `./reportes/prtg_audit_Guadalajara_20260511_170000.csv`

**Parámetros principales:**

| Parámetro | Descripción |
|---|---|
| `--host` | URL base de PRTG (con protocolo) |
| `--user` | Nombre de usuario PRTG |
| `--passhash` | Passhash del usuario (no la contraseña) |
| `--site-name` | Etiqueta del sitio para el reporte |
| `--output` | Carpeta donde guardar el CSV |
| `--no-ssl-verify` | Deshabilitar SSL (para certs autofirmados) |
| `--timeout` | Segundos de espera por llamada (default: 30) |

---

## Módulos de auditoría

| Módulo | Qué detecta |
|---|---|
| **Inventario general** | Total de dispositivos y sensores, distribución de estados, dispositivos sin sensores |
| **Sensores Down/Warning** | Alertas activas y tiempo sin atender |
| **Sensores sin umbrales** | Sensores que nunca alertarán aunque el valor sea anómalo |
| **Sensores pausados** | Puntos ciegos por pausas crónicas (>7 y >30 días) |
| **Usuarios y privilegios** | Clasificación de riesgo por nivel de acceso y actividad reciente |
| **Notificaciones** | Plantillas inactivas, sin disparador o sin método de entrega |

---

## ¿Dónde se guardan los datos?

**Dashboard Web:** Los datos viven únicamente en la RAM del browser durante la sesión activa. Al cerrar o recargar, se pierden. El único mecanismo de persistencia es el botón **"Exportar CSV"**.

**Script Python:** Genera un nuevo archivo CSV con timestamp en cada ejecución, acumulando un historial en la carpeta `--output`. El script y el HTML nunca crecen — solo los reportes exportados.

```
./reportes/
├── prtg_audit_Guadalajara_20260509_070000.csv
├── prtg_audit_Guadalajara_20260510_070000.csv
└── prtg_audit_Guadalajara_20260511_070000.csv  ← historial acumulado
```

---

## Despliegue con Docker

El repo incluye un proxy Nginx que resuelve errores CORS al abrir el dashboard en un servidor:

```bash
# Copiar y editar variables de entorno
cp .env.example .env
nano .env  # configurar PRTG_HOST, PRTG_USER, PRTG_PASSHASH

# Levantar el servicio
docker-compose up -d

# Acceder al dashboard
open http://localhost:8080
```

---

## Estructura del proyecto

```
PRTG-Audit-Dashboard/
├── prtg-audit-dashboard.html   ← Dashboard web (abrir directamente)
├── scripts/
│   └── prtg_audit.py           ← Script Python CLI
├── docs/
│   └── MANUAL.md               ← Manual completo de usuario
├── proxy/                      ← Configuración Nginx para Docker
├── src/                        ← Fuentes y assets adicionales
├── requirements.txt            ← Solo: requests>=2.31.0
├── Dockerfile
├── docker-compose.yml
├── .env.example                ← Plantilla de variables de entorno
└── .gitignore                  ← Excluye .env, *.csv, reportes/
```

---

## Seguridad

- Usar cuenta PRTG de **solo lectura** exclusiva para auditoría (`svc_auditoria`)
- El passhash **nunca se guarda** en el repositorio (incluido en `.gitignore`)
- Los reportes CSV tampoco se sincronizan al repo
- El aplicativo es **100% de solo lectura** — no modifica ninguna configuración de PRTG
- No envía datos a servidores externos

---

## Documentación completa

Consulta el **[Manual de Usuario](docs/MANUAL.md)** para:

- Arquitectura detallada de los dos componentes
- Cómo funciona el almacenamiento de datos (RAM vs disco)
- Configuración multi-sitio y auditoría de toda la infraestructura
- Automatización con cron jobs
- Resolución de problemas (CORS, SSL, permisos, Excel)
- Interpretación del score de auditoría y checklist de 8 puntos
- Glosario técnico (Passhash, Umbral, CORS, etc.)

---

> Desarrollado para infraestructura enterprise con PRTG Network Monitor
