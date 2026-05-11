"""
src/features/users/audit.py
============================
Feature: Auditoría de usuarios y permisos.

Detecta:
  - Usuarios con tipo PRTG Administrator (riesgo CRÍTICO)
  - Usuarios sin email configurado (no recibirán alertas)
  - Usuarios desactivados que siguen en el sistema
  - Cuentas de solo lectura sin grupo asignado
"""
from __future__ import annotations
from src.core.client import PRTGClient
from src.core.constants import API_TABLE, USER_COLS
from src.core.exceptions import PRTGDataError

# Grupos o roles considerados privilegio elevado
_HIGH_PRIV = {"PRTG Administrators", "Administrators", "Administrator"}


class UserAudit:
    """
    Audita usuarios PRTG y los enriquece con nivel de riesgo.

    Cada registro devuelto incluye:
      id, name, email, group, user_group,
      risk_level  (CRÍTICO | ALTO | MEDIO | BAJO),
      risk_reason (descripción legible del motivo)

    Uso:
        users = UserAudit(client).run()
    """

    def __init__(self, client: PRTGClient) -> None:
        self.client = client

    def run(self) -> list[dict]:
        print("  [users] Obteniendo usuarios...")
        data = self.client.get(API_TABLE, {
            "content": "accounts",
            "columns": USER_COLS,
            "count":   1000,
            "output":  "json",
        })

        raw = data.get("accounts", [])
        if not isinstance(raw, list):
            raise PRTGDataError("La API no devolvió una lista de cuentas.")

        result = [self._classify(u) for u in raw]

        critico = sum(1 for u in result if u["risk_level"] == "CRÍTICO")
        alto    = sum(1 for u in result if u["risk_level"] == "ALTO")
        print(f"  [users] {len(result)} usuarios — CRÍTICO={critico} ALTO={alto}")
        return result

    # ── helpers ──────────────────────────────────────────────────────────────

    def _classify(self, u: dict) -> dict:
        group      = u.get("groupmembership", "")
        user_group = u.get("usergroup", "")
        email      = u.get("email", "").strip()
        active     = str(u.get("active", "1")).lower() not in ("0", "false", "no")

        risk_level  = "BAJO"
        risk_reason = "Sin observaciones"

        # Reglas de riesgo — la de mayor severidad gana
        in_admin = any(g.strip() in _HIGH_PRIV for g in group.split(","))
        if in_admin or user_group in _HIGH_PRIV:
            risk_level  = "CRÍTICO"
            risk_reason = f"Pertenece al grupo administrador: '{user_group or group}'"
        elif not email:
            risk_level  = "ALTO"
            risk_reason = "Sin email configurado — no recibirá notificaciones de alerta"
        elif not active:
            risk_level  = "MEDIO"
            risk_reason = "Cuenta desactivada — considerar eliminar para reducir superficie de ataque"
        elif not group:
            risk_level  = "MEDIO"
            risk_reason = "Sin grupo asignado — acceso potencialmente sin restricciones"

        return {
            "id":          u.get("objid", ""),
            "name":        u.get("name", ""),
            "email":       email,
            "group":       group,
            "user_group":  user_group,
            "active":      "Sí" if active else "No",
            "risk_level":  risk_level,
            "risk_reason": risk_reason,
        }
