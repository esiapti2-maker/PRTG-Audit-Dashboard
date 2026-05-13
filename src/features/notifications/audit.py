"""
src/features/notifications/audit.py
=====================================
Auditoría de plantillas de notificación PRTG.

Resultado de NotificationAudit.run():
    {
        "paused":   list[dict],   # plantillas pausadas o sin disparadores
        "all":      list[dict],   # todas las plantillas encontradas
    }

Cada dict incluye:
    id, nombre, activo, tipo, ultimo_uso, tiene_disparador, estado
"""

from __future__ import annotations
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.core.client import PRTGClient

log = logging.getLogger(__name__)

_COLUMNS = "objid,name,active,type,lastexecution"


class NotificationAudit:
    """Revisa plantillas de notificación e identifica las inactivas o sin uso."""

    def __init__(self, client: "PRTGClient") -> None:
        self.client = client

    def run(self) -> dict[str, list[dict]]:
        log.info("[notifications] Consultando plantillas de notificación...")
        raw = self.client.get("/api/table.json", {
            "content": "notifications",
            "columns": _COLUMNS,
            "count":   5000,
            "output":  "json",
        })
        notifs = [self._normalize(n) for n in raw.get("notifications", [])]
        log.info("[notifications] %d plantillas encontradas", len(notifs))

        paused = [
            n for n in notifs
            if not n["activo"]
            or n["ultimo_uso"].strip() in ("", "never", "-", "nunca")
        ]

        log.info("[notifications] Pausadas/sin uso: %d", len(paused))
        return {"paused": paused, "all": notifs}

    @staticmethod
    def _normalize(raw: dict) -> dict:
        activo = raw.get("active", True)
        # PRTG puede devolver 1/0, True/False o strings
        if isinstance(activo, str):
            activo = activo.lower() not in ("0", "false", "inactive", "paused")
        return {
            "id":            raw.get("objid", ""),
            "nombre":        raw.get("name", ""),
            "activo":        bool(activo),
            "tipo":          raw.get("type", ""),
            "ultimo_uso":    raw.get("lastexecution", ""),
        }
