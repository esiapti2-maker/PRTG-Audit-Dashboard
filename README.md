# PRTG Audit Dashboard

Dashboard de auditoría para **PRTG Network Monitor** — aplicación HTML estática de una sola página, sin dependencias de servidor.

## Características

- 📊 **Dashboard principal** — KPIs: dispositivos, sensores OK/Down, sin umbrales, pausados y Score de Auditoría
- 🔍 **Sensores** — Tabla completa con filtros por estado y búsqueda
- ⚙️ **Umbrales** — Sensores sin `LimitMaxError`/`LimitMaxWarning` configurados
- 👥 **Usuarios & Accesos** — Clasificación automática de riesgo (Alto/Medio/Bajo)
- 🔔 **Notificaciones** — Detecta notificaciones inactivas o sin disparadores
- ✅ **Checklist de Auditoría** — 8 verificaciones automáticas con semáforo
- 💻 **Scripts API** — Código listo en Python, PowerShell y cURL
- 🌙 **Modo oscuro/claro** — Soporte completo
- 📱 **Responsive** — Funciona en móvil y desktop

## Uso

1. Abre `prtg-audit-dashboard.html` en cualquier navegador moderno
2. Haz clic en **"Cargar datos demo"** para explorar sin conectarte a PRTG
3. Para conectar a tu PRTG real: ingresa el host, usuario y **passhash**
   - El passhash se obtiene en PRTG → Setup → My Account → Show Passhash
4. Haz clic en **"Conectar & Auditar"**
5. Usa **"Exportar CSV"** para generar el reporte de auditoría

## Nota sobre CORS

La conexión directa desde el navegador requiere que PRTG tenga CORS habilitado o que uses el dashboard desde la misma red interna.

## Stack

- HTML5 / CSS3 / JavaScript vanilla
- Sin frameworks — una sola dependencia CDN (Lucide Icons)
