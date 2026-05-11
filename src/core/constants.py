"""
src/core/constants.py
======================
Constantes compartidas entre todos los módulos de auditoría.
Centralizar aquí evita strings duplicados y facilita ajustes.
"""

# ── Endpoints ─────────────────────────────────────────────────────────────────
API_TABLE = "/api/table.json"
API_SENSORTREE = "/api/table.json"  # mismo endpoint, content=sensortree

# ── Columnas por contenido ────────────────────────────────────────────────────
SENSOR_COLS = (
    "objid,sensor,device,group,probe,status,status_raw,"
    "lastvalue,priority,message,downtime,uptime,tags,"
    "limitsmax,limitsmin"
)

DEVICE_COLS = (
    "objid,device,host,group,probe,status,"
    "totalsens,downsens,warnsens,pausedsens"
)

USER_COLS = (
    "objid,name,email,groupmembership,usergroup,active"
)

NOTIF_COLS = (
    "objid,name,active,status,lasttrigger,tcount,toaddress"
)

# ── Códigos de estado de sensor (status_raw) ──────────────────────────────────
STATUS_UP              = 3
STATUS_WARNING         = 4
STATUS_DOWN            = 5
STATUS_NO_PROBE        = 6
STATUS_PAUSED_BY_USER  = 7
STATUS_PAUSED_INHERIT  = 8
STATUS_PAUSED_SCHEDULE = 9
STATUS_UNUSUAL         = 10
STATUS_NOT_LICENSED    = 11
STATUS_PAUSED_DEPEND   = 12

# Todos los estados considerados "pausado"
STATUS_PAUSED_ALL = {
    STATUS_PAUSED_BY_USER,
    STATUS_PAUSED_INHERIT,
    STATUS_PAUSED_SCHEDULE,
    STATUS_PAUSED_DEPEND,
}

# Nombres legibles por código
STATUS_NAMES: dict[int, str] = {
    STATUS_UP:              "OK",
    STATUS_WARNING:         "Warning",
    STATUS_DOWN:            "Down",
    STATUS_NO_PROBE:        "Sin sonda",
    STATUS_PAUSED_BY_USER:  "Pausado (manual)",
    STATUS_PAUSED_INHERIT:  "Pausado (heredado)",
    STATUS_PAUSED_SCHEDULE: "Pausado (horario)",
    STATUS_UNUSUAL:         "Inusual",
    STATUS_NOT_LICENSED:    "Sin licencia",
    STATUS_PAUSED_DEPEND:   "Pausado (dependencia)",
}
