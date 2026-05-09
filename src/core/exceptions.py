"""
src/core/exceptions.py
======================
Jerarquía de excepciones propias del proyecto.
"""


class PRTGError(Exception):
    """Base para todos los errores del proyecto."""


class PRTGAuthError(PRTGError):
    """Credenciales inválidas o ausentes."""


class PRTGConnectionError(PRTGError):
    """No se pudo conectar al servidor PRTG."""


class PRTGDataError(PRTGError):
    """La API devolvió datos inesperados o incompletos."""
