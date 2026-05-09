"""
features/sensors/audit.py
=========================
Módulo de auditoría de sensores.
Cubre 3 hallazgos clave:
  1. Sensores Down / Warning
  2. Sensores sin umbrales configurados (riesgo silencioso)
  3. Sensores pausados (>30 días = riesgo de auditoría)
"""

from src.core.client import PRTGClient


class SensorAudit:
    """
    Audita el estado de los sensores en PRTG:
    - down/warning, sin umbrales, y pausados.
    """

    def __init__(self, client: PRTGClient):
        self.client = client
        self.sensors_down = []
        self.sensors_warning = []
        self.sensors_no_limits = []
        self.sensors_paused = []

    def audit_down_warning(self) -> tuple:
        """
        Obtiene sensores en estado Down (status=5) y Warning (status=4).

        Returns:
            Tuple (sensors_down, sensors_warning)
        """
        print("  → Verificando sensores caídos / en warning...")
        columns = "objid,name,device,group,status,lastvalue,message,priority,tags"

        # Status 5 = Down
        data_down = self.client.get("table.json", {
            "content": "sensors",
            "columns": columns,
            "filter_status": "5",
        })
        self.sensors_down = data_down.get("sensors", [])

        # Status 4 = Warning
        data_warn = self.client.get("table.json", {
            "content": "sensors",
            "columns": columns,
            "filter_status": "4",
        })
        self.sensors_warning = data_warn.get("sensors", [])

        print(f"     ✓ Caídos: {len(self.sensors_down)} | Warning: {len(self.sensors_warning)}")
        return self.sensors_down, self.sensors_warning

    def audit_no_limits(self) -> list:
        """
        Identifica sensores sin umbrales de alerta configurados.
        Un sensor sin límites no alertará aunque el valor sea anómalo.

        Returns:
            Lista de sensores con limitmode=0 o sin límite máximo de error.
        """
        print("  → Verificando sensores sin umbrales definidos...")
        data = self.client.get("table.json", {
            "content": "sensors",
            "columns": "objid,name,device,group,status,lastvalue,priority,limitmaxerror,limitmaxwarning,limitmode",
        })
        sensors = data.get("sensors", [])
        self.sensors_no_limits = [
            s for s in sensors
            if str(s.get("limitmode", "0")) == "0"
            or s.get("limitmaxerror") in ["", None, "0"]
        ]
        print(f"     ✓ {len(self.sensors_no_limits)} sensores sin umbrales de {len(sensors)} totales.")
        return self.sensors_no_limits

    def audit_paused(self) -> list:
        """
        Obtiene sensores pausados (status=7).
        Pausas prolongadas (>30 días) representan riesgo de auditoría.

        Returns:
            Lista de sensores en estado Paused.
        """
        print("  → Verificando sensores pausados...")
        data = self.client.get("table.json", {
            "content": "sensors",
            "columns": "objid,name,device,group,status,message,tags",
            "filter_status": "7",  # 7 = Paused
        })
        self.sensors_paused = data.get("sensors", [])
        print(f"     ✓ {len(self.sensors_paused)} sensores pausados.")
        return self.sensors_paused

    def run(self) -> dict:
        """
        Ejecuta los 3 módulos de auditoría de sensores.

        Returns:
            Dict con keys: down, warning, no_limits, paused
        """
        self.audit_down_warning()
        self.audit_no_limits()
        self.audit_paused()
        return {
            "down": self.sensors_down,
            "warning": self.sensors_warning,
            "no_limits": self.sensors_no_limits,
            "paused": self.sensors_paused,
        }
