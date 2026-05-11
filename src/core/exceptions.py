"""
src/core/exceptions.py
========================
Jerarquía de excepciones del proyecto.

PRTGError
  ├── PRTGAuthError      — Credenciales inválidas o faltantes
  ├── PRTGConnectionError — Error de red o HTTP
  └── PRTGDataError      — Respuesta inesperada de la API
"""


class PRTGError(Exception):
    """Base para todos los errores del proyecto."""


class PRTGAuthError(PRTGError):
    """Credenciales inválidas, faltantes o URL malformada."""


class PRTGConnectionError(PRTGError):
    """Error de red, timeout o respuesta HTTP no exitosa."""


class PRTGDataError(PRTGError):
    """La API respondió OK pero el contenido no tiene el formato esperado."""
