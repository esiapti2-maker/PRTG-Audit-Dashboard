"""Motor de checklist de auditoría PRTG — 8 puntos con score 0-100.

Cada CheckItem evalúa una dimensión específica del entorno PRTG y produce:
- status: 'pass' | 'warn' | 'fail'
- score_contribution: peso relativo en el score final
- detail: descripción del hallazgo
- recommendation: acción correctiva sugerida

Puntos del checklist:
  1. Sensores sin umbrales configurados
  2. Sensores en estado Down o Down (Acknowledged)
  3. Sensores en Warning
  4. Dispositivos sin sensores activos
  5. Usuarios administradores con nombre genérico o sin email
  6. Plantillas de notificación huérfanas o sin método de entrega
  7. Cuentas de usuario nunca utilizadas (last_login vacío)
  8. Exceso de administradores activos simultáneos
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Literal

logger = logging.getLogger(__name__)

Status = Literal["pass", "warn", "fail"]


@dataclass
class CheckResult:
    id: int
    name: str
    status: Status
    score_contribution: float   # Puntos aportados al score final (0 – weight)
    weight: float               # Peso máximo de este ítem
    detail: str
    recommendation: str
    metric: str = ""            # Valor numérico legible (ej. "12 sensores")

    @property
    def passed(self) -> bool:
        return self.status == "pass"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "status": self.status,
            "score_contribution": self.score_contribution,
            "weight": self.weight,
            "detail": self.detail,
            "recommendation": self.recommendation,
            "metric": self.metric,
        }


# ---------------------------------------------------------------------------
# Umbrales configurables
# ---------------------------------------------------------------------------
_THRESHOLDS = {
    "sensors_no_limits_pct_warn": 20,   # % de sensores sin umbrales → warn
    "sensors_no_limits_pct_fail": 40,   # % de sensores sin umbrales → fail
    "sensors_down_warn": 1,             # ≥ N sensores down → warn
    "sensors_down_fail": 5,             # ≥ N sensores down → fail
    "sensors_warning_warn": 3,
    "sensors_warning_fail": 10,
    "devices_no_sensors_warn": 1,
    "devices_no_sensors_fail": 5,
    "risky_users_warn": 1,
    "risky_users_fail": 3,
    "bad_notifications_warn": 1,
    "bad_notifications_fail": 3,
    "never_logged_warn": 2,
    "never_logged_fail": 5,
    "max_admins_warn": 3,
    "max_admins_fail": 6,
}


# ---------------------------------------------------------------------------
# Evaluadores individuales
# ---------------------------------------------------------------------------

def _check_sensors_no_limits(sensor_audit: Dict[str, Any]) -> CheckResult:
    summary = sensor_audit.get("summary", {})
    total = summary.get("total", 0)
    no_limits = summary.get("no_limits", 0)
    pct = round((no_limits / total) * 100) if total else 0

    warn_t = _THRESHOLDS["sensors_no_limits_pct_warn"]
    fail_t = _THRESHOLDS["sensors_no_limits_pct_fail"]

    if pct >= fail_t:
        status: Status = "fail"
        contrib = 0.0
    elif pct >= warn_t:
        status = "warn"
        contrib = 6.0
    else:
        status = "pass"
        contrib = 12.0

    return CheckResult(
        id=1,
        name="Sensores sin umbrales configurados",
        status=status,
        score_contribution=contrib,
        weight=12.0,
        detail=f"{no_limits} de {total} sensores ({pct}%) no tienen límites de alerta definidos.",
        recommendation="Definir valores de umbral (límite superior/inferior) en cada sensor. "
                       "Sensores sin umbrales nunca generarán alertas aunque el valor sea anómalo.",
        metric=f"{no_limits} sensores sin umbrales ({pct}%)",
    )


def _check_sensors_down(sensor_audit: Dict[str, Any]) -> CheckResult:
    summary = sensor_audit.get("summary", {})
    down = summary.get("down", 0) + summary.get("down_ack", 0)

    warn_t = _THRESHOLDS["sensors_down_warn"]
    fail_t = _THRESHOLDS["sensors_down_fail"]

    if down >= fail_t:
        status: Status = "fail"
        contrib = 0.0
    elif down >= warn_t:
        status = "warn"
        contrib = 6.25
    else:
        status = "pass"
        contrib = 12.5

    return CheckResult(
        id=2,
        name="Sensores en estado Down",
        status=status,
        score_contribution=contrib,
        weight=12.5,
        detail=f"{down} sensor(es) actualmente en estado Down o Down (Acknowledged).",
        recommendation="Revisar y resolver los sensores caídos. Los sensores en Down (Acknowledged) "
                       "indican que el problema es conocido pero no resuelto.",
        metric=f"{down} sensores Down",
    )


def _check_sensors_warning(sensor_audit: Dict[str, Any]) -> CheckResult:
    summary = sensor_audit.get("summary", {})
    warning = summary.get("warning", 0)

    warn_t = _THRESHOLDS["sensors_warning_warn"]
    fail_t = _THRESHOLDS["sensors_warning_fail"]

    if warning >= fail_t:
        status: Status = "fail"
        contrib = 0.0
    elif warning >= warn_t:
        status = "warn"
        contrib = 6.25
    else:
        status = "pass"
        contrib = 12.5

    return CheckResult(
        id=3,
        name="Sensores en Warning",
        status=status,
        score_contribution=contrib,
        weight=12.5,
        detail=f"{warning} sensor(es) en estado Warning — valores fuera de rango normal.",
        recommendation="Investigar la causa de cada warning. Si el estado es esperado, "
                       "ajustar los umbrales para evitar falsos positivos.",
        metric=f"{warning} sensores Warning",
    )


def _check_devices_no_sensors(device_audit: Dict[str, Any]) -> CheckResult:
    summary = device_audit.get("summary", {})
    no_sensors = summary.get("no_sensors", 0)

    warn_t = _THRESHOLDS["devices_no_sensors_warn"]
    fail_t = _THRESHOLDS["devices_no_sensors_fail"]

    if no_sensors >= fail_t:
        status: Status = "fail"
        contrib = 0.0
    elif no_sensors >= warn_t:
        status = "warn"
        contrib = 6.25
    else:
        status = "pass"
        contrib = 12.5

    return CheckResult(
        id=4,
        name="Dispositivos sin sensores activos",
        status=status,
        score_contribution=contrib,
        weight=12.5,
        detail=f"{no_sensors} dispositivo(s) no tienen ningún sensor activo asignado.",
        recommendation="Agregar sensores relevantes a cada dispositivo (ping, SNMP, WMI, etc.). "
                       "Un dispositivo sin sensores es invisible para el monitoreo.",
        metric=f"{no_sensors} dispositivos sin sensores",
    )


def _check_risky_users(user_audit: Dict[str, Any]) -> CheckResult:
    findings = user_audit.get("findings", [])
    high_critical = [
        f for f in findings
        if f.get("risk") in ("high", "critical")
    ]
    count = len(high_critical)

    warn_t = _THRESHOLDS["risky_users_warn"]
    fail_t = _THRESHOLDS["risky_users_fail"]

    if count >= fail_t:
        status: Status = "fail"
        contrib = 0.0
    elif count >= warn_t:
        status = "warn"
        contrib = 6.25
    else:
        status = "pass"
        contrib = 12.5

    return CheckResult(
        id=5,
        name="Usuarios con riesgo alto o crítico",
        status=status,
        score_contribution=contrib,
        weight=12.5,
        detail=f"{count} cuenta(s) con nivel de riesgo High o Critical detectadas.",
        recommendation="Revisar cuentas de administrador con nombre genérico, sin email o "
                       "nunca utilizadas. Deshabilitar o corregir según el caso.",
        metric=f"{count} cuentas riesgosas",
    )


def _check_bad_notifications(notif_audit: Dict[str, Any]) -> CheckResult:
    findings = notif_audit.get("findings", [])
    count = len(findings)

    warn_t = _THRESHOLDS["bad_notifications_warn"]
    fail_t = _THRESHOLDS["bad_notifications_fail"]

    if count >= fail_t:
        status: Status = "fail"
        contrib = 0.0
    elif count >= warn_t:
        status = "warn"
        contrib = 6.25
    else:
        status = "pass"
        contrib = 12.5

    return CheckResult(
        id=6,
        name="Plantillas de notificación con problemas",
        status=status,
        score_contribution=contrib,
        weight=12.5,
        detail=f"{count} plantilla(s) inactivas, huérfanas o sin método de entrega.",
        recommendation="Activar o eliminar plantillas sin uso. Asegurarse de que cada plantilla "
                       "tenga al menos un canal de entrega (email, SMS o ejecutable).",
        metric=f"{count} plantillas con problemas",
    )


def _check_never_logged_users(user_audit: Dict[str, Any]) -> CheckResult:
    summary = user_audit.get("summary", {})
    count = summary.get("never_logged_in", 0)

    warn_t = _THRESHOLDS["never_logged_warn"]
    fail_t = _THRESHOLDS["never_logged_fail"]

    if count >= fail_t:
        status: Status = "fail"
        contrib = 0.0
    elif count >= warn_t:
        status = "warn"
        contrib = 6.25
    else:
        status = "pass"
        contrib = 12.5

    return CheckResult(
        id=7,
        name="Cuentas de usuario nunca utilizadas",
        status=status,
        score_contribution=contrib,
        weight=12.5,
        detail=f"{count} cuenta(s) sin registro de último inicio de sesión.",
        recommendation="Deshabilitar cuentas que nunca han sido utilizadas o confirmar "
                       "que son cuentas de servicio con propósito definido.",
        metric=f"{count} cuentas sin uso",
    )


def _check_excess_admins(user_audit: Dict[str, Any]) -> CheckResult:
    summary = user_audit.get("summary", {})
    admins = summary.get("admins", 0)

    warn_t = _THRESHOLDS["max_admins_warn"]
    fail_t = _THRESHOLDS["max_admins_fail"]

    if admins >= fail_t:
        status: Status = "fail"
        contrib = 0.0
    elif admins > warn_t:
        status = "warn"
        contrib = 6.25
    else:
        status = "pass"
        contrib = 12.5

    return CheckResult(
        id=8,
        name="Exceso de administradores activos",
        status=status,
        score_contribution=contrib,
        weight=12.5,
        detail=f"{admins} cuenta(s) con rol de Administrador activas simultáneamente.",
        recommendation="Reducir el número de administradores al mínimo necesario (≤ 3 recomendado). "
                       "Usar cuentas de solo lectura para monitoreo operativo diario.",
        metric=f"{admins} administradores activos",
    )


# ---------------------------------------------------------------------------
# Punto de entrada público
# ---------------------------------------------------------------------------

_EVALUATORS = [
    _check_sensors_no_limits,
    _check_sensors_down,
    _check_sensors_warning,
    _check_devices_no_sensors,
    _check_risky_users,
    _check_bad_notifications,
    _check_never_logged_users,
    _check_excess_admins,
]


def run_checklist(
    sensor_audit: Dict[str, Any],
    device_audit: Dict[str, Any],
    user_audit: Dict[str, Any],
    notif_audit: Dict[str, Any],
) -> Dict[str, Any]:
    """Ejecuta los 8 puntos del checklist y calcula el score final.

    Args:
        sensor_audit:  Resultado de audit_sensors()
        device_audit:  Resultado de audit_devices()
        user_audit:    Resultado de audit_users()
        notif_audit:   Resultado de audit_notifications()

    Returns:
        Dict con claves:
            items   — lista de CheckResult serializados
            score   — int 0-100
            passed  — número de ítems con status 'pass'
            warned  — número de ítems con status 'warn'
            failed  — número de ítems con status 'fail'
            grade   — letra A/B/C/D/F según score
    """
    audits_by_evaluator = [
        sensor_audit,  # 1 - no limits
        sensor_audit,  # 2 - down
        sensor_audit,  # 3 - warning
        device_audit,  # 4 - no sensors
        user_audit,    # 5 - risky users
        notif_audit,   # 6 - bad notifications
        user_audit,    # 7 - never logged
        user_audit,    # 8 - excess admins
    ]

    results: List[CheckResult] = []
    for evaluator, audit_data in zip(_EVALUATORS, audits_by_evaluator):
        try:
            result = evaluator(audit_data)
            results.append(result)
        except Exception as exc:  # pragma: no cover
            logger.error("Error en evaluador %s: %s", evaluator.__name__, exc)

    total_weight = sum(r.weight for r in results)
    total_contrib = sum(r.score_contribution for r in results)
    score = round((total_contrib / total_weight) * 100) if total_weight else 0

    passed = sum(1 for r in results if r.status == "pass")
    warned = sum(1 for r in results if r.status == "warn")
    failed = sum(1 for r in results if r.status == "fail")

    if score >= 90:
        grade = "A"
    elif score >= 75:
        grade = "B"
    elif score >= 60:
        grade = "C"
    elif score >= 40:
        grade = "D"
    else:
        grade = "F"

    logger.info(
        "Checklist completado: score=%d (%s), pass=%d, warn=%d, fail=%d",
        score, grade, passed, warned, failed,
    )

    return {
        "items": [r.to_dict() for r in results],
        "score": score,
        "grade": grade,
        "passed": passed,
        "warned": warned,
        "failed": failed,
    }
