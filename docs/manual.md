# Manual de Usuario — PRTG Audit Dashboard

> Versión 1.0 · Mayo 2026  
> Repositorio: [esiapti2-maker/PRTG-Audit-Dashboard](https://github.com/esiapti2-maker/PRTG-Audit-Dashboard)

---

## Índice

1. [Arquitectura del sistema](#1-arquitectura-del-sistema)
2. [¿Dónde se guarda la configuración?](#2-dónde-se-guarda-la-configuración)
3. [Componentes del aplicativo](#3-componentes-del-aplicativo)
4. [Dashboard Web — Guía completa](#4-dashboard-web--guía-completa)
   - 4.1 [Primera vez — Configurar instancias](#41-primera-vez--configurar-instancias)
   - 4.2 [Conectar y auditar](#42-conectar-y-auditar)
   - 4.3 [Modo Demo](#43-modo-demo)
   - 4.4 [Sección Sensores](#44-sección-sensores)
   - 4.5 [Sección Umbrales](#45-sección-umbrales)
   - 4.6 [Sección Usuarios](#46-sección-usuarios)
   - 4.7 [Sección Notificaciones](#47-sección-notificaciones)
   - 4.8 [Checklist automático](#48-checklist-automático)
   - 4.9 [Exportar CSV](#49-exportar-csv)
5. [Script Python — Guía completa](#5-script-python--guía-completa)
   - 5.1 [Instalación](#51-instalación)
   - 5.2 [Uso básico](#52-uso-básico)
   - 5.3 [Auditoría multi-sitio](#53-auditoría-multi-sitio)
   - 5.4 [Automatización con cron](#54-automatización-con-cron)
6. [CORS — Por qué y cuándo usar cada herramienta](#6-cors--por-qué-y-cuándo-usar-cada-herramienta)
7. [Despliegue con Docker](#7-despliegue-con-docker)
8. [Glosario técnico](#8-glosario-técnico)
9. [Solución de problemas](#9-solución-de-problemas)

---

## 1. Arquitectura del sistema

El proyecto se compone de **dos herramientas independientes** que atacan el mismo objetivo desde ángulos distintos:

```
┌────────────────────────────────────────────────────────────────┐
│                   PRTG Audit Dashboard                         │
│                                                                │
│  ┌──────────────────────────┐   ┌──────────────────────────┐  │
│  │   Dashboard Web          │   │   Script Python          │  │
│  │   (HTML estático)        │   │   (CLI / cron)           │  │
│  │                          │   │                          │  │
│  │ • Corre en el browser    │   │ • Corre en terminal      │  │
│  │ • Sin instalación        │   │ • Sin restricción CORS   │  │
│  │ • UI visual / auditoria  │   │ • Exporta CSV a disco    │  │
│  │ • Estado en RAM (sesión) │   │ • Historial acumulable   │  │
│  │ • Hasta 14 instancias    │   │ • Multi-sitio en batch   │  │
│  └────────────┬─────────────┘   └────────────┬─────────────┘  │
│               │                              │                 │
│               └──────────────┬───────────────┘                 │
│                              ▼                                 │
│                    API PRTG (JSON)                             │
│               /api/table.json?content=...                      │
└────────────────────────────────────────────────────────────────┘
```

---

## 2. ¿Dónde se guarda la configuración?

Esta es la pregunta más común al usar el aplicativo por primera vez.

### Dashboard Web

El dashboard es un archivo **HTML estático** — no tiene servidor, no tiene base de datos, no escribe ningún archivo. Todo lo que capturas en los formularios (host, usuario, passhash, nombres de instancias) vive únicamente en la **memoria RAM del navegador** durante esa sesión.

| Momento | ¿Qué pasa con los datos? |
|---|---|
| Abrir el archivo / URL | Se cargan los 5 slots pre-configurados por defecto (sin credenciales) |
| Configurar una instancia | Los datos se guardan en una variable JavaScript en memoria |
| Cargar datos de PRTG | El resultado se almacena en la variable `state` en RAM |
| Cerrar o recargar la pestaña | **Todo se pierde** — vuelves a los valores por defecto |
| Exportar CSV | Los hallazgos se descargan a tu disco antes de que se pierdan |

**¿Qué hacer si quieres persistencia?**

- Usa el **botón Exportar CSV** antes de cerrar para guardar los hallazgos en disco.
- Usa el **script Python** que sí escribe un archivo `.csv` con timestamp en cada ejecución, creando historial acumulado.
- Si desplegas el dashboard vía **Docker + Nginx** (incluido en el repo), podrías agregar un proxy con sesiones persistentes — pero en su forma base, la configuración no persiste.

### Script Python

El script sí guarda resultados en disco. Cada ejecución crea un CSV nuevo con timestamp:

```
reportes/
├── prtg_audit_GDL-Principal_20260509_143022.csv
├── prtg_audit_GDL-Principal_20260512_080000.csv
├── prtg_audit_MTY_20260509_143045.csv
└── prtg_audit_MTY_20260512_080012.csv
```

Esto te da **historial acumulado** por instancia y por fecha. El directorio de salida lo controlas con `--output`.

---

## 3. Componentes del aplicativo

| Componente | Archivo | Cuándo usarlo |
|---|---|---|
| **Dashboard Web** | `prtg-audit-dashboard.html` | Revisión visual rápida, presentar en reunión, explorar con modo Demo sin PRTG |
| **Script Python** | `scripts/prtg_audit.py` | Automatizar con cron, historial de reportes, multi-sitio en batch, cuando el browser da error CORS |
| **Dockerfile + Compose** | `Dockerfile`, `docker-compose.yml` | Servir el dashboard vía Nginx en red interna sin abrir el HTML directamente |
| **Variables de entorno** | `.env.example` | Plantilla para definir credenciales sin escribirlas en el código |

---

## 4. Dashboard Web — Guía completa

### 4.1 Primera vez — Configurar instancias

Al abrir el dashboard por primera vez verás **5 slots pre-nombrados** (GDL Principal, MTY, CDMX, DR Site, Planta Norte) y **9 slots vacíos**. Ninguno tiene host ni credenciales — solo nombres de referencia.

**Pasos para configurar tu primera instancia:**

1. Ve a la sección **Instancias** (menú lateral izquierdo).
2. Haz clic en **Editar** (ícono de lápiz) en el slot que quieras configurar, o en **Configurar** en un slot vacío.
3. En el modal que aparece, completa:
   - **Nombre del sitio** — identificador libre (ej: `Guadalajara NOC`)
   - **Host PRTG** — URL completa con protocolo (ej: `https://prtg.empresa.com`)
   - **Usuario API** — el usuario de PRTG con acceso a la API
   - **Passhash o API token** — obtenido desde *PRTG → Setup → My Account → Passhash*
4. Haz clic en **Guardar**.
5. Repite para las demás instancias que necesites.

> **Nota sobre el passhash:** Es preferible al password en texto plano porque está hasheado. Lo encuentras en PRTG en *Setup → My Account → Passhash*. También puedes usar un API token si tu versión de PRTG lo soporta.

**Capacidad máxima:** 14 instancias simultáneas. La barra de progreso en el sidebar y en la sección Instancias muestra cuántos slots están en uso.

### 4.2 Conectar y auditar

1. En el **selector del sidebar** (`Instancia activa`), elige la instancia que quieres auditar.
2. Los campos de Host y Usuario se llenan automáticamente.
3. Si el passhash no estaba guardado, ingrésalo en el campo correspondiente.
4. Haz clic en **Conectar y auditar** (o en el botón **Auditar instancia** del header).
5. El dashboard hace **4 llamadas paralelas** a la API de PRTG:
   - `content=sensors` — todos los sensores
   - `content=devices` — inventario de dispositivos
   - `content=users` — usuarios y permisos
   - `content=notifications` — plantillas de notificación
6. Los datos se procesan y se llenan todos los KPIs, tablas y el checklist.

### 4.3 Modo Demo

El botón **Demo** (o **Cargar demo**) carga un conjunto de datos de ejemplo sin necesitar acceso a PRTG. Útil para:

- Mostrar el dashboard en una presentación sin exponer credenciales.
- Explorar todas las funcionalidades antes de tener acceso a producción.
- Verificar que el dashboard funciona correctamente.

Los datos demo incluyen sensores en todos los estados (OK, Warning, Down, Pausado), usuarios con diferentes niveles de riesgo y notificaciones con hallazgos.

### 4.4 Sección Sensores

Muestra todos los sensores de la instancia activa con:

| Columna | Descripción |
|---|---|
| Sensor | Nombre del sensor en PRTG |
| Dispositivo | Nombre del host/device asociado |
| Grupo | Grupo padre en la jerarquía PRTG |
| Estado | Badge visual: OK / Warning / Down / Pausado |
| Último valor | Último valor medido por el sensor |
| Mensaje | Mensaje de estado actual |

**Filtros disponibles:**
- **Por estado** — dropdown: Todos / OK / Warning / Down / Pausado
- **Búsqueda de texto** — busca en nombre del sensor, dispositivo, grupo y mensaje simultáneamente

### 4.5 Sección Umbrales

Muestra los sensores que **no tienen umbrales configurados** (`limitmode=0` o sin `LimitMaxError` definido).

> **¿Por qué es crítico?** Un sensor sin umbral nunca generará una alerta aunque su valor sea completamente anómalo. Por ejemplo, un sensor de CPU al 100% sin umbral jamás disparará una notificación.

Este es uno de los **hallazgos de mayor impacto** en auditorías PRTG — organizaciones con cientos de sensores suelen tener una fracción significativa sin umbrales definidos.

### 4.6 Sección Usuarios

Muestra todos los usuarios del sistema con una clasificación de riesgo automática:

| Riesgo | Criterio de clasificación |
|---|---|
| **Alto** | Nombre contiene `admin` (cuentas administrativas) |
| **Medio** | Tipo `Read/Write` (acceso de escritura sin ser admin) |
| **Bajo** | Tipo `Read Only` (solo lectura) |

> **Hallazgo típico:** Múltiples cuentas `Admin` activas, cuentas sin email asociado (dificulta la trazabilidad), cuentas de servicio con permisos excesivos.

### 4.7 Sección Notificaciones

Revisar las plantillas de notificación y su estado:

| Columna | Descripción |
|---|---|
| Nombre | Nombre de la plantilla |
| Activa | Badge verde/rojo según si está habilitada |
| Trigger | Tipo de disparador configurado |
| Hallazgo | Evaluación automática |

> **Hallazgo típico:** Plantillas inactivas que nadie desactivó intencionalmente, o plantillas sin disparador configurado que nunca enviarán alertas.

### 4.8 Checklist automático

Ocho verificaciones automáticas que generan un score de 0 a 100%:

| # | Verificación | Criterio para "Cumple" |
|---|---|---|
| 1 | Sin sensores en estado Down | 0 sensores Down |
| 2 | Warnings controlados | Menos de 5 sensores en Warning |
| 3 | Sin sensores sin umbrales | 0 sensores sin `LimitMaxError` |
| 4 | Sin sensores pausados sin justificación | 0 sensores Pausados |
| 5 | Todas las notificaciones activas | 0 plantillas inactivas |
| 6 | Sin usuarios de alto riesgo | 0 usuarios clasificados como Alto riesgo |
| 7 | Inventario de dispositivos poblado | Al menos 1 dispositivo |
| 8 | Cobertura mínima de sensores | Al menos 5 sensores |

**Score = (verificaciones que cumplen / 8) × 100%**

- 80–100% → Verde (buena configuración)
- 60–79% → Naranja (requiere atención)
- 0–59% → Rojo (hallazgos críticos pendientes)

### 4.9 Exportar CSV

El botón **Exportar CSV** descarga un archivo con todos los hallazgos actuales, incluyendo:

- Todos los sensores con su estado
- Sensores sin umbrales
- Usuarios con su nivel de riesgo
- Notificaciones y su estado
- Resultado del checklist completo

El archivo se nombra automáticamente:
```
prtg-audit-gdl-principal-2026-05-12.csv
```

**Columnas del CSV:**

| tipo | nombre | dispositivo | grupo | estado | valor | mensaje_hallazgo |
|---|---|---|---|---|---|---|
| sensor | Ping Core SW | core-sw-01 | Campus GDL | up | 1 ms | OK |
| sin_umbral | CPU VMware | esxi-01 | Virtualización | 0 | 91% | Sin LimitMaxError configurado |
| usuario | prtgadmin | | | Admin | | Alto riesgo |
| checklist | Sin sensores Down | | | revisar | | Requiere atención |

---

## 5. Script Python — Guía completa

### 5.1 Instalación

```bash
# Clonar el repositorio
git clone https://github.com/esiapti2-maker/PRTG-Audit-Dashboard.git
cd PRTG-Audit-Dashboard

# Instalar dependencias (solo una: requests)
pip install -r requirements.txt
```

**Requisitos:** Python 3.8 o superior.

### 5.2 Uso básico

```bash
python scripts/prtg_audit.py \
  --host https://tu-prtg.empresa.com \
  --user auditor \
  --passhash TU_PASSHASH \
  --site-name "GDL Principal" \
  --output ./reportes
```

**Parámetros disponibles:**

| Parámetro | Requerido | Descripción | Ejemplo |
|---|---|---|---|
| `--host` | Sí | URL completa del servidor PRTG | `https://prtg.empresa.com` |
| `--user` | Sí | Usuario de la API PRTG | `auditor` |
| `--passhash` | Sí | Passhash de My Account | `1234567890ABCDEF` |
| `--site-name` | No | Nombre del sitio para el CSV | `GDL Principal` |
| `--output` | No | Directorio de salida (default: `.`) | `./reportes` |
| `--no-verify-ssl` | No | Deshabilitar verificación SSL | *(flag, sin valor)* |

### 5.3 Auditoría multi-sitio

Para auditar múltiples instancias en un solo comando, usa el archivo de configuración de sitios:

```bash
# Crear archivo de sitios
cat > sitios.json << 'EOF'
[
  {"name": "GDL Principal", "host": "https://prtg-gdl.empresa.com", "user": "auditor", "passhash": "HASH1"},
  {"name": "MTY",           "host": "https://prtg-mty.empresa.com", "user": "auditor", "passhash": "HASH2"},
  {"name": "CDMX",          "host": "https://prtg-cdmx.empresa.com","user": "auditor", "passhash": "HASH3"},
  {"name": "DR Site",       "host": "https://prtg-dr.empresa.com",  "user": "auditor", "passhash": "HASH4"}
]
EOF

# Ejecutar auditoría multi-sitio
python scripts/prtg_audit.py --sites sitios.json --output ./reportes
```

El script procesa cada sitio en secuencia y genera un CSV separado por instancia con timestamp.

### 5.4 Automatización con cron

Ejemplos de tareas programadas típicas para NOC:

```cron
# Auditoría diaria a las 7:00 AM (hora Guadalajara, CST = UTC-6)
0 13 * * * /usr/bin/python3 /opt/prtg-audit/scripts/prtg_audit.py \
  --sites /opt/prtg-audit/sitios.json \
  --output /opt/prtg-audit/reportes \
  >> /var/log/prtg-audit.log 2>&1

# Auditoría cada lunes a las 8:00 AM para reporte semanal
0 14 * * 1 /usr/bin/python3 /opt/prtg-audit/scripts/prtg_audit.py \
  --sites /opt/prtg-audit/sitios.json \
  --output /opt/prtg-audit/reportes/semanales \
  >> /var/log/prtg-audit-weekly.log 2>&1
```

**Tip:** Los archivos de reporte se acumulan por fecha:
```
reportes/
├── prtg_audit_GDL-Principal_20260509_070000.csv
├── prtg_audit_GDL-Principal_20260510_070000.csv
├── prtg_audit_GDL-Principal_20260511_070000.csv
└── prtg_audit_MTY_20260509_070000.csv
```

---

## 6. CORS — Por qué y cuándo usar cada herramienta

### ¿Qué es CORS?

CORS (Cross-Origin Resource Sharing) es una política de seguridad de los navegadores. Cuando el dashboard intenta llamar a `https://tu-prtg.empresa.com/api/...` desde una URL diferente, el browser primero pregunta al servidor PRTG si permite esa llamada. Si PRTG no está configurado para responder con los headers CORS correctos, el browser **bloquea la petición** y el dashboard muestra un error.

### Cuándo aparece el error de CORS

- Estás abriendo el `prtg-audit-dashboard.html` directamente desde tu disco (`file://...`)
- Estás sirviendo el dashboard desde un servidor diferente al PRTG
- PRTG no tiene habilitados los headers `Access-Control-Allow-Origin`

### Soluciones

| Solución | Descripción | Cuándo usar |
|---|---|---|
| **Mismo dominio** | Alojar el dashboard en el mismo servidor que PRTG | Acceso directo a PRTG desde la misma red |
| **Docker + Nginx proxy** | El proxy reenvía las llamadas al PRTG real (sin CORS) | Cuando el dashboard debe servirse desde un dominio diferente |
| **Script Python** | No pasa por el browser, no tiene restricción CORS | Siempre que haya restricción de CORS |
| **Red interna** | Usar desde una máquina en la misma VLAN que PRTG | La forma más sencilla si tienes acceso de red directo |

---

## 7. Despliegue con Docker

El repo incluye `Dockerfile` y `docker-compose.yml` para servir el dashboard vía Nginx.

```bash
# Levantar el dashboard
cd PRTG-Audit-Dashboard
docker compose up -d

# Acceder en:
# http://localhost:8080
```

El contenedor Nginx sirve el HTML estático. Para agregar el proxy inverso hacia PRTG (resolver CORS), edita `proxy/` según tus instancias.

---

## 8. Glosario técnico

| Término | Definición |
|---|---|
| **Passhash** | Versión hasheada de la contraseña de un usuario PRTG. Se obtiene en *Setup → My Account → Passhash*. Más seguro que enviar el password en texto plano. |
| **API token** | Token de autenticación alternativo al passhash, disponible en versiones recientes de PRTG. |
| **limitmode** | Propiedad PRTG del sensor. Valor `1` = umbrales habilitados, `0` = sin umbrales activos. |
| **LimitMaxError** | Valor umbral que, al superarse, pone el sensor en estado `Error/Down`. Si no está definido, el sensor nunca alarma por umbral. |
| **CORS** | Cross-Origin Resource Sharing. Política del browser que puede bloquear llamadas a APIs en dominios diferentes. |
| **content=sensors** | Endpoint de la API PRTG que devuelve el listado de sensores con sus propiedades. |
| **content=devices** | Endpoint que devuelve el inventario de dispositivos/hosts monitoreados. |
| **Slot** | Espacio de configuración para una instancia PRTG en el dashboard. Capacidad máxima: 14 slots. |
| **Score de auditoría** | Puntuación de 0-100% calculada automáticamente a partir de 8 verificaciones del checklist. |
| **Estado RAM** | Los datos cargados en el dashboard viven en variables JavaScript en memoria, sin persistencia entre sesiones. |

---

## 9. Solución de problemas

### Error: "Failed to fetch" o "CORS policy"

**Causa:** El browser bloqueó la llamada por restricción CORS.

**Soluciones:**
1. Usa el **script Python** — no tiene esta restricción.
2. Despliega el dashboard en el mismo servidor que PRTG.
3. Usa el dashboard desde una máquina dentro de la red interna donde PRTG es accesible.

### Error: "HTTP 401 Unauthorized"

**Causa:** Credenciales incorrectas.

**Verificar:**
- El usuario existe en PRTG y tiene acceso a la API.
- El passhash es el correcto (puede cambiar si cambiaste el password).
- El usuario tiene permisos de lectura en los objetos auditados.

### Error: "HTTP 403 Forbidden"

**Causa:** El usuario no tiene permisos suficientes.

**Solución:** Verificar en PRTG que el usuario tiene acceso al grupo raíz o a los grupos que quieres auditar.

### Los datos de instancias desaparecieron al recargar

**Causa normal:** El dashboard no tiene persistencia. Los datos viven en RAM.

**Solución:** Antes de cerrar, **exporta el CSV**. Para evitar reconfigurar instancias cada vez, considera hacer un fork del repo y pre-configurar tus instancias en el código fuente (sin credenciales).

### El score del checklist es bajo pero la infraestructura está bien

**Causa posible:** Los umbrales del checklist son estrictos (0 sensores Down, 0 usuarios Admin, etc.).

**Interpretar correctamente:** El score es un punto de partida para la discusión, no un juicio final. Un sensor Down puede ser esperado (mantenimiento), y una cuenta Admin puede ser legítima. El valor del checklist es **forzar la revisión consciente** de cada punto.

---

*Manual generado con el apoyo de Perplexity AI · PRTG Audit Dashboard © 2026*
