"""
src/core/audit_engine.py
==========================
Motor de auditoría de alto nivel.

Orquesta la ejecución de todos los módulos de auditoría y
calcula el AuditScore (0–100) que mide la salud del PRTG.

Fórmula del AuditScore:
  - Penalización por sensores Down         (peso 3)
  - Penalización por sensores sin umbrales (peso 2)
  - Penalización por notificaciones paused (peso 2)
  - Penalización por usuarios CRÍTICO      (peso 1)
  - Base 100 — suma de penalizaciones (mínimo 0)

Uso:
    engine = AuditEngine(client)
    result = engine.run()
    print(result.score)   # 0–100
    print(result.issues)  # lista de strings con hallazgos
"""
from __future__ import annotations
from dataclasses import dataclass, field

from src.core.client import PRTGClient
from src.features.devices.audit       import DeviceAudit
from src.features.sensors.audit       import SensorAudit
from src.features.users.audit         import UserAudit
from src.features.notifications.audit import NotificationAudit


@dataclass
class AuditResult:
    site_name:     str
    devices:       list = field(default_factory=list)
    sensors_down:  list = field(default_factory=list)
    sensors_warn:  list = field(default_factory=list)
    no_limits:     list = field(default_factory=list)
    paused:        list = field(default_factory=list)
    users:         list = field(default_factory=list)
    notifs_active: list = field(default_factory=list)
    notifs_paused: list = field(default_factory=list)
    score:         int  = 100
    issues:        list = field(default_factory=list)

    @property
    def summary(self) -> dict:
        return {
            "score":                self.score,
            "devices":             len(self.devices),
            "sensors_down":        len(self.sensors_down),
            "sensors_warning":     len(self.sensors_warn),
            "sensors_no_limits":   len(self.no_limits),
            "sensors_paused":      len(self.paused),
            "users":               len(self.users),
            "users_critical":      sum(1 for u in self.users if u.get("risk_level") == "CRÍTICO"),
            "notifications_active":len(self.notifs_active),
            "notifications_paused":len(self.notifs_paused),
        }


class AuditEngine:
    """
    Ejecuta todos los módulos de auditoría y calcula el AuditScore.

    Args:
        client: Instancia autenticada de PRTGClient
    """

    def __init__(self, client: PRTGClient) -> None:
        self.client = client

    def run(self, site_name: str = "sitio") -> AuditResult:
        result = AuditResult(site_name=site_name)

        # Ejecutar módulos
        result.devices = DeviceAudit(self.client).run()

        sensors = SensorAudit(self.client).run()
        result.sensors_down = sensors["down"]
        result.sensors_warn = sensors["warning"]
        result.no_limits    = sensors["no_limits"]
        result.paused       = sensors["paused"]

        result.users = UserAudit(self.client).run()

        notifs = NotificationAudit(self.client).run()
        result.notifs_active = notifs["active"]
        result.notifs_paused = notifs["paused"]

        # Calcular score
        result.score, result.issues = self._score(result)
        return result

    # ── scoring ───────────────────────────────────────────────────────────────

    def _score(self, r: AuditResult) -> tuple[int, list[str]]:
        total_sensors = max(
            len(r.sensors_down) + len(r.sensors_warn) + len(r.no_limits) + len(r.paused), 1
        )
        issues: list[str] = []
        penalty = 0

        # Sensores Down — penalización fuerte
        if r.sensors_down:
            pct = len(r.sensors_down) / total_sensors * 100
            p   = min(int(pct * 3), 40)   # máximo 40 puntos
            penalty += p
            issues.append(
                f"{len(r.sensors_down)} sensor(es) Down "
                f"({pct:.1f}% del total) — penalización {p} pts"
            )

        # Sin umbrales — penalización moderada
        if r.no_limits:
            pct = len(r.no_limits) / total_sensors * 100
            p   = min(int(pct * 2), 30)
            penalty += p
            issues.append(
                f"{len(r.no_limits)} sensor(es) sin umbrales "
                f"({pct:.1f}%) — penalización {p} pts"
            )

        # Notificaciones pausadas
        if r.notifs_paused:
            p = min(len(r.notifs_paused) * 3, 15)
            penalty += p
            issues.append(
                f"{len(r.notifs_paused)} notificación(es) pausada(s) "
                f"— penalización {p} pts"
            )

        # Usuarios con privilegios críticos sin control
        crit_users = [u for u in r.users if u.get("risk_level") == "CRÍTICO"]
        if crit_users:
            p = min(len(crit_users) * 2, 10)
            penalty += p
            issues.append(
                f"{len(crit_users)} usuario(s) con privilegios críticos "
                f"— penalización {p} pts"
            )

        score = max(100 - penalty, 0)
        if not issues:
            issues.append("Sin hallazgos críticos detectados ✓")
        return score, issues
