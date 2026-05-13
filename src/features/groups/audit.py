"""
src/features/groups/audit.py
==============================
Auditoría de grupos PRTG.

Resultado de GroupAudit.run():
    {
        "all":   list[dict],   # todos los grupos
        "empty": list[dict],   # grupos sin dispositivos (candidatos a limpieza)
    }

Cada dict incluye:
    id, nombre, padre, probe, total_devices, total_sensors, estado
"""

from __future__ import annotations
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.core.client import PRTGClient

log = logging.getLogger(__name__)

_COLUMNS = "objid,group,parent,probe,totalsens,totaldev,status"


class GroupAudit:
    """Audita la estructura de grupos y detecta grupos vacíos."""

    def __init__(self, client: "PRTGClient") -> None:
        self.client = client

    def run(self) -> dict[str, list[dict]]:
        log.info("[groups] Consultando estructura de grupos...")
        raw = self.client.get("/api/table.json", {
            "content": "groups",
            "columns": _COLUMNS,
            "count":   50000,
            "output":  "json",
        })
        groups = [self._normalize(g) for g in raw.get("groups", [])]
        log.info("[groups] %d grupos encontrados", len(groups))

        empty = [g for g in groups if g["total_devices"] == 0]
        log.info("[groups] Grupos vacíos: %d", len(empty))

        return {"all": groups, "empty": empty}

    @staticmethod
    def _normalize(raw: dict) -> dict:
        return {
            "id":            raw.get("objid", ""),
            "nombre":        raw.get("group", ""),
            "padre":         raw.get("parent", ""),
            "probe":         raw.get("probe", ""),
            "total_devices": int(raw.get("totaldev", 0) or 0),
            "total_sensors": int(raw.get("totalsens", 0) or 0),
            "estado":        raw.get("status", ""),
        }
