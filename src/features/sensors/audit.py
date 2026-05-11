"""
src/features/sensors/audit.py
==============================
Feature: Auditoría de sensores.

Clasifica sensores en cuatro categorías:
  - down:       estado caído (status_raw == 5)
  - warning:    en advertencia (status_raw == 4)
  - no_limits:  sin límites/umbrales configurados (lastvalue vacío y activo)
  - paused:     pausados manual, por horario o por dependencia

Diagnóstico extendido:
  - Tiempo acumulado en estado Down/Warning (si `downtime` disponible)
  - Prioridad traducida a texto legible
  - Flag `has_limits` para diferenciar sensores con valor pero sin umbral
"""
from __future__ import annotations
from src.core.client import PRTGClient
from src.core.constants import (
    API_TABLE, SENSOR_COLS,
    STATUS_DOWN, STATUS_WARNING, STATUS_PAUSED_ALL, STATUS_NAMES,
)
from src.core.exceptions import PRTGDataError

_PRIORITY_MAP = {
    "1": "Muy baja", "2": "Baja", "3": "Normal",
    "4": "Alta",    "5": "Muy alta",
}


class SensorAudit:
    """
    Audita todos los sensores visibles para el usuario autenticado.

    Uso:
        result = SensorAudit(client).run()
        # result keys: "down", "warning", "no_limits", "paused"
    """

    def __init__(self, client: PRTGClient) -> None:
        self.client = client

    def run(self) -> dict[str, list]:
        print("  [sensors] Obteniendo sensores...")
        data = self.client.get(API_TABLE, {
            "content": "sensors",
            "columns": SENSOR_COLS,
            "count":   50_000,
            "output":  "json",
        })

        raw = data.get("sensors", [])
        if not isinstance(raw, list):
            raise PRTGDataError("La API no devolvió una lista de sensores.")

        down, warning, no_limits, paused = [], [], [], []

        for s in raw:
            status_raw = s.get("status_raw", 0)
            record     = self._parse(s, status_raw)

            if status_raw == STATUS_DOWN:
                down.append(record)
            elif status_raw == STATUS_WARNING:
                warning.append(record)
            elif status_raw in STATUS_PAUSED_ALL:
                paused.append(record)

            # Sin umbrales: sensor activo sin lastvalue Y sin limitsmax definido
            is_active    = status_raw not in STATUS_PAUSED_ALL
            has_lastval  = bool(str(s.get("lastvalue", "")).strip())
            has_limits_h = bool(str(s.get("limitsmax", "")).strip())
            has_limits_l = bool(str(s.get("limitsmin", "")).strip())

            if is_active and not has_lastval and not has_limits_h and not has_limits_l:
                no_limits.append(record)

        print(
            f"  [sensors] Down={len(down)} | Warning={len(warning)} "
            f"| Sin umbrales={len(no_limits)} | Pausados={len(paused)}"
        )
        return {
            "down":      down,
            "warning":   warning,
            "no_limits": no_limits,
            "paused":    paused,
        }

    # ── helpers ──────────────────────────────────────────────────────────────

    def _parse(self, s: dict, status_raw: int) -> dict:
        prio_raw = str(s.get("priority", ""))
        return {
            "id":          s.get("objid", ""),
            "name":        s.get("sensor", ""),
            "device":      s.get("device", ""),
            "group":       s.get("group", ""),
            "probe":       s.get("probe", ""),
            "status":      STATUS_NAMES.get(status_raw, s.get("status", "")),
            "status_raw":  status_raw,
            "lastvalue":   s.get("lastvalue", ""),
            "priority":    _PRIORITY_MAP.get(prio_raw, prio_raw),
            "priority_raw":prio_raw,
            "message":     s.get("message", ""),
            "downtime":    s.get("downtime", ""),
            "uptime":      s.get("uptime", ""),
            "tags":        s.get("tags", ""),
        }
