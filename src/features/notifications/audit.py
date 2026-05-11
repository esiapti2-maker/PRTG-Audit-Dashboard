"""
src/features/notifications/audit.py
=====================================
Feature: Auditoría de notificaciones / alertas.

Detecta:
  - Notificaciones pausadas o desactivadas (gap de alertas)
  - Notificaciones sin trigger_count (plantillas huérfanas sin sensores vinculados)
  - Notificaciones sin recipientes configurados (email vacío)
  - Clasifica cada notificación con nivel de riesgo
"""
from __future__ import annotations
from src.core.client import PRTGClient
from src.core.constants import API_TABLE, NOTIF_COLS
from src.core.exceptions import PRTGDataError


class NotificationAudit:
    """
    Clasifica notificaciones PRTG en activas y pausadas,
    enriqueciendo cada registro con diagnóstico de riesgo.

    Uso:
        result = NotificationAudit(client).run()
        # result["active"] — lista de notificaciones activas
        # result["paused"] — lista de notificaciones pausadas/sin uso
    """

    def __init__(self, client: PRTGClient) -> None:
        self.client = client

    def run(self) -> dict[str, list]:
        print("  [notifications] Obteniendo notificaciones...")
        data = self.client.get(API_TABLE, {
            "content": "notifications",
            "columns": NOTIF_COLS,
            "count":   5_000,
            "output":  "json",
        })

        raw = data.get("notifications", [])
        if not isinstance(raw, list):
            raise PRTGDataError("La API no devolvió una lista de notificaciones.")

        active, paused = [], []

        for n in raw:
            record = self._parse(n)
            if record["is_paused"]:
                paused.append(record)
            else:
                active.append(record)

        print(
            f"  [notifications] Activas={len(active)} | "
            f"Pausadas/sin uso={len(paused)}"
        )
        return {"active": active, "paused": paused}

    # ── helpers ──────────────────────────────────────────────────────────────

    def _parse(self, n: dict) -> dict:
        active_raw    = str(n.get("active",       "1")).lower()
        last_trigger  = str(n.get("lasttrigger",  "")).strip()
        trigger_count = int(n.get("tcount",        0) or 0)
        recipient     = str(n.get("toaddress",     "")).strip()

        is_paused = active_raw in ("0", "false", "no", "")

        # Clasificación de riesgo
        issues = []
        if is_paused:
            issues.append("Notificación desactivada — no generará alertas")
        if trigger_count == 0:
            issues.append("Sin sensores vinculados (plantilla huérfana)")
        if not recipient:
            issues.append("Sin destinatario configurado")

        risk_level = "OK"
        if issues:
            risk_level = "CRÍTICO" if is_paused else "ALTO"

        return {
            "id":            n.get("objid",      ""),
            "name":          n.get("name",       ""),
            "active":        "No" if is_paused else "Sí",
            "is_paused":     is_paused,
            "last_trigger":  last_trigger or "Nunca",
            "trigger_count": trigger_count,
            "recipient":     recipient or "(no definido)",
            "risk_level":    risk_level,
            "issue":         " | ".join(issues) if issues else "",
        }
