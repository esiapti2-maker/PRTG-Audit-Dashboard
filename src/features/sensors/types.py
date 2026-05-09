"""
src/features/sensors/types.py
==============================
Type hints para el feature de sensores.
"""
from typing import TypedDict


class SensorRecord(TypedDict):
    id:        str
    name:      str
    device:    str
    group:     str
    probe:     str
    status:    str
    lastvalue: str
    priority:  str
    message:   str


class SensorAuditResult(TypedDict):
    down:      list
    warning:   list
    no_limits: list
    paused:    list
