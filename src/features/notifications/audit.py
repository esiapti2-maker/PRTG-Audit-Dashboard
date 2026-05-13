"""Módulo de auditoría de notificaciones/acciones PRTG.

Detecta:
- Plantillas sin ningún método de entrega configurado
- Plantillas inactivas (activo = false)
- Plantillas huérfanas (ningún sensor/dispositivo las usa como trigger)
- Plantillas sin email cuando no hay SMS ni exec (punto ciego de alertas)
- Delay excesivo (postpone > 60 min) en notificaciones críticas
- Nombre genérico o por defecto ("Notification #1", etc.)
"""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, List

from .types import NotificationRecord

logger = logging.getLogger(__name__)

_GENERIC_NAME_PATTERN = re.compile(
    r"^(notification|notificaci[oó]n|alerta|alert)\s*#?\d*$",
    re.IGNORECASE,
)
_EXCESSIVE_POSTPONE_MINUTES = 60


def _parse_notification(raw: Dict[str, Any]) -> NotificationRecord:
    """Construye un NotificationRecord desde el dict crudo de la API."""
    objid = int(raw.get("objid", 0))
    name = str(raw.get("name", "")).strip()
    active = str(raw.get("active", "1")) not in ("0", "false", "False")
    schedule = str(raw.get("schedule", "")).strip()
    subject = str(raw.get("subject", "")).strip()

    # Postpone puede venir como string "5 minutes" o int
    raw_postpone = raw.get("postpone", 0)
    if isinstance(raw_postpone, str):
        digits = re.findall(r"\d+", raw_postpone)
        postpone = int(digits[0]) if digits else 0
    else:
        postpone = int(raw_postpone)

    # Métodos de entrega — PRTG los reporta como flags en el raw dict
    # El campo puede llamarse 'emailaddress', 'hasemail', etc., según versión
    has_email = bool(
        raw.get("emailaddress")
        or raw.get("hasemail")
        or raw.get("email")
        or raw.get("toemail")
    )
    has_sms = bool(
        raw.get("hassms")
        or raw.get("smsnumber")
        or raw.get("phonenumber")
    )
    has_exec = bool(
        raw.get("hasexe")
        or raw.get("exefilelocation")
        or raw.get("exefile")
    )

    triggers_count = int(raw.get("triggers", raw.get("triggerscount", 0)))

    return NotificationRecord(
        objid=objid,
        name=name,
        active=active,
        has_email=has_email,
        has_sms=has_sms,
        has_exec=has_exec,
        triggers_count=triggers_count,
        schedule=schedule,
        postpone=postpone,
        subject=subject,
    )


def _detect_issues(n: NotificationRecord) -> NotificationRecord:
    """Rellena n.issues con todos los problemas detectados."""
    issues: List[str] = []

    if not n.active:
        issues.append("Plantilla inactiva — no se disparará aunque haya trigger")

    if not n.has_delivery_method:
        issues.append("Sin método de entrega (no email, no SMS, no ejecutable)")

    if n.is_orphan:
        issues.append("Plantilla huérfana — ningún sensor/dispositivo la referencia")

    if not n.has_email and not n.has_sms and not n.has_exec:
        issues.append("Punto ciego de alertas: sin canal de notificación configurado")

    if n.postpone > _EXCESSIVE_POSTPONE_MINUTES:
        issues.append(
            f"Delay excesivo: {n.postpone} min antes de notificar "
            f"(recomendado ≤ {_EXCESSIVE_POSTPONE_MINUTES} min)"
        )

    if _GENERIC_NAME_PATTERN.match(n.name):
        issues.append(f"Nombre genérico '{n.name}' — dificulta la identificación rápida")

    n.issues = issues
    return n


def audit_notifications(raw_notifications: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Audita las plantillas de notificación de PRTG.

    Args:
        raw_notifications: Lista de dicts crudos del endpoint
            /api/table.json?content=notifications

    Returns:
        Dict con claves:
            notifications  — lista serializada con issues por plantilla
            summary        — contadores globales
            findings       — solo plantillas con al menos 1 problema
            score          — % de plantillas sin problemas (0-100)
    """
    if not raw_notifications:
        logger.warning("audit_notifications: lista vacía recibida")
        return {"notifications": [], "summary": {}, "findings": [], "score": 100}

    records = [_parse_notification(n) for n in raw_notifications]
    records = [_detect_issues(n) for n in records]

    summary = {
        "total": len(records),
        "active": sum(1 for n in records if n.active),
        "inactive": sum(1 for n in records if not n.active),
        "orphans": sum(1 for n in records if n.is_orphan),
        "no_delivery_method": sum(1 for n in records if not n.has_delivery_method),
        "with_email": sum(1 for n in records if n.has_email),
        "with_sms": sum(1 for n in records if n.has_sms),
        "with_exec": sum(1 for n in records if n.has_exec),
        "excessive_delay": sum(
            1 for n in records if n.postpone > _EXCESSIVE_POSTPONE_MINUTES
        ),
    }

    findings = [
        {
            "objid": n.objid,
            "name": n.name,
            "active": n.active,
            "triggers_count": n.triggers_count,
            "has_email": n.has_email,
            "has_sms": n.has_sms,
            "postpone_min": n.postpone,
            "issues": n.issues,
        }
        for n in records
        if n.issues
    ]

    healthy = sum(1 for n in records if not n.issues)
    score = round((healthy / len(records)) * 100) if records else 100

    logger.info(
        "audit_notifications completado: %d plantillas, %d con problemas, score=%d",
        len(records), len(findings), score,
    )

    return {
        "notifications": [
            {
                "objid": n.objid,
                "name": n.name,
                "active": n.active,
                "has_email": n.has_email,
                "has_sms": n.has_sms,
                "has_exec": n.has_exec,
                "triggers_count": n.triggers_count,
                "postpone_min": n.postpone,
                "schedule": n.schedule,
                "issues": n.issues,
            }
            for n in records
        ],
        "summary": summary,
        "findings": findings,
        "score": score,
    }
