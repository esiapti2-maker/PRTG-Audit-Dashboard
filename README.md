# PRTG Audit Dashboard

Herramienta de auditoría para instancias PRTG Network Monitor. Genera reportes CSV con hallazgos de configuración para revisiones internas.

## Características

- ✅ Inventario completo de dispositivos
- ✅ Detección de sensores caídos y en warning
- ✅ Identificación de sensores **sin umbrales configurados** (riesgo de auditoría)
- ✅ Sensores pausados (verificar justificación)
- ✅ Auditoría de usuarios y permisos
- ✅ Estado de notificaciones activas vs pausadas
- ✅ Soporte **multi-sitio** (varias instancias PRTG)
- ✅ Exportación a CSV con clasificación de hallazgos

## Instalación

```bash
pip install -r requirements.txt
```

## Uso Rápido

### Un solo servidor

```bash
python scripts/prtg_audit.py \
  --host https://prtg.miempresa.com \
  --user admin \
  --pass MiContraseña \
  --site-name Corporativo
```

### Con passhash (recomendado — más seguro que contraseña en texto)

```bash
python scripts/prtg_audit.py \
  --host https://prtg.miempresa.com \
  --user auditor \
  --passhash 1234567890 \
  --output ./reportes
```

> 💡 El passhash se obtiene en PRTG: **Setup → Account Settings → My Account → Passhash**

### Multi-sitio (varias instancias)

Edita la lista `SITES` dentro de `scripts/prtg_audit.py`:

```python
SITES = [
    {
        "name": "Sitio-Principal",
        "host": "https://prtg-gdl.miempresa.com",
        "username": "auditor",
        "passhash": "1234567890",
    },
    {
        "name": "Sitio-DR",
        "host": "https://prtg-mty.miempresa.com",
        "username": "auditor",
        "passhash": "0987654321",
    },
]
```

Luego ejecuta:

```bash
python scripts/prtg_audit.py --multi-site --output ./reportes
```

## Hallazgos del reporte CSV

| Tipo de Hallazgo | Descripción | Acción recomendada |
|---|---|---|
| `CRITICO: Sensor caído` | Sensor en estado Down | Investigar causa raíz de inmediato |
| `ADVERTENCIA: Sensor en warning` | Sensor en estado Warning | Revisar umbrales y estado del dispositivo |
| `RIESGO: Sin umbrales de alerta` | Sensor activo sin límites configurados | Definir `LimitMaxError` y `LimitMaxWarning` |
| `REVISION: Sensor pausado` | Sensor con pausa activa | Verificar justificación o eliminar si es obsoleto |
| `Inventario de usuarios` | Lista de cuentas de acceso | Verificar contraseñas por defecto (`prtgadmin`) |

## Checklist de Auditoría PRTG

- [ ] Todos los sensores críticos con umbrales definidos
- [ ] Intervalos de polling: críticos ≤ 60s, secundarios ≤ 300s
- [ ] Notificaciones activas con contactos actualizados
- [ ] No hay usuarios con contraseñas por defecto
- [ ] Sensores pausados tienen justificación documentada
- [ ] Cobertura: todos los dispositivos del inventario están monitoreados
- [ ] Grupos organizados por sitio/función para facilitar la revisión

## Estructura del proyecto

```
PRTG-Audit-Dashboard/
├── scripts/
│   └── prtg_audit.py    # Script principal de auditoría
├── reports/             # Reportes CSV generados (se crea automáticamente)
├── requirements.txt
└── README.md
```

## Seguridad

> ⚠️ **Nunca commitees credenciales al repositorio.** Usa variables de entorno o un archivo `.env` (agrega `.env` a tu `.gitignore`).

```bash
# Opción con variables de entorno
export PRTG_HOST=https://prtg.empresa.com
export PRTG_USER=auditor
export PRTG_PASSHASH=1234567890

python scripts/prtg_audit.py \
  --host $PRTG_HOST \
  --user $PRTG_USER \
  --passhash $PRTG_PASSHASH
```
