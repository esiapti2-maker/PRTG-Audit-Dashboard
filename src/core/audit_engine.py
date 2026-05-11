"""
Motor de auditoría PRTG.
Cada método devuelve una lista de hallazgos (dicts) listos para exportar.
"""
from __future__ import annotations
from typing import List, Dict, Any
from .prtg_client import PRTGClient


class AuditEngine:
    """Orquesta los 6 módulos de auditoría."""

    def __init__(self, client: PRTGClient):
        self.client = client

    # ------------------------------------------------------------------
    # 1. Inventario general
    # ------------------------------------------------------------------
    def audit_inventory(self) -> Dict[str, Any]:
        sensors = self.client.get_sensors()["sensors"]
        devices = self.client.get_devices()["devices"]
        return {
            "total_sensors": len(sensors),
            "total_devices": len(devices),
            "by_status": self._count_by(sensors, "status"),
        }

    # ------------------------------------------------------------------
    # 2. Sensores críticos (Down / Warning)
    # ------------------------------------------------------------------
    def audit_critical_sensors(self) -> List[Dict]:
        sensors = self.client.get_sensors()["sensors"]
        findings = []
        for s in sensors:
            status = s.get("status", "").lower()
            if "down" in status or "warning" in status:
                findings.append({
                    "category": "critical_sensor",
                    "objid": s.get("objid"),
                    "sensor": s.get("sensor"),
                    "device": s.get("device"),
                    "group": s.get("group"),
                    "status": s.get("status"),
                    "message": s.get("message"),
                })
        return findings

    # ------------------------------------------------------------------
    # 3. Sensores sin umbrales definidos
    # ------------------------------------------------------------------
    def audit_no_thresholds(self) -> List[Dict]:
        """Detecta sensores cuyos canales no tienen límites configurados."""
        sensors = self.client.get_sensors()["sensors"]
        findings = []
        for s in sensors[:500]:  # máx 500 para no sobrecargar la API
            try:
                channels = self.client.get_channels(s["objid"]).get("channels", [])
                has_limit = any(
                    ch.get("limitmaxerror") or ch.get("limitminerror")
                    for ch in channels
                )
                if not has_limit:
                    findings.append({
                        "category": "no_threshold",
                        "objid": s.get("objid"),
                        "sensor": s.get("sensor"),
                        "device": s.get("device"),
                        "group": s.get("group"),
                        "channels_checked": len(channels),
                    })
            except Exception:
                pass
        return findings

    # ------------------------------------------------------------------
    # 4. Sensores pausados
    # ------------------------------------------------------------------
    def audit_paused_sensors(self) -> List[Dict]:
        sensors = self.client.get_sensors()["sensors"]
        return [
            {
                "category": "paused_sensor",
                "objid": s.get("objid"),
                "sensor": s.get("sensor"),
                "device": s.get("device"),
                "group": s.get("group"),
                "message": s.get("message"),
            }
            for s in sensors
            if "pause" in s.get("status", "").lower()
        ]

    # ------------------------------------------------------------------
    # 5. Usuarios y permisos
    # ------------------------------------------------------------------
    def audit_users(self) -> List[Dict]:
        users = self.client.get_users().get("accounts", [])
        findings = []
        for u in users:
            groups = u.get("usergroup", "").lower()
            risk = "high" if "prtg system administrator" in groups else (
                "medium" if "admin" in groups else "low"
            )
            findings.append({
                "category": "user_review",
                "objid": u.get("objid"),
                "name": u.get("name"),
                "email": u.get("email"),
                "groups": u.get("usergroup"),
                "risk_level": risk,
            })
        return findings

    # ------------------------------------------------------------------
    # 6. Notificaciones
    # ------------------------------------------------------------------
    def audit_notifications(self) -> List[Dict]:
        notifs = self.client.get_notifications().get("notifications", [])
        findings = []
        for n in notifs:
            issue = None
            if not n.get("active"):
                issue = "inactive"
            elif n.get("postpone"):
                issue = "postponed"
            if issue:
                findings.append({
                    "category": "notification_issue",
                    "objid": n.get("objid"),
                    "name": n.get("name"),
                    "issue": issue,
                })
        return findings

    # ------------------------------------------------------------------
    # Helper
    # ------------------------------------------------------------------
    @staticmethod
    def _count_by(items: List[Dict], field: str) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for item in items:
            key = item.get(field, "unknown")
            counts[key] = counts.get(key, 0) + 1
        return counts
