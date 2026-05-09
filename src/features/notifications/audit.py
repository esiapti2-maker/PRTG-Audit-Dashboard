"""
features/notifications/audit.py
================================
Módulo de auditoría de notificaciones y alertas.
Verifica qué notificaciones están activas vs pausadas.
Notificaciones pausadas = riesgo de no recibir alertas críticas.
"""

from src.core.client import PRTGClient


class NotificationAudit:
    """
    Audita el estado de las notificaciones/alertas configuradas en PRTG.
    """

    def __init__(self, client: PRTGClient):
        self.client = client
        self.notifications = []
        self.active = []
        self.paused = []

    def run(self) -> dict:
        """
        Obtiene todas las notificaciones y clasifica activas vs pausadas.

        Returns:
            Dict con keys: all, active, paused
        """
        print("  → Auditando notificaciones/alertas...")
        data = self.client.get("table.json", {
            "content": "notifications",
            "columns": "objid,name,active",
        })
        self.notifications = data.get("notifications", [])
        self.active = [n for n in self.notifications if str(n.get("active", "0")) == "1"]
        self.paused = [n for n in self.notifications if str(n.get("active", "0")) != "1"]
        print(f"     ✓ Activas: {len(self.active)} | Pausadas: {len(self.paused)}")
        return {
            "all": self.notifications,
            "active": self.active,
            "paused": self.paused,
        }
