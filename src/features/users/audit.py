"""
features/users/audit.py
=======================
Módulo de auditoría de usuarios y permisos.
Obtiene la lista de usuarios registrados en PRTG para
verificar credenciales por defecto, roles y accesos activos.
"""

from src.core.client import PRTGClient


class UserAudit:
    """
    Audita usuarios registrados en PRTG.
    Permite identificar cuentas con permisos excesivos o
    credenciales que no han sido rotadas.
    """

    COLUMNS = "objid,name,email,type"

    def __init__(self, client: PRTGClient):
        self.client = client
        self.users = []

    def run(self) -> list:
        """
        Obtiene todos los usuarios del servidor PRTG.

        Returns:
            Lista de dicts con información de cada usuario.
        """
        print("  → Auditando usuarios y permisos...")
        data = self.client.get("table.json", {
            "content": "users",
            "columns": self.COLUMNS,
        })
        self.users = data.get("users", [])
        print(f"     ✓ {len(self.users)} usuarios encontrados.")
        return self.users
