# PRTG Audit Dashboard

Herramienta de auditoría técnica para instancias de **PRTG Network Monitor**. Detecta brechas de configuración, sensores sin cobertura real, cuentas con privilegios excesivos y notificaciones inoperantes.

## Componentes

| Archivo | Descripción |
|---|---|
| `prtg-audit-dashboard.html` | Dashboard web interactivo (abrir con doble clic) |
| `scripts/prtg_audit.py` | Script CLI para automatización y multi-sitio |

## Inicio rápido — Dashboard Web

1. Descargar o clonar el repositorio
2. Abrir `prtg-audit-dashboard.html` en el navegador
3. Ingresar la URL de tu PRTG, usuario y passhash
4. Presionar **"Ejecutar Auditoría"**
5. Exportar el reporte con **"Exportar CSV"**

> Para obtener el **passhash**: PRTG → tu usuario → My Account → sección API/Passhash

## Inicio rápido — Script Python

```bash
git clone https://github.com/esiapti2-maker/PRTG-Audit-Dashboard.git
cd PRTG-Audit-Dashboard
pip install -r requirements.txt

python scripts/prtg_audit.py \
  --host https://tu-prtg.empresa.com \
  --user auditor \
  --passhash TU_PASSHASH \
  --site-name Guadalajara \
  --output ./reportes
```

## Módulos de auditoría

- **Inventario general** — dispositivos, sensores y distribución de estados
- **Sensores Down/Warning** — equipos con alertas activas sin atender
- **Sensores sin umbrales** — sensores que nunca alertarán aunque estén en valor anómalo
- **Sensores pausados** — puntos ciegos por pausas crónicas (>7 días)
- **Usuarios y privilegios** — clasificación de riesgo por nivel de acceso
- **Notificaciones** — plantillas inactivas o sin disparador asignado

## Documentación completa

Consulta el **[Manual de Usuario](docs/MANUAL.md)** para:
- Explicación detallada de cada módulo
- Configuración multi-sitio y automatización con cron
- Resolución de problemas (CORS, SSL, permisos)
- Lectura del reporte CSV en Excel/LibreOffice
- Glosario técnico

## Estructura del proyecto

```
PRTG-Audit-Dashboard/
├── prtg-audit-dashboard.html   ← Dashboard web
├── scripts/
│   └── prtg_audit.py           ← Script Python CLI
├── docs/
│   └── MANUAL.md               ← Manual completo
├── requirements.txt
├── .env.example
└── .gitignore
```

## Seguridad

- Usar cuenta PRTG de **solo lectura** exclusiva para auditoría
- El passhash nunca se guarda en el repositorio (está en `.gitignore`)
- Los reportes CSV tampoco se sincronizan al repo

---

> Desarrollado para infraestructura enterprise con PRTG Network Monitor
