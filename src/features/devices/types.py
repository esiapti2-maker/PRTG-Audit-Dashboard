"""
src/features/devices/types.py
==============================
Type hints / TypedDict para el feature de dispositivos.
"""
from typing import TypedDict


class DeviceRecord(TypedDict):
    id:      str
    name:    str
    host:    str
    group:   str
    probe:   str
    status:  str
    message: str
