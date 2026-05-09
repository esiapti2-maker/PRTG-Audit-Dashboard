"""
src/features/devices/audit.py
==============================
Feature: Inventario de dispositivos.
Obtiene todos los dispositivos registrados en PRTG con su estado actual.
"""
from src.core.client import PRTGClient
from src.core.constants import API_TABLE, DEVICE_COLS, STATUS_NAMES
from src.core.exceptions import PRTGDataError


class DeviceAudit:
    """
    Audita el inventario completo de dispositivos.

    Uso:
        devices = DeviceAudit(client).run()
    """

    def __init__(self, client: PRTGClient):
        self.client = client

    def run(self) -> list[dict]:
        """
        Obtiene todos los dispositivos.

        Returns:
            Lista de dicts con info de cada dispositivo.
        """
        print("  [devices] Obteniendo inventario de dispositivos...")
        data = self.client.get(API_TABLE, {
            "content":  "devices",
            "columns":  DEVICE_COLS,
            "count":    5000,
            "output":   "json",
        })

        devices = data.get("devices", [])
        if not isinstance(devices, list):
            raise PRTGDataError("La API no devolvió una lista de dispositivos.")

        result = []
        for d in devices:
            status_raw = d.get("status_raw", 0)
            result.append({
                "id":      d.get("objid", ""),
                "name":    d.get("device", ""),
                "host":    d.get("host", ""),
                "group":   d.get("group", ""),
                "probe":   d.get("probe", ""),
                "status":  STATUS_NAMES.get(status_raw, d.get("status", "")),
                "message": d.get("message", ""),
            })

        print(f"  [devices] {len(result)} dispositivos encontrados.")
        return result
