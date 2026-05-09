"""
src/features/users/audit.py
============================
Feature: Auditoría de usuarios y permisos.
Obtiene la lista de cuentas de usuario activas en PRTG.
"""
from src.core.client import PRTGClient
from src.core.constants import API_TABLE, USER_COLS
from src.core.exceptions import PRTGDataError


class UserAudit:
    """
    Obtiene todos los usuarios registrados en PRTG.

    Uso:
        users = UserAudit(client).run()
    """

    def __init__(self, client: PRTGClient):
        self.client = client

    def run(self) -> list[dict]:
        print("  [users] Obteniendo usuarios...")
        data = self.client.get(API_TABLE, {
            "content": "accounts",
            "columns": USER_COLS,
            "count":   1000,
            "output":  "json",
        })

        users = data.get("accounts", [])
        if not isinstance(users, list):
            raise PRTGDataError("La API no devolvió una lista de cuentas.")

        result = [
            {
                "id":          u.get("objid", ""),
                "name":        u.get("name", ""),
                "email":       u.get("email", ""),
                "group":       u.get("groupmembership", ""),
                "user_group":  u.get("usergroup", ""),
            }
            for u in users
        ]

        print(f"  [users] {len(result)} usuarios encontrados.")
        return result
