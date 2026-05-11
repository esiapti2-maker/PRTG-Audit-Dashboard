# Manual de Usuario — PRTG Audit Dashboard

**Versión:** 1.0  
**Fecha:** Mayo 2026  
**Repositorio:** [esiapti2-maker/PRTG-Audit-Dashboard](https://github.com/esiapti2-maker/PRTG-Audit-Dashboard)

---

## Tabla de Contenidos

1. [Descripción general](#1-descripción-general)
2. [Arquitectura del proyecto](#2-arquitectura-del-proyecto)
3. [Componente 1 — Dashboard Web](#3-componente-1--dashboard-web-prtg-audit-dashboardhtml)
   - 3.1 [Requisitos para abrirlo](#31-requisitos-para-abrirlo)
   - 3.2 [Pantalla de configuración inicial](#32-pantalla-de-configuración-inicial)
   - 3.3 [Dónde se guarda la configuración](#33-dónde-se-guarda-la-configuración)
   - 3.4 [Secciones del dashboard](#34-secciones-del-dashboard)
   - 3.5 [Modo Demo](#35-modo-demo)
   - 3.6 [Exportar CSV](#36-exportar-csv)
   - 3.7 [Problema de CORS y cuándo usarlo](#37-problema-de-cors-y-cuándo-usarlo)
4. [Componente 2 — Script Python](#4-componente-2--script-python-scriptsprtg_auditpy)
   - 4.1 [Instalación de dependencias](#41-instalación-de-dependencias)
   - 4.2 [Configuración via .env](#42-configuración-via-env)
   - 4.3 [Uso desde CLI](#43-uso-desde-cli)
   - 4.4 [Auditoría multi-sitio](#44-auditoría-multi-sitio)
   - 4.5 [Automatización con cron](#45-automatización-con-cron)
5. [Módulos de auditoría](#5-módulos-de-auditoría)
6. [Checklist automático de salud](#6-checklist-automático-de-salud)
7. [Lectura del reporte CSV](#7-lectura-del-reporte-csv)
8. [Obtener el Passhash de PRTG](#8-obtener-el-passhash-de-prtg)
9. [Resolución de problemas](#9-resolución-de-problemas)
10. [Glosario técnico](#10-glosario-técnico)

---

## 1. Descripción general

PRTG Audit Dashboard es una herramienta de auditoría técnica para instancias de **PRTG Network Monitor**. Permite identificar brechas de configuración, sensores sin cobertura real, cuentas con privilegios excesivos y notificaciones inoperantes.

El aplicativo tiene **dos componentes independientes** que se complementan:

| Componente | Tipo | Cuándo usarlo |
|---|---|---|
| `prtg-audit-dashboard.html` | Dashboard web estático | Revisión visual rápida, presentaciones, exploración con Demo |
| `scripts/prtg_audit.py` | Script Python CLI | Automatización, multi-sitio, entornos con restricción CORS |

Ambos consumen la misma **API JSON de PRTG** (disponible en cualquier instalación estándar, sin plugins adicionales).

---

## 2. Arquitectura del proyecto

```
PRTG-Audit-Dashboard/
├── prtg-audit-dashboard.html   ← Dashboard web (todo en un archivo)
├── scripts/
│   └── prtg_audit.py           ← Script de auditoría Python
├── docs/
│   └── MANUAL.md               ← Este archivo
├── requirements.txt            ← Dependencias Python
├── .env.example                ← Plantilla de variables de entorno
├── .gitignore                  ← Ignora CSVs, .env y __pycache__
└── README.md                   ← Inicio rápido
```

> **Nota de almacenamiento:** El proyecto no usa base de datos ni archivo de configuración persistente. Los reportes generados (CSV) viven únicamente en tu máquina local y no se sincronizan al repositorio (están en `.gitignore`).

---

## 3. Componente 1 — Dashboard Web (`prtg-audit-dashboard.html`)

### 3.1 Requisitos para abrirlo

- Cualquier navegador moderno (Chrome 90+, Firefox 88+, Edge 90+)
- Acceso de red al servidor PRTG (mismo segmento o VPN activa)
- Credenciales de PRTG: usuario + **passhash** (ver [sección 8](#8-obtener-el-passhash-de-prtg))

No requiere instalación, servidor web local ni dependencias externas. Simplemente abre el archivo `.html` con doble clic.

### 3.2 Pantalla de configuración inicial

Al abrir el dashboard, se muestra un formulario de conexión con los siguientes campos:

| Campo | Descripción | Ejemplo |
|---|---|---|
| **URL del servidor PRTG** | Dirección completa con protocolo | `https://prtg.empresa.com` o `http://192.168.1.100:8080` |
| **Usuario** | Nombre de usuario PRTG | `auditor` |
| **Passhash** | Hash seguro equivalente a la contraseña | `123456789` (ver sección 8) |
| **Nombre del sitio** | Etiqueta para identificar la instancia | `Guadalajara`, `CDMX-DC` |

Después de ingresar los datos y presionar **"Ejecutar Auditoría"**, el dashboard realiza 4 llamadas paralelas a la API de PRTG y muestra los resultados en segundos.

### 3.3 Dónde se guarda la configuración

**La configuración NO se guarda de forma permanente.** Al ingresar los datos en el formulario, estos se almacenan en variables JavaScript en memoria RAM del navegador. Esto significa:

- ✅ Los datos son seguros — nunca salen de tu máquina hacia un servidor externo
- ✅ No hay archivo de configuración que pueda filtrarse
- ⚠️ Al recargar o cerrar la pestaña, debes ingresar los datos nuevamente
- ⚠️ No existe historial de conexiones previas en el browser

**¿Qué sí persiste?** Los reportes exportados en CSV. Cada vez que presionas "Exportar CSV", se descarga un archivo con timestamp (`prtg_audit_Guadalajara_20260511_141500.csv`) que queda en tu carpeta de Descargas de forma permanente.

### 3.4 Secciones del dashboard

#### KPIs principales (fila superior)

Cuatro tarjetas con métricas inmediatas:

- **Dispositivos totales** — cantidad de hosts/equipos monitoreados
- **Sensores OK** — sensores en estado verde
- **Sensores Down** — sensores caídos o en error (en rojo)
- **Sin umbrales** — sensores activos que no tienen límites de alerta configurados (crítico)

#### Score de salud

Un indicador de 0 a 100% que evalúa el estado general de la configuración PRTG. El cálculo considera la proporción de sensores con umbrales, estado de notificaciones activas y nivel de privilegios de usuarios.

#### Tabla de sensores

Lista completa de todos los sensores con:
- Nombre del sensor y dispositivo al que pertenece
- Estado actual (OK / Warning / Down / Paused)
- Indicador visual de si tiene umbrales configurados
- Filtro en tiempo real por estado y búsqueda por texto

#### Usuarios y privilegios

Clasificación automática de cuentas:

| Nivel de riesgo | Criterio |
|---|---|
| 🔴 Alto | Cuenta con rol de administrador sin restricciones |
| 🟡 Medio | Cuenta con acceso de escritura a grupos sensibles |
| 🟢 Bajo | Cuenta de solo lectura o acceso limitado |

#### Notificaciones

Revisión de plantillas de alerta configuradas en PRTG:
- Notificaciones activas vs. inactivas
- Notificaciones sin ningún disparador asignado (nunca se ejecutarán)
- Canal de entrega: email, SMS, webhook, etc.

#### Checklist de auditoría

Ocho puntos de evaluación con resultado pass/fail automático (ver [sección 6](#6-checklist-automático-de-salud)).

### 3.5 Modo Demo

El botón **"Cargar Demo"** en la pantalla inicial carga un conjunto de datos de ejemplo predefinido sin necesidad de conexión a PRTG. Ideal para:

- Familiarizarse con la interfaz antes de una auditoría real
- Mostrar el funcionamiento a un equipo o cliente
- Desarrollar y probar sin acceso a producción

El modo Demo genera automáticamente ~50 sensores ficticios con distintos estados, 8 usuarios con distintos niveles de privilegio y 5 notificaciones, de las cuales 2 están inactivas y 1 sin disparador.

### 3.6 Exportar CSV

El botón **"Exportar CSV"** genera un archivo descargable con:

- Resumen ejecutivo (fecha, sitio, score, totales)
- Lista completa de sensores con su estado y configuración de umbrales
- Lista de usuarios con clasificación de riesgo
- Estado de notificaciones
- Resultado del checklist de 8 puntos

El nombre del archivo sigue el formato: `prtg_audit_{sitio}_{YYYYMMDD}_{HHMMSS}.csv`

> **Recomendación:** Exportar el CSV al finalizar cada sesión, ya que al cerrar el browser los datos se pierden.

### 3.7 Problema de CORS y cuándo usarlo

CORS (Cross-Origin Resource Sharing) es una política de seguridad del navegador. Cuando el archivo HTML intenta llamar a la API de PRTG desde un origen diferente (el sistema de archivos local o un servidor web distinto), el navegador puede bloquear la petición.

**Síntomas de error CORS:**
- La auditoría inicia pero no carga datos
- Aparece un error en la consola del navegador: `Access-Control-Allow-Origin`
- PRTG muestra el acceso en sus logs pero el browser rechaza la respuesta

**Soluciones:**

1. **Usar el script Python** — no tiene restricciones CORS, es la solución definitiva
2. **Extensión CORS para Chrome** (solo para pruebas, no producción): [CORS Unblock](https://chrome.google.com/webstore/detail/cors-unblock)
3. **Configurar headers en PRTG**: en algunos casos PRTG puede configurarse para emitir headers `Access-Control-Allow-Origin: *`

---

## 4. Componente 2 — Script Python (`scripts/prtg_audit.py`)

### 4.1 Instalación de dependencias

```bash
# Clonar el repositorio
git clone https://github.com/esiapti2-maker/PRTG-Audit-Dashboard.git
cd PRTG-Audit-Dashboard

# Crear entorno virtual (recomendado)
python3 -m venv venv
source venv/bin/activate        # Linux/macOS
venv\Scripts\activate           # Windows

# Instalar dependencias
pip install -r requirements.txt
```

Única dependencia externa: `requests >= 2.31.0`

### 4.2 Configuración via .env

Copia el archivo de ejemplo y edítalo:

```bash
cp .env.example .env
nano .env
```

Contenido del `.env`:

```dotenv
# Instancia principal
PRTG_HOST=https://prtg.empresa.com
PRTG_USER=auditor
PRTG_PASSHASH=1234567890
PRTG_SITE_NAME=Guadalajara

# Directorio de salida para los CSVs
OUTPUT_DIR=./reportes
```

> El archivo `.env` está en `.gitignore` — nunca se sube al repositorio.

### 4.3 Uso desde CLI

#### Auditoría básica (un sitio)

```bash
python scripts/prtg_audit.py \
  --host https://prtg.empresa.com \
  --user auditor \
  --passhash TU_PASSHASH \
  --site-name Guadalajara \
  --output ./reportes
```

#### Parámetros disponibles

| Parámetro | Obligatorio | Descripción | Default |
|---|---|---|---|
| `--host` | ✅ | URL completa del servidor PRTG | — |
| `--user` | ✅ | Usuario de PRTG | — |
| `--passhash` | ✅ | Passhash del usuario | — |
| `--site-name` | ✅ | Etiqueta del sitio (aparece en el CSV) | — |
| `--output` | ❌ | Carpeta donde se guarda el CSV | `./output` |
| `--modules` | ❌ | Módulos a ejecutar (separados por coma) | Todos |
| `--timeout` | ❌ | Segundos de timeout por petición | `30` |
| `--verify-ssl` | ❌ | Verificar certificado SSL | `True` |
| `--no-verify-ssl` | ❌ | Deshabilitar verificación SSL | — |

#### Ejecutar módulos específicos

```bash
# Solo sensores down y sin umbrales
python scripts/prtg_audit.py \
  --host https://prtg.empresa.com \
  --user auditor \
  --passhash TU_PASSHASH \
  --site-name GDL \
  --modules sensors_down,no_thresholds
```

Módulos disponibles: `inventory`, `sensors_down`, `no_thresholds`, `paused`, `users`, `notifications`

#### Deshabilitar SSL (servidores con cert autofirmado)

```bash
python scripts/prtg_audit.py \
  --host https://192.168.100.50 \
  --user admin \
  --passhash 9876543210 \
  --site-name DC-Local \
  --no-verify-ssl
```

### 4.4 Auditoría multi-sitio

Puedes crear un script bash/Python wrapper para iterar sobre múltiples instancias:

```bash
#!/bin/bash
# audit_all_sites.sh

SITES=(
  "https://prtg-gdl.empresa.com|auditor|PASSHASH1|Guadalajara"
  "https://prtg-cdmx.empresa.com|auditor|PASSHASH2|CDMX"
  "https://prtg-mty.empresa.com|auditor|PASSHASH3|Monterrey"
)

for SITE in "${SITES[@]}"; do
  IFS='|' read -r HOST USER PASSHASH NAME <<< "$SITE"
  python scripts/prtg_audit.py \
    --host "$HOST" \
    --user "$USER" \
    --passhash "$PASSHASH" \
    --site-name "$NAME" \
    --output ./reportes
done

echo "Auditoría multi-sitio completada. Reportes en ./reportes/"
```

```bash
chmod +x audit_all_sites.sh
./audit_all_sites.sh
```

Esto genera un CSV independiente por cada sitio:
```
reportes/
├── prtg_audit_Guadalajara_20260511_140000.csv
├── prtg_audit_CDMX_20260511_140015.csv
└── prtg_audit_Monterrey_20260511_140030.csv
```

### 4.5 Automatización con cron

#### Auditoría semanal (lunes 7:00 AM)

```bash
crontab -e
```

Agregar la línea:

```cron
0 7 * * 1 cd /opt/prtg-audit && source venv/bin/activate && python scripts/prtg_audit.py --host https://prtg.empresa.com --user auditor --passhash $(cat /etc/prtg_passhash) --site-name Produccion --output /opt/prtg-audit/reportes >> /var/log/prtg_audit.log 2>&1
```

#### Guardar el passhash de forma segura en Linux

```bash
# Crear archivo con permisos restrictivos
echo "TU_PASSHASH" > /etc/prtg_passhash
chmod 600 /etc/prtg_passhash
chown root:root /etc/prtg_passhash
```

---

## 5. Módulos de auditoría

El aplicativo ejecuta 6 módulos de análisis, tanto en el dashboard web como en el script Python.

### Módulo 1 — Inventario general (`inventory`)

Conecta al endpoint `/api/table.json` de PRTG y obtiene el conteo total de:
- Grupos, dispositivos y sensores
- Distribución por estado (OK, Warning, Down, Paused, Unknown)
- Tiempo de uptime de la instancia PRTG

### Módulo 2 — Sensores Down/Warning (`sensors_down`)

Lista todos los sensores que actualmente están en estado Down o Warning. Para cada uno muestra:
- Nombre del sensor y dispositivo padre
- Tiempo transcurrido desde que entró en ese estado
- Mensaje de error de PRTG
- Grupo al que pertenece

**Por qué importa:** Sensores down por más de 24h sin ticket asociado indican que nadie está respondiendo a las alertas.

### Módulo 3 — Sensores sin umbrales (`no_thresholds`)

Identifica sensores que **no tienen límites de alerta configurados**. Un sensor sin umbrales nunca generará una alerta de Warning o Critical, incluso si el valor que mide está fuera de rango.

Ejemplo crítico: un sensor de uso de CPU al 99% no alertará si no tiene umbral configurado en 85%.

**Por qué importa:** Es el hallazgo más común en auditorías PRTG y el de mayor riesgo operativo.

### Módulo 4 — Sensores pausados (`paused`)

Lista sensores en estado Paused con más de 7 días en ese estado. Clasifica entre:
- Paused by user (pausa manual)
- Paused by dependency (pausa en cascada por dispositivo padre)
- Paused by schedule (pausa programada — puede estar mal configurada)

**Por qué importa:** Sensores pausados indefinidamente generan puntos ciegos en el monitoreo.

### Módulo 5 — Usuarios y privilegios (`users`)

Obtiene todos los usuarios de PRTG y los clasifica por nivel de riesgo:

| Nivel | Condición |
|---|---|
| Alto | Rol `PRTG System Administrator` |
| Medio | Derechos de escritura en grupos sensibles |
| Bajo | Solo lectura o acceso limitado a grupos específicos |

También detecta:
- Cuentas sin último login registrado (posiblemente inactivas)
- Cuentas que comparten contraseña o passhash (misma cuenta genérica)

### Módulo 6 — Notificaciones (`notifications`)

Revisa todas las plantillas de notificación configuradas:
- Estado (activa / inactiva)
- Cantidad de disparadores asignados
- Canal de entrega (email, webhook, SMS, push)
- Última ejecución registrada

**Hallazgos típicos:**
- Notificaciones activas pero sin ningún disparador → nunca se ejecutarán
- Notificaciones apuntando a correos que ya no existen
- Canal de entrega sin configurar (campo vacío)

---

## 6. Checklist automático de salud

El dashboard y el CSV incluyen un checklist de **8 puntos** evaluados automáticamente con base en los datos obtenidos de PRTG:

| # | Punto de control | Criterio para PASS |
|---|---|---|
| 1 | Sensores sin umbrales | Menos del 10% del total |
| 2 | Sensores pausados crónicos | Menos del 5% del total |
| 3 | Notificaciones activas | Al menos 1 notificación activa con disparador |
| 4 | Notificaciones sin disparador | Ninguna notificación activa sin disparador |
| 5 | Usuarios administrador | Máximo 3 cuentas con rol de admin |
| 6 | Sensores down sin atender | Ningún sensor down por más de 48h |
| 7 | Cobertura de dispositivos | Todos los dispositivos tienen al menos 1 sensor |
| 8 | Diversidad de canales de alerta | Al menos 2 canales distintos configurados |

El **score** se calcula como: `(puntos en PASS / 8) × 100%`

---

## 7. Lectura del reporte CSV

El archivo CSV exportado tiene las siguientes secciones separadas por líneas de encabezado:

```
=== RESUMEN EJECUTIVO ===
Fecha,Sitio,Score,Dispositivos,Sensores_Total,Sensores_OK,Sensores_Down,...

=== SENSORES SIN UMBRALES ===
Sensor_ID,Nombre,Dispositivo,Grupo,Estado,Tipo

=== SENSORES DOWN/WARNING ===
Sensor_ID,Nombre,Dispositivo,Estado,Mensaje,Tiempo_En_Estado

=== USUARIOS ===
Usuario,Rol,Nivel_Riesgo,Ultimo_Login,Grupos_Acceso

=== NOTIFICACIONES ===
Nombre,Estado,Disparadores,Canal,Ultima_Ejecucion

=== CHECKLIST ===
Punto,Resultado,Detalle
```

**Para importar en Excel:**
1. Abrir Excel → Datos → Desde texto/CSV
2. Seleccionar el archivo
3. Delimitador: coma
4. Codificación: UTF-8

**Para importar en LibreOffice Calc:**
- Doble clic directo sobre el archivo CSV
- Seleccionar coma como separador y UTF-8 como codificación

---

## 8. Obtener el Passhash de PRTG

El **Passhash** es un identificador numérico único que PRTG asigna a cada cuenta. Es equivalente a la contraseña para uso en la API, pero no la expone en texto plano.

### Pasos para obtenerlo

1. Iniciar sesión en PRTG con la cuenta que se usará para la auditoría
2. Hacer clic en el nombre de usuario (esquina superior derecha)
3. Seleccionar **"My Account"** (Mi cuenta)
4. En la sección **"API / Passhash"**, copiar el valor numérico de ~10 dígitos

### Via URL directa

```
https://TU-PRTG.empresa.com/api/getpasshash.htm?username=USUARIO&password=CONTRASEÑA
```

Esta URL devuelve únicamente el passhash en texto plano. Úsala una sola vez para obtenerlo y luego usa el passhash en lugar de la contraseña.

### Buenas prácticas de seguridad

- Crear una cuenta PRTG **de solo lectura** exclusiva para auditoría (no usar el admin principal)
- Rotar el passhash después de cada auditoría formal
- Guardar el passhash en un gestor de contraseñas o en un archivo con permisos `600`
- Nunca incluirlo directamente en scripts que se suban a repositorios públicos

---

## 9. Resolución de problemas

### Error: "Failed to fetch" o datos vacíos en el dashboard

**Causa probable:** Restricción CORS del navegador.

**Solución:** Usar el script Python desde la terminal. Si necesitas usar el dashboard, revisa la sección [3.7 Problema de CORS](#37-problema-de-cors-y-cuándo-usarlo).

---

### Error: `requests.exceptions.SSLError`

**Causa probable:** El servidor PRTG tiene un certificado SSL autofirmado.

**Solución:**
```bash
python scripts/prtg_audit.py ... --no-verify-ssl
```

> ⚠️ Usar `--no-verify-ssl` solo en redes internas de confianza.

---

### Error: `401 Unauthorized`

**Causa probable:** Passhash incorrecto o usuario inexistente.

**Verificación:**
```bash
curl -k "https://TU-PRTG/api/table.json?content=devices&output=json&username=USUARIO&passhash=PASSHASH&count=1"
```

Si devuelve `{"prtg-version":...}` el acceso es correcto. Si devuelve `{"error":1}`, el passhash es inválido.

---

### Error: `ConnectionRefusedError` o timeout

**Causas posibles:**
- El puerto de PRTG no es el estándar (443/80) — especificar el puerto en la URL: `https://192.168.1.100:8443`
- Firewall bloqueando el acceso — verificar con `telnet 192.168.1.100 8443`
- VPN no conectada

---

### El score aparece en 0% con datos correctos

**Causa probable:** La cuenta de auditoría no tiene permisos para leer la configuración de notificaciones o usuarios.

**Solución:** Asegurarse de que la cuenta tenga al menos permisos de lectura en **todos los grupos** de PRTG, incluyendo el grupo raíz.

---

### El CSV se descarga vacío

**Causa:** El Export se activó antes de que terminara la carga de datos.

**Solución:** Esperar a que el score y todos los paneles muestren datos antes de exportar. El botón de exportar se habilita automáticamente cuando la carga termina.

---

## 10. Glosario técnico

| Término | Definición |
|---|---|
| **Passhash** | Identificador numérico de autenticación de PRTG, equivalente a contraseña para uso en API |
| **Sensor** | Unidad de monitoreo en PRTG que mide un parámetro específico (CPU, ping, disco, etc.) |
| **Umbral (Threshold)** | Valor límite configurado en un sensor que, al superarse, genera una alerta |
| **CORS** | Cross-Origin Resource Sharing — política de seguridad del navegador que restringe llamadas a dominios distintos |
| **Passhash** | Token numérico único que PRTG asigna a cada usuario para autenticación en la API |
| **Sensor Down** | Sensor que no puede ejecutar su medición, generalmente por falla de conectividad o del agente |
| **Sensor Paused** | Sensor detenido manualmente, por dependencia o por programación |
| **Disparador (Trigger)** | Condición que activa una notificación cuando un sensor cambia de estado |
| **API JSON de PRTG** | Interfaz HTTP de PRTG disponible en `/api/table.json` que devuelve datos de monitoreo en formato JSON |
| **Score de salud** | Porcentaje calculado a partir del checklist de 8 puntos que refleja la calidad de la configuración PRTG |
| **Multi-sitio** | Modo de auditoría que itera sobre múltiples instancias PRTG independientes en una sola ejecución |
| **CSV de auditoría** | Archivo de valores separados por coma generado como evidencia y registro de la auditoría realizada |

---

*Manual generado para PRTG Audit Dashboard v1.0 — Mayo 2026*
