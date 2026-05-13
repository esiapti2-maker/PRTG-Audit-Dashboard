"""
src/features/users/audit.py
============================
Auditoría de usuarios y roles PRTG.

Resultado de UserAudit.run():
    list[dict] — cada usuario con:
        id, nombre, email, tipo, activo, rol_calculado, riesgo

    riesgo: "ALTO" | "MEDIO" | "BAJO"
        ALTO  → tipo "admin" (acceso total)
        MEDIO → tipo "readwrite" sin email configurado
        BAJO  → tipo "readonly"
"""

from __future__ import annotations
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.core.client import PRTGClient

log = logging.getLogger(__name__)

_COLUMNS = "objid,name,email,usertype,active"


class UserAudit:
    """Evalúa usuarios de PRTG y clasifica su nivel de riesgo."""

    def __init__(self, client: "PRTGClient") -> None:
        self.client = client

    def run(self) -> list[dict]:
        log.info("[users] Consultando usuarios...")
        raw = self.client.get("/api/table.json", {
            "content": "users",
            "columns": _COLUMNS,
            "count":   5000,
            "output":  "json",
        })
        users_raw = raw.get("users", [])
        log.info("[users] %d usuarios encontrados", len(users_raw))
        users = [self._normalize(u) for u in users_raw]
        for u in users:
            u["riesgo"] = self._classify_risk(u)
        return users

    @staticmethod
    def _classify_risk(user: dict) -> str:
        tipo = user.get("tipo", "").lower()
        email = user.get("email", "").strip()
        activo = user.get("activo", True)

        if not activo:
            return "BAJO"  # cuenta inactiva, riesgo reducido

        if tipo == "admin" or tipo == "administrator":
            return "ALTO"

        if tipo in ("readwrite", "write") and not email:
            return "MEDIO"  # puede escribir pero sin notificaciones

        return "BAJO"

    @staticmethod
    def _normalize(raw: dict) -> dict:
        return {
            "id":      raw.get("objid", ""),
            "nombre":  raw.get("name", ""),
            "email":   raw.get("email", ""),
            "tipo":    raw.get("usertype", ""),
            "activo":  raw.get("active", True),
        }
