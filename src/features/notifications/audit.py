"""
src/features/notifications/audit.py
=====================================
Feature: Auditoría de notificaciones / alertas.
Detecta alertas activas vs pausadas para revisión de gaps de monitoreo.
"""
from src.core.client import PRTGClient
from src.core.constants import API_TABLE, NOTIF_COLS
from src.core.exceptions import PRTGDataError


class NotificationAudit:
    """
    Clasifica notificaciones en activas y pausadas.

    Uso:
        result = NotificationAudit(client).run()
        # result["active"], result["paused"]
    """

    def __init__(self, client: PRTGClient):
        self.client = client

    def run(self) -> dict[str, list]:
        print("  [notifications] Obteniendo notificaciones...")
        data = self.client.get(API_TABLE, {
            "content": "notifications",
            "columns": NOTIF_COLS,
            "count":   5000,
            "output":  "json",
        })

        notifs = data.get("notifications", [])
        if not isinstance(notifs, list):
            raise PRTGDataError("La API no devolvió una lista de notificaciones.")

        active, paused = [], []

        for n in notifs:
            record = {
                "id":           n.get("objid", ""),
                "name":         n.get("name", ""),
                "active":       n.get("active", ""),
                "status":       n.get("status", ""),
                "last_trigger": n.get("lasttrigger", ""),
            }
            if str(n.get("active", "")).lower() in ("0", "false", "no", ""):
                paused.append(record)
            else:
                active.append(record)

        print(f"  [notifications] Activas={len(active)} | Pausadas={len(paused)}")
        return {"active": active, "paused": paused}
