"""
core/client.py
==============
Cliente base HTTP para la API REST de PRTG.
Todas las features usan esta clase para realizar llamadas.
"""

import sys
import requests
import urllib3

from .auth import build_auth_params
from .exceptions import PRTGConnectionError, PRTGAuthError, PRTGTimeoutError

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class PRTGClient:
    """
    Cliente HTTP para la API de PRTG.
    Encapsula autenticación, manejo de errores y llamadas GET.
    """

    def __init__(self, host: str, username: str, password: str = None, passhash: str = None):
        """
        Args:
            host:     URL base del servidor PRTG (ej: https://prtg.empresa.com)
            username: Usuario de PRTG
            password: Contraseña en texto plano (usar passhash es más seguro)
            passhash: Hash de contraseña desde Setup → My Account → Passhash
        """
        self.host = host.rstrip("/")
        self.base_url = f"{self.host}/api"
        self._auth = build_auth_params(username, password, passhash)

    def get(self, endpoint: str, extra_params: dict = None) -> dict:
        """
        Realiza una llamada GET a la API de PRTG.

        Args:
            endpoint:     Endpoint relativo (ej: "table.json")
            extra_params: Parámetros adicionales de la query

        Returns:
            Respuesta JSON como dict

        Raises:
            PRTGConnectionError: Si no se puede conectar al servidor
            PRTGTimeoutError:    Si la request excede el timeout
            PRTGAuthError:       Si el servidor devuelve 401/403
        """
        params = dict(self._auth)
        if extra_params:
            params.update(extra_params)

        url = f"{self.base_url}/{endpoint}"

        try:
            response = requests.get(url, params=params, verify=False, timeout=30)

            if response.status_code in (401, 403):
                raise PRTGAuthError(f"Autenticación fallida en {self.host}. Verifica usuario/password/passhash.")

            response.raise_for_status()
            return response.json()

        except requests.exceptions.ConnectionError:
            raise PRTGConnectionError(f"No se puede conectar a {self.host}. Verifica URL y conectividad.")
        except requests.exceptions.Timeout:
            raise PRTGTimeoutError(f"Timeout al conectar a {self.host} (30s).")
        except requests.exceptions.HTTPError as e:
            raise PRTGConnectionError(f"HTTP {response.status_code}: {e}")
