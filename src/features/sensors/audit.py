"""
src/features/sensors/audit.py
==============================
Feature: Auditoría de sensores.
Clasifica sensores en cuatro categorías:
  - down:       estado caído (status_raw == 5)
  - warning:    en advertencia (status_raw == 4)
  - no_limits:  sin límites/umbrales configurados
  - paused:     pausados manual o por horario
"""
from src.core.client import PRTGClient
from src.core.constants import (
    API_TABLE, SENSOR_COLS,
    STATUS_DOWN, STATUS_WARNING, STATUS_PAUSED_ALL, STATUS_NAMES,
)
from src.core.exceptions import PRTGDataError


class SensorAudit:
    """
    Audita todos los sensores y los clasifica por estado.

    Uso:
        result = SensorAudit(client).run()
        # result["down"], result["warning"], result["no_limits"], result["paused"]
    """

    def __init__(self, client: PRTGClient):
        self.client = client

    def run(self) -> dict[str, list]:
        print("  [sensors] Obteniendo sensores...")
        data = self.client.get(API_TABLE, {
            "content": "sensors",
            "columns": SENSOR_COLS,
            "count":   50000,
            "output":  "json",
        })

        sensors = data.get("sensors", [])
        if not isinstance(sensors, list):
            raise PRTGDataError("La API no devolvió una lista de sensores.")

        down, warning, no_limits, paused = [], [], [], []

        for s in sensors:
            status_raw = s.get("status_raw", 0)
            record = self._parse(s, status_raw)

            if status_raw == STATUS_DOWN:
                down.append(record)
            elif status_raw == STATUS_WARNING:
                warning.append(record)
            elif status_raw in STATUS_PAUSED_ALL:
                paused.append(record)

            # Sin umbrales: lastvalue vacío y sensor activo
            if not s.get("lastvalue") and status_raw not in STATUS_PAUSED_ALL:
                no_limits.append(record)

        print(f"  [sensors] Down={len(down)} | Warning={len(warning)} "
              f"| Sin umbrales={len(no_limits)} | Pausados={len(paused)}")

        return {
            "down":      down,
            "warning":   warning,
            "no_limits": no_limits,
            "paused":    paused,
        }

    def _parse(self, s: dict, status_raw: int) -> dict:
        return {
            "id":        s.get("objid", ""),
            "name":      s.get("sensor", ""),
            "device":    s.get("device", ""),
            "group":     s.get("group", ""),
            "probe":     s.get("probe", ""),
            "status":    STATUS_NAMES.get(status_raw, s.get("status", "")),
            "lastvalue": s.get("lastvalue", ""),
            "priority":  s.get("priority", ""),
            "message":   s.get("message", ""),
        }
