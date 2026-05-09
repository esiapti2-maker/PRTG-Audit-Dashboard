"""
src/features/users/types.py
============================
Type hints para el feature de usuarios.
"""
from typing import TypedDict


class UserRecord(TypedDict):
    id:         str
    name:       str
    email:      str
    group:      str
    user_group: str
