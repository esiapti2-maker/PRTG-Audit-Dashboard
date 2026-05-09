"""
core/auth.py
============
Manejo de autenticación para la API de PRTG.
Soporta password en texto plano y passhash (recomendado).

Obtener passhash: Setup → My Account → Passhash en PRTG.
"""


def build_auth_params(username: str, password: str = None, passhash: str = None) -> dict:
    """
    Construye los parámetros de autenticación para la API de PRTG.

    Args:
        username: Usuario de PRTG
        password: Contraseña en texto plano (menos seguro)
        passhash: Hash de contraseña obtenido desde PRTG (recomendado)

    Returns:
        dict con parámetros listos para incluir en la request

    Raises:
        ValueError: Si no se proporciona ni password ni passhash
    """
    if not password and not passhash:
        raise ValueError("Se requiere 'password' o 'passhash' para autenticar.")

    params = {"username": username, "output": "json"}
    if passhash:
        params["passhash"] = passhash
    else:
        params["password"] = password
    return params
