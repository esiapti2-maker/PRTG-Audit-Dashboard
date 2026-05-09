"""
core/exceptions.py
==================
Excepciones personalizadas para el cliente PRTG.
"""


class PRTGError(Exception):
    """Excepción base para todos los errores de PRTG Audit."""
    pass


class PRTGConnectionError(PRTGError):
    """No se pudo establecer conexión con el servidor PRTG."""
    pass


class PRTGAuthError(PRTGError):
    """Error de autenticación — usuario, password o passhash inválidos."""
    pass


class PRTGTimeoutError(PRTGError):
    """La request al servidor PRTG excedió el tiempo de espera."""
    pass
