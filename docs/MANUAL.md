# Manual de Usuario — PRTG Audit Dashboard

> **Versión:** 1.0.0 · **Última actualización:** Junio 2026  
> Herramienta de auditoría técnica para instancias de PRTG Network Monitor

---

## Tabla de contenido

1. [Arquitectura del aplicativo](#1-arquitectura-del-aplicativo)
2. [Componente 1 — Dashboard Web](#2-componente-1--dashboard-web)
   - [Instalación y apertura](#21-instalación-y-apertura)
   - [Formulario de conexión](#22-formulario-de-conexión)
   - [Flujo de auditoría](#23-flujo-de-auditoría)
   - [Secciones del dashboard](#24-secciones-del-dashboard)
   - [Exportar el reporte CSV](#25-exportar-el-reporte-csv)
   - [Modo Demo](#26-modo-demo)
3. [Componente 2 — Script Python CLI](#3-componente-2--script-python-cli)
   - [Instalación](#31-instalación)
   - [Uso básico](#32-uso-básico)
   - [Parámetros disponibles](#33-parámetros-disponibles)
   - [Auditoría multi-sitio](#34-auditoría-multi-sitio)
   - [Automatización con cron](#35-automatización-con-cron)
4. [Dónde se guarda la información](#4-dónde-se-guarda-la-información)
5. [Módulos de auditoría explicados](#5-módulos-de-auditoría-explicados)
   - [Inventario general](#51-inventario-general)
   - [Sensores Down y Warning](#52-sensores-down-y-warning)
   - [Sensores sin umbrales](#53-sensores-sin-umbrales)
   - [Sensores pausados](#54-sensores-pausados)
   - [Usuarios y privilegios](#55-usuarios-y-privilegios)
   - [Notificaciones](#56-notificaciones)
6. [Checklist automático y scoring](#6-checklist-automático-y-scoring)
7. [Lectura del reporte CSV](#7-lectura-del-reporte-csv)
8. [Resolución de problemas](#8-resolución-de-problemas)
9. [Seguridad y buenas prácticas](#9-seguridad-y-buenas-prácticas)
10. [Glosario técnico](#10-glosario-técnico)

---

## 1. Arquitectura del aplicativo

El PRTG Audit Dashboard se compone de **dos herramientas independientes** que se complementan:

```
┌─────────────────────────────────────────────────────────┐
│                 PRTG Audit Dashboard                    │
├────────────────────────┬────────────────────────────────┤
│  Dashboard Web         │  Script Python CLI             │
│  (HTML estático)       │  (prtg_audit.py)               │
├────────────────────────┼────────────────────────────────┤
│ • Corre en el browser  │ • Corre en terminal/servidor   │
│ • Visual e interactivo │ • Automatizable con cron       │
│ • Sin instalación      │ • Sin restricciones CORS       │
│ • Datos en RAM (sesión)│ • Guarda CSV con timestamp     │
│ • Exporta CSV manual   │ • Multi-sitio en un solo run   │
└────────────────────────┴────────────────────────────────┘
              │                        │
              └──────────┬─────────────┘
                         ▼
              API REST de PRTG (/api/)
```

**¿Cuándo usar cuál?**

| Situación | Herramienta recomendada |
|---|---|
| Revisión puntual, presentación en reunión | Dashboard Web |
| PRTG accesible desde el browser (sin CORS) | Dashboard Web |
| Programar auditorías automáticas | Script Python |
| Múltiples instancias PRTG (multi-sitio) | Script Python |
| PRTG en red interna sin acceso directo del browser | Script Python desde servidor |
| Historial acumulado de reportes | Script Python (CSV por fecha) |
| PRTG con certificado SSL autofirmado | Script Python con `--no-ssl-verify` |

---

## 2. Componente 1 — Dashboard Web

### 2.1 Instalación y apertura

No requiere instalación. Es un archivo HTML autocontenido.

```bash
# Opción A — Descarga directa
curl -O https://raw.githubusercontent.com/esiapti2-maker/PRTG-Audit-Dashboard/main/prtg-audit-dashboard.html

# Opción B — Clonar el repo completo
git clone https://github.com/esiapti2-maker/PRTG-Audit-Dashboard.git
```

Luego abre `prtg-audit-dashboard.html` con doble clic en cualquier browser moderno (Chrome 90+, Firefox 88+, Edge 90+). No necesita servidor web.

**Navegadores compatibles:**

| Navegador | Soporte |
|---|---|
| Chrome 90+ | ✅ Completo |
| Edge 90+ | ✅ Completo |
| Firefox 88+ | ✅ Completo |
| Safari 15+ | ✅ Completo |
| IE 11 | ❌ No soportado |

### 2.2 Formulario de conexión

Al abrir el dashboard verás el panel de configuración con tres campos:

| Campo | Descripción | Ejemplo |
|---|---|---|
| **URL de PRTG** | Dirección completa con protocolo | `https://prtg.empresa.com` |
| **Usuario** | Cuenta PRTG (recomendado: solo lectura) | `auditoria` |
| **Passhash** | Token de autenticación (no la contraseña) | `1234567890ABCDEF` |

> **¿Cómo obtener el Passhash?**  
> Dentro de PRTG: clic en tu nombre de usuario (esquina superior derecha) → **My Account** → sección **API / Passhash** → copiar el valor del campo *Passhash*.
>
> El passhash es más seguro que la contraseña porque es un token de solo lectura para la API y no expone tu contraseña real.

### 2.3 Flujo de auditoría

```
[Ingresar credenciales] → [Clic "Ejecutar Auditoría"]
         │
         ▼
[4 llamadas paralelas a la API de PRTG]
   • /api/table.json?content=devices    → Inventario
   • /api/table.json?content=sensors    → Sensores
   • /api/table.json?content=accounts   → Usuarios
   • /api/table.json?content=notifications → Notificaciones
         │
         ▼
[Procesamiento en el browser]
   • Clasificación de estados
   • Detección de anomalías
   • Cálculo de score
         │
         ▼
[Renderizado de resultados en pantalla]
         │
         ▼
[Exportar CSV] ← opcional
```

El proceso completo tarda entre **3 y 15 segundos** dependiendo del tamaño de tu instalación PRTG.

### 2.4 Secciones del dashboard

#### Panel de KPIs (parte superior)

Muestra 4 métricas principales al instante:

- **Total Dispositivos** — conteo completo de hosts monitoreados
- **Sensores OK** — sensores en estado verde (número y porcentaje)
- **Sensores Down** — sensores en estado rojo (alerta crítica)
- **Sin Umbrales** — sensores activos pero sin límites configurados (riesgo silencioso)
- **Score de Auditoría** — puntaje de 0 a 100% calculado con 8 criterios

#### Tabla de Sensores

Lista completa y filtrable con:
- Nombre del sensor y dispositivo padre
- Estado actual (Down, Warning, OK, Paused)
- Última lectura de valor
- Indicador visual de umbral configurado (✓ / ✗)

Usa el campo de **búsqueda** para filtrar por nombre, y el **selector de estado** para ver solo Down, solo Warning, etc.

#### Sección de Usuarios

Clasifica todas las cuentas PRTG en niveles de riesgo:
- 🔴 **Alto** — administradores o cuentas con acceso total
- 🟡 **Medio** — acceso a grupos específicos con permisos de escritura
- 🟢 **Bajo** — cuentas de solo lectura o monitoreo

#### Sección de Notificaciones

Revisa todas las plantillas de alerta configuradas:
- Plantillas **activas** (al menos un sensor la usa)
- Plantillas **inactivas** (configuradas pero sin asignar)
- Plantillas **sin disparador** (asignadas pero sin condición de activación)

#### Checklist de Auditoría

Ocho criterios con resultado pass ✅ / fail ❌ y recomendaciones por cada punto fallado.

### 2.5 Exportar el reporte CSV

El botón **"Exportar CSV"** descarga un archivo con nombre automático:
```
prtg_audit_YYYYMMDD_HHMMSS.csv
```

El archivo incluye:
- Resumen ejecutivo (KPIs)
- Lista completa de sensores con todos sus campos
- Tabla de usuarios con clasificación de riesgo
- Estado de notificaciones
- Resultados del checklist con recomendaciones

> **Importante:** Este es el único mecanismo de persistencia del Dashboard Web. Los datos **no se guardan automáticamente**. Si cierras el browser sin exportar, los resultados se pierden.

### 2.6 Modo Demo

El botón **"Cargar Demo"** carga datos de ejemplo sin necesitar conexión a PRTG. Útil para:
- Presentar el aplicativo a stakeholders antes de tener acceso al PRTG productivo
- Capacitar al equipo en la lectura de resultados
- Probar el aplicativo en redes sin acceso al servidor PRTG

---

## 3. Componente 2 — Script Python CLI

### 3.1 Instalación

**Requisitos:** Python 3.8 o superior

```bash
# Clonar el repo
git clone https://github.com/esiapti2-maker/PRTG-Audit-Dashboard.git
cd PRTG-Audit-Dashboard

# Instalar dependencias (solo 'requests')
pip install -r requirements.txt

# Verificar instalación
python scripts/prtg_audit.py --help
```

### 3.2 Uso básico

```bash
python scripts/prtg_audit.py \
  --host https://prtg.empresa.com \
  --user auditoria \
  --passhash TU_PASSHASH_AQUI \
  --site-name "Guadalajara" \
  --output ./reportes
```

Esto genera un archivo:
```
./reportes/prtg_audit_Guadalajara_20260601_170000.csv
```

### 3.3 Parámetros disponibles

| Parámetro | Obligatorio | Descripción | Ejemplo |
|---|---|---|---|
| `--host` | ✅ | URL base de PRTG | `https://prtg.empresa.com` |
| `--user` | ✅ | Nombre de usuario | `auditoria` |
| `--passhash` | ✅ | Passhash del usuario | `ABC123...` |
| `--site-name` | ❌ | Etiqueta para el reporte | `"CDMX-DC1"` |
| `--output` | ❌ | Carpeta de salida | `./reportes` (default: `.`) |
| `--timeout` | ❌ | Segundos de espera por llamada | `30` (default) |
| `--no-ssl-verify` | ❌ | Deshabilitar verificación SSL | (flag, sin valor) |
| `--modules` | ❌ | Módulos a ejecutar (separados por coma) | `sensors,users` |

**Ejemplo con PRTG de certificado autofirmado:**
```bash
python scripts/prtg_audit.py \
  --host https://prtg.local \
  --user auditoria \
  --passhash ABC123DEF456 \
  --site-name "Lab-Interno" \
  --output ./reportes \
  --no-ssl-verify
```

**Ejemplo completo con todos los parámetros:**
```bash
python scripts/prtg_audit.py \
  --host https://prtg.empresa.com \
  --user auditoria \
  --passhash ABC123DEF456 \
  --site-name "Monterrey-DC2" \
  --output /var/log/prtg-audits \
  --timeout 60 \
  --no-ssl-verify \
  --modules sensors,users,notifications
```

### 3.4 Auditoría multi-sitio

Para auditar múltiples instancias PRTG en un solo script, crea un archivo `sites.json`:

```json
[
  {
    "host": "https://prtg-gdl.empresa.com",
    "user": "auditoria",
    "passhash": "HASH_GDL",
    "site_name": "Guadalajara"
  },
  {
    "host": "https://prtg-mty.empresa.com",
    "user": "auditoria",
    "passhash": "HASH_MTY",
    "site_name": "Monterrey"
  },
  {
    "host": "https://prtg-cdmx.empresa.com",
    "user": "auditoria",
    "passhash": "HASH_CDMX",
    "site_name": "CDMX"
  }
]
```

Luego ejecuta:
```bash
python scripts/prtg_audit.py --sites-file sites.json --output ./reportes
```

Se genera un CSV separado por cada sitio más un **reporte consolidado** con todos los sitios.

> ⚠️ **Seguridad:** No guardes `sites.json` en el repositorio. Está en `.gitignore` por defecto.

### 3.5 Automatización con cron

**Auditoría diaria a las 7:00 AM:**
```bash
crontab -e
```

Agregar línea:
```cron
0 7 * * * /usr/bin/python3 /opt/prtg-audit/scripts/prtg_audit.py \
  --host https://prtg.empresa.com \
  --user auditoria \
  --passhash TU_PASSHASH \
  --site-name Produccion \
  --output /var/log/prtg-audits \
  >> /var/log/prtg-audits/cron.log 2>&1
```

**Auditoría semanal (lunes 6:00 AM) con limpieza de reportes viejos:**
```bash
# Ejecutar auditoría
0 6 * * 1 /usr/bin/python3 /opt/prtg-audit/scripts/prtg_audit.py --host https://prtg.empresa.com --user auditoria --passhash TU_HASH --output /var/log/prtg-audits

# Limpiar reportes con más de 90 días
0 6 * * 1 find /var/log/prtg-audits -name "prtg_audit_*.csv" -mtime +90 -delete
```

---

## 4. Dónde se guarda la información

Este punto es importante para entender el comportamiento del aplicativo:

### Dashboard Web

```
Browser abre el HTML
       │
       ▼
┌─────────────────────┐
│   RAM del browser   │  ← AQUÍ viven los datos durante la sesión
│  (memoria volátil)  │
└─────────────────────┘
       │
       │  Al cerrar/recargar → datos PERDIDOS
       │  Al hacer "Exportar CSV" → datos GUARDADOS en tu disco
       ▼
  Tu disco local
  prtg_audit_20260601_170523.csv
```

**El archivo HTML no crece.** Cada vez que abres el dashboard es exactamente el mismo archivo. Los datos que trae de PRTG son temporales.

### Script Python

```
Ejecución del script
       │
       ▼
  Llamadas a API PRTG
       │
       ▼
  Procesamiento en Python
       │
       ▼
  /reportes/prtg_audit_SITIO_20260601.csv  ← SE ACUMULA uno por ejecución
  /reportes/prtg_audit_SITIO_20260608.csv
  /reportes/prtg_audit_SITIO_20260615.csv
       ↑
  Sí va creciendo como historial por fecha
```

Con el script Python **sí se acumula un historial** porque cada ejecución genera un nuevo CSV con timestamp diferente.

---

## 5. Módulos de auditoría explicados

### 5.1 Inventario general

**¿Qué hace?** Consulta todos los dispositivos y sensores de la instancia PRTG.

**Datos que recopila:**
- Total de dispositivos (hosts)
- Total de sensores y distribución por estado (OK / Down / Warning / Paused / Unknown)
- Promedio de sensores por dispositivo
- Dispositivos sin ningún sensor (puntos ciegos totales)

**Hallazgo crítico que detecta:** Dispositivos con 0 sensores — están en PRTG pero no se monitorea nada de ellos.

### 5.2 Sensores Down y Warning

**¿Qué hace?** Lista todos los sensores que actualmente están en estado de alerta.

**Datos que recopila:**
- Nombre del sensor y dispositivo padre
- Estado actual
- Tiempo en ese estado (cuánto llevan fallando)
- Último mensaje de error

**Hallazgo crítico que detecta:** Sensores que llevan más de 24 horas en Down sin que nadie los haya atendido — indica falta de proceso de respuesta a alertas.

### 5.3 Sensores sin umbrales

**¿Qué hace?** Identifica sensores que están activos (verde/OK) pero que nunca generarán una alerta porque no tienen definidos los límites de cuándo es normal y cuándo es anómalo.

**¿Por qué es un riesgo grave?** Un sensor de CPU al 98% aparece como verde si no tiene umbral configurado. PRTG mide y grafica, pero nunca alerta. Es una falsa sensación de monitoreo.

**Ejemplo práctico:**
```
Sensor: CPU Usage — Servidor-DB-01
Valor actual: 94%
Estado PRTG: ✅ OK
Umbral Warning: (no configurado)
Umbral Error: (no configurado)
Riesgo: ALTO — el servidor puede llegar al 100% sin que nadie sea notificado
```

### 5.4 Sensores pausados

**¿Qué hace?** Lista todos los sensores en estado "Paused" (pausados manualmente) y calcula cuántos días llevan pausados.

**Umbral de riesgo:**
- **< 7 días:** Normal (mantenimiento programado)
- **7–30 días:** Sospechoso (¿se olvidaron de reactivarlo?)
- **> 30 días:** Punto ciego crónico (riesgo alto)

**Hallazgo que detecta:** Sensores que fueron pausados durante un mantenimiento y nadie los reactivó, creando puntos ciegos permanentes en el monitoreo.

### 5.5 Usuarios y privilegios

**¿Qué hace?** Obtiene todas las cuentas de PRTG y las clasifica por nivel de riesgo según sus permisos.

**Clasificación de riesgo:**

| Nivel | Criterio | Acción recomendada |
|---|---|---|
| 🔴 Alto | Rol `PRTG System Administrator` | Verificar que sea una cuenta nombrada, no genérica |
| 🔴 Alto | Contraseña sin expiración + admin | Establecer política de rotación |
| 🟡 Medio | Acceso a múltiples grupos con escritura | Revisar si el acceso amplio está justificado |
| 🟡 Medio | Cuentas sin actividad en 90+ días | Considerar deshabilitación |
| 🟢 Bajo | Solo lectura, grupo específico | Sin acción requerida |

**Dato importante:** PRTG no expone el hash de contraseñas a través de la API. El módulo evalúa solo permisos y configuración de cuenta, no la fortaleza de contraseñas.

### 5.6 Notificaciones

**¿Qué hace?** Revisa todas las plantillas de notificación configuradas en PRTG.

**Problemas que detecta:**

1. **Plantilla inactiva** — existe pero está deshabilitada.
2. **Sin disparador asignado** — la plantilla está activa pero ningún sensor o dispositivo la tiene configurada.
3. **Sin método de entrega** — plantilla sin email, SMS, webhook ni script configurado.

---

## 6. Checklist automático y scoring

El dashboard evalúa 8 criterios y calcula un score de auditoría de 0 a 100%:

| # | Criterio | Peso | Descripción |
|---|---|---|---|
| 1 | Sensores Down < 5% | 15 pts | Menos del 5% de sensores en estado Down |
| 2 | Sin sensores sin umbrales | 20 pts | Todos los sensores tienen límites configurados |
| 3 | Pausados < 10% | 10 pts | No más del 10% de sensores pausados |
| 4 | Sin pausados crónicos | 15 pts | Ningún sensor pausado más de 30 días |
| 5 | Administradores ≤ 3 | 10 pts | Máximo 3 cuentas con rol administrador |
| 6 | Sin cuentas inactivas | 10 pts | No hay cuentas sin actividad en 90+ días |
| 7 | Notificaciones activas | 10 pts | Al menos una notificación activa y asignada |
| 8 | Sin dispositivos sin sensores | 10 pts | Todos los dispositivos tienen al menos 1 sensor |

**Interpretación del score:**

| Score | Estado | Significado |
|---|---|---|
| 90–100% | 🟢 Excelente | Infraestructura bien configurada |
| 70–89% | 🟡 Aceptable | Áreas de mejora identificadas |
| 50–69% | 🟠 Deficiente | Brechas significativas de monitoreo |
| < 50% | 🔴 Crítico | Monitoreo no confiable |

---

## 7. Lectura del reporte CSV

El CSV exportado está en **UTF-8 con BOM** para compatibilidad con Excel en Windows.

### Abrir en Microsoft Excel

1. No hacer doble clic directo (puede mostrar caracteres raros)
2. Abrir Excel → **Datos** → **Desde Texto/CSV**
3. Seleccionar el archivo
4. Confirmar codificación **UTF-8** y delimitador **coma**
5. Clic en **Cargar**

### Abrir en LibreOffice Calc

1. Archivo → Abrir
2. Seleccionar el CSV
3. En el diálogo: Conjunto de caracteres **Unicode (UTF-8)**, Separador **Coma**
4. Aceptar

### Estructura del CSV

```
## RESUMEN EJECUTIVO ##
fecha,sitio,total_dispositivos,sensores_ok,sensores_down,...

## SENSORES ##
nombre,dispositivo,estado,valor,umbral_configurado,...

## USUARIOS ##
usuario,rol,ultimo_acceso,nivel_riesgo,...

## NOTIFICACIONES ##
nombre,activa,disparadores,metodo,...

## CHECKLIST ##
criterio,resultado,puntos,recomendacion,...
```

---

## 8. Resolución de problemas

### Error: "Failed to fetch" o "CORS error" en el Dashboard Web

**Causa:** El browser bloquea la solicitud al servidor PRTG por política de seguridad cross-origin.

**Soluciones:**

**Opción A — Usar el Script Python** (recomendada para producción):
```bash
python scripts/prtg_audit.py --host https://tu-prtg.com --user x --passhash y
```

**Opción B — Agregar cabeceras CORS en PRTG** (solo si tienes acceso al servidor):
En el servidor PRTG, agregar en `webserver.conf`:
```
Access-Control-Allow-Origin: *
```

**Opción C — Usar el proxy Nginx incluido** (para despliegue en servidor):
```bash
docker-compose up -d
# El proxy en el puerto 8080 reenvía las solicitudes evitando CORS
```

### Error: SSL Certificate Verify Failed

**Causa:** PRTG usa un certificado SSL autofirmado (común en entornos internos).

**Solución en el script Python:**
```bash
python scripts/prtg_audit.py \
  --host https://prtg.local \
  --user auditoria \
  --passhash TU_PASSHASH \
  --no-ssl-verify
```

> ⚠️ Usar `--no-ssl-verify` solo en redes internas de confianza.

### Error: "401 Unauthorized" o "Invalid credentials"

**Verificar:**
1. ¿Estás usando el **passhash** y no la contraseña?
2. El passhash se obtiene en: PRTG → My Account → API → Passhash
3. ¿La cuenta tiene permisos para acceder a la API?
4. ¿El usuario tiene al menos acceso de **solo lectura** a los objetos raíz?

### El dashboard tarda mucho o no carga todos los sensores

**Causa:** PRTG grande con miles de sensores. La API devuelve resultados paginados.

**Solución:** Usar el script Python con timeout extendido:
```bash
python scripts/prtg_audit.py --host https://prtg.com --user x --passhash y --timeout 120
```

### Los datos del reporte CSV se ven en una sola columna en Excel

**Causa:** Excel interpretó el archivo con separador de punto y coma en lugar de coma.

**Solución:**
1. En Excel: pestaña **Datos** → **Texto en columnas**
2. Seleccionar **Delimitado** → **Coma**
3. Finalizar

---

## 9. Seguridad y buenas prácticas

### Cuenta de auditoría dedicada

Crea una cuenta PRTG exclusiva para auditoría con los permisos mínimos necesarios:

```
Nombre sugerido: svc_auditoria (o audit_readonly)
Rol: Read Only User
Acceso: Solo lectura a grupos raíz
Contraseña: Rotar cada 90 días
Uso: Solo para ejecutar este script
```

**Pasos en PRTG:**
1. Setup → User Accounts → Add User Account
2. Tipo: **PRTG User** (no Windows User)
3. Rol: **Read Only User**
4. Member of: el grupo raíz (para ver todo) o grupos específicos
5. Guardar → ir al perfil del usuario → copiar el **Passhash**

### Protección de credenciales

- ✅ Usar variables de entorno: `export PRTG_PASSHASH=tu_hash`
- ✅ El archivo `.env` está en `.gitignore` — nunca se sube al repo
- ✅ Los reportes CSV están en `.gitignore` — no se sincronizan
- ❌ No hardcodear el passhash en scripts de cron — usar variables de entorno
- ❌ No compartir el passhash por Slack/Teams/email

**Uso con variable de entorno en cron:**
```bash
# /etc/cron.d/prtg-audit
PRTG_HOST=https://prtg.empresa.com
PRTG_USER=auditoria
PRTG_HASH=TU_PASSHASH_AQUI

0 7 * * * root python3 /opt/prtg-audit/scripts/prtg_audit.py \
  --host $PRTG_HOST --user $PRTG_USER --passhash $PRTG_HASH \
  --output /var/log/prtg-audits
```

### Qué datos NO expone este aplicativo

- ❌ No lee contraseñas de usuarios PRTG (la API no las devuelve)
- ❌ No modifica ninguna configuración de PRTG (solo lectura)
- ❌ No almacena datos en ningún servidor externo
- ❌ No envía telemetría ni métricas a terceros

---

## 10. Glosario técnico

| Término | Definición |
|---|---|
| **Passhash** | Token de autenticación de PRTG para la API REST. Equivale a una contraseña de API pero más seguro porque es de solo lectura y se puede revocar sin cambiar la contraseña del usuario. |
| **Sensor** | Unidad de medición en PRTG. Cada sensor monitorea una métrica específica (ping, CPU, disco, servicio, puerto, etc.). Un dispositivo puede tener N sensores. |
| **Umbral (Threshold)** | Límites configurados en un sensor que definen cuándo el valor es normal (verde), advertencia (amarillo) o error (rojo). Sin umbral, el sensor siempre aparece verde sin importar el valor medido. |
| **CORS** | Cross-Origin Resource Sharing. Política de seguridad de los browsers que bloquea solicitudes HTTP a dominios diferentes al origen de la página. Afecta al dashboard web pero no al script Python. |
| **Passhash vs Password** | La contraseña es el acceso principal a la interfaz web. El passhash es un hash derivado de la contraseña, exclusivo para la API, que permite autenticación sin exponer la contraseña real. |
| **Estado Down** | Sensor que no puede obtener datos o cuyo valor supera el umbral de error. |
| **Estado Warning** | Sensor cuyo valor supera el umbral de advertencia pero no el de error. |
| **Estado Paused** | Sensor deshabilitado manualmente. No genera alertas ni consume licencia. |
| **Estado Unknown** | Sensor que nunca ha sido ejecutado o cuyo resultado no puede determinarse. |
| **Score de auditoría** | Puntaje de 0-100% calculado evaluando 8 criterios de buenas prácticas de PRTG. |
| **Multi-sitio** | Capacidad del script Python para auditar varias instancias PRTG en una sola ejecución, generando un reporte consolidado. |
| **SSL Verify** | Verificación del certificado SSL del servidor PRTG. Deshabilitarla (`--no-ssl-verify`) es necesario cuando PRTG usa certificados autofirmados. Solo recomendado en redes internas. |

---

*Manual generado para PRTG Audit Dashboard v1.0.0 — Junio 2026*
