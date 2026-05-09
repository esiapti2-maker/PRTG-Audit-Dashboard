"""
src/features/notifications/types.py
=====================================
Type hints para el feature de notificaciones.
"""
from typing import TypedDict


class NotificationRecord(TypedDict):
    id:           str
    name:         str
    active:       str
    status:       str
    last_trigger: str


class NotificationAuditResult(TypedDict):
    active: list
    paused: list
