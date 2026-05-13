"""Módulo de auditoría de usuarios PRTG.

Clasifica cada cuenta según nivel de riesgo y detecta:
- Cuentas con privilegios excesivos (admin sin necesidad aparente)
- Cuentas sin email configurado (no recibirán alertas)
- Cuentas nunca utilizadas (last_login vacío)
- Cuentas con nombre genérico (admin, test, demo, guest)
- Múltiples administradores activos simultáneos
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List

from .types import RiskLevel, UserRecord

logger = logging.getLogger(__name__)

# Nombres de usuario genéricos considerados riesgosos
_GENERIC_NAMES = {"admin", "administrator", "test", "demo", "guest", "usuario", "user", "prtg"}


def _parse_user(raw: Dict[str, Any]) -> UserRecord:
    """Construye un UserRecord desde el dict crudo de la API de PRTG."""
    objid = int(raw.get("objid", 0))
    name = str(raw.get("name", "")).strip()
    email = str(raw.get("email", "")).strip()
    role = str(raw.get("role", "")).strip()
    active = str(raw.get("active", "1")) not in ("0", "false", "False")
    last_login = str(raw.get("lastlogin", "")).strip()

    role_lower = role.lower()
    is_admin = "admin" in role_lower or "superuser" in role_lower
    is_readonly = "read" in role_lower

    groups_raw = raw.get("groups", "")
    groups: List[str] = []
    if isinstance(groups_raw, list):
        groups = [str(g) for g in groups_raw]
    elif isinstance(groups_raw, str) and groups_raw:
        groups = [g.strip() for g in groups_raw.split(",") if g.strip()]

    return UserRecord(
        objid=objid,
        name=name,
        email=email,
        role=role,
        is_admin=is_admin,
        is_readonly=is_readonly,
        last_login=last_login,
        active=active,
        groups=groups,
    )


def _classify_risk(user: UserRecord, total_admins: int) -> UserRecord:
    """Asigna RiskLevel y lista de razones al UserRecord."""
    reasons: List[str] = []
    level = RiskLevel.LOW

    # Sin email → no recibirá ninguna alerta
    if not user.email:
        reasons.append("Sin email configurado — no recibirá alertas")
        level = max(level, RiskLevel.MEDIUM, key=lambda r: list(RiskLevel).index(r))

    # Nunca ha ingresado
    if not user.last_login:
        reasons.append("Cuenta nunca utilizada (sin last_login)")
        level = max(level, RiskLevel.MEDIUM, key=lambda r: list(RiskLevel).index(r))

    # Nombre genérico
    if user.name.lower() in _GENERIC_NAMES:
        reasons.append(f"Nombre de usuario genérico: '{user.name}'")
        level = max(level, RiskLevel.MEDIUM, key=lambda r: list(RiskLevel).index(r))

    # Admin sin email
    if user.is_admin and not user.email:
        reasons.append("Administrador sin email — credenciales elevadas sin contacto")
        level = max(level, RiskLevel.HIGH, key=lambda r: list(RiskLevel).index(r))

    # Admin nunca utilizado
    if user.is_admin and not user.last_login:
        reasons.append("Cuenta de administrador nunca utilizada")
        level = max(level, RiskLevel.HIGH, key=lambda r: list(RiskLevel).index(r))

    # Demasiados admins activos (más de 3 es señal de alerta)
    if user.is_admin and total_admins > 3:
        reasons.append(f"Demasiados administradores activos simultáneos: {total_admins}")
        level = max(level, RiskLevel.HIGH, key=lambda r: list(RiskLevel).index(r))

    # Admin con nombre genérico → crítico
    if user.is_admin and user.name.lower() in _GENERIC_NAMES:
        reasons.append("Administrador con nombre genérico — riesgo de acceso no autorizado")
        level = RiskLevel.CRITICAL

    user.risk_level = level
    user.risk_reasons = reasons
    return user


def audit_users(raw_users: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Audita la lista de usuarios PRTG y devuelve hallazgos estructurados.

    Args:
        raw_users: Lista de dicts crudos del endpoint /api/table.json?content=users

    Returns:
        Dict con claves:
            users       — lista de UserRecord serializados
            summary     — contadores por nivel de riesgo
            findings    — hallazgos críticos/high para el checklist
            score       — porcentaje de cuentas sin riesgo elevado (0-100)
    """
    if not raw_users:
        logger.warning("audit_users: lista vacía recibida")
        return {"users": [], "summary": {}, "findings": [], "score": 100}

    records = [_parse_user(u) for u in raw_users]

    # Contar admins activos para la regla de exceso
    total_admins = sum(1 for u in records if u.is_admin and u.active)

    # Clasificar riesgo
    records = [_classify_risk(u, total_admins) for u in records]

    # Resumen por nivel
    summary = {
        "total": len(records),
        "active": sum(1 for u in records if u.active),
        "admins": total_admins,
        "readonly": sum(1 for u in records if u.is_readonly),
        "no_email": sum(1 for u in records if not u.email),
        "never_logged_in": sum(1 for u in records if not u.last_login),
        "by_risk": {
            "low": sum(1 for u in records if u.risk_level == RiskLevel.LOW),
            "medium": sum(1 for u in records if u.risk_level == RiskLevel.MEDIUM),
            "high": sum(1 for u in records if u.risk_level == RiskLevel.HIGH),
            "critical": sum(1 for u in records if u.risk_level == RiskLevel.CRITICAL),
        },
    }

    # Hallazgos para el reporte (solo medium/high/critical)
    findings = [
        {
            "user": u.name,
            "email": u.email,
            "role": u.role,
            "risk": u.risk_level.value,
            "reasons": u.risk_reasons,
        }
        for u in records
        if u.risk_level != RiskLevel.LOW
    ]

    # Score: % de cuentas activas sin riesgo elevado (high/critical)
    active_users = [u for u in records if u.active]
    if active_users:
        safe = sum(
            1 for u in active_users
            if u.risk_level in (RiskLevel.LOW, RiskLevel.MEDIUM)
        )
        score = round((safe / len(active_users)) * 100)
    else:
        score = 100

    logger.info(
        "audit_users completado: %d usuarios, %d hallazgos, score=%d",
        len(records), len(findings), score,
    )

    return {
        "users": [
            {
                "objid": u.objid,
                "name": u.name,
                "email": u.email,
                "role": u.role,
                "is_admin": u.is_admin,
                "active": u.active,
                "last_login": u.last_login,
                "risk_level": u.risk_level.value,
                "risk_reasons": u.risk_reasons,
            }
            for u in records
        ],
        "summary": summary,
        "findings": findings,
        "score": score,
    }
