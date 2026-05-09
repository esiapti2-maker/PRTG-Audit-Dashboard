"""
features/devices/audit.py
=========================
Módulo de auditoría de dispositivos.
Obteniene el inventario completo de todos los dispositivos en PRTG.
"""

from src.core.client import PRTGClient


class DeviceAudit:
    """
    Audita el inventario de dispositivos registrados en PRTG.
    """

    COLUMNS = "objid,name,host,group,status,message,tags"

    def __init__(self, client: PRTGClient):
        self.client = client
        self.devices = []

    def run(self) -> list:
        """
        Obtiene todos los dispositivos del servidor PRTG.

        Returns:
            Lista de dicts con información de cada dispositivo.
        """
        print("  → Obteniendo inventario de dispositivos...")
        data = self.client.get("table.json", {
            "content": "devices",
            "columns": self.COLUMNS,
        })
        self.devices = data.get("devices", [])
        print(f"     ✓ {len(self.devices)} dispositivos encontrados.")
        return self.devices
