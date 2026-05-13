"""
src/features/devices/audit.py
==============================
Auditoría de dispositivos PRTG.

Resultado de DeviceAudit.run():
    list[dict] — cada dict representa un dispositivo con sus campos clave.

Campos devueltos por dispositivo:
    objid, device, host, group, status, active, probe,
    message, sensor_count, down_count
"""

from __future__ import annotations
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.core.client import PRTGClient

log = logging.getLogger(__name__)

# Columnas solicitadas a la API PRTG
_COLUMNS = "objid,device,host,group,status,active,probe,message,totalsens,downsens"


class DeviceAudit:
    """Extrae y normaliza el inventario de dispositivos."""

    def __init__(self, client: "PRTGClient") -> None:
        self.client = client

    def run(self) -> list[dict]:
        """Devuelve la lista completa de dispositivos con sus métricas."""
        log.info("[devices] Consultando inventario...")
        raw = self.client.get("/api/table.json", {
            "content":  "devices",
            "columns":  _COLUMNS,
            "count":    50000,
            "output":   "json",
        })
        devices = raw.get("devices", [])
        log.info("[devices] %d dispositivos encontrados", len(devices))
        return [self._normalize(d) for d in devices]

    @staticmethod
    def _normalize(raw: dict) -> dict:
        """Mapea claves crudas de la API a nombres legibles."""
        return {
            "id":           raw.get("objid", ""),
            "nombre":       raw.get("device", ""),
            "host":         raw.get("host", ""),
            "grupo":        raw.get("group", ""),
            "probe":        raw.get("probe", ""),
            "estado":       raw.get("status", ""),
            "activo":       raw.get("active", True),
            "mensaje":      raw.get("message", ""),
            "total_sens":   raw.get("totalsens", 0),
            "sens_down":    raw.get("downsens", 0),
        }
