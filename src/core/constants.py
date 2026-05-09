"""
src/core/constants.py
=====================
Constantes y mapeos de la API PRTG.
Evita números mágicos dispersos en el código.
"""

# ── Estados de sensores ───────────────────────────────────────────────────────
STATUS_DOWN         = 5   # Sensor caído
STATUS_WARNING      = 4   # Sensor en advertencia
STATUS_UP           = 3   # Sensor OK
STATUS_PAUSED       = 7   # Sensor pausado manualmente
STATUS_PAUSED_SCHED = 8   # Pausado por horario
STATUS_PAUSED_DEP   = 9   # Pausado por dependencia

STATUS_PAUSED_ALL = {STATUS_PAUSED, STATUS_PAUSED_SCHED, STATUS_PAUSED_DEP}

STATUS_NAMES = {
    1:  "Unknown",
    2:  "Scanning",
    3:  "Up",
    4:  "Warning",
    5:  "Down",
    6:  "No Probe",
    7:  "Paused",
    8:  "Paused (Schedule)",
    9:  "Paused (Dependency)",
    10: "Paused (Maintenance)",
    11: "Down (Acknowledged)",
    12: "Down (Partial)",
}

# ── Endpoints de la API ───────────────────────────────────────────────────────
API_TABLE         = "/api/table.json"
API_SENSOR_DETAILS = "/api/getsensordetails.json"
API_USERS         = "/api/table.json"   # content=accounts
API_NOTIFICATIONS  = "/api/table.json"  # content=notifications

# ── Columnas de tabla por defecto ─────────────────────────────────────────────
DEVICE_COLS    = "objid,device,host,group,probe,status,message"
SENSOR_COLS    = "objid,sensor,device,group,probe,status,message,lastvalue,priority"
USER_COLS      = "objid,name,email,groupmembership,usergroup"
NOTIF_COLS     = "objid,name,active,status,lasttrigger"
