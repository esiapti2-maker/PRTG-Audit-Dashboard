"""
src/core/client.py
==================
Cliente HTTP base para la API JSON de PRTG.
Toda comunicación con el servidor pasa por aquí.
"""
import requests
from urllib.parse import urljoin
from .exceptions import PRTGAuthError, PRTGConnectionError


class PRTGClient:
    """
    Encapsula las credenciales y realiza GET requests a la API de PRTG.

    Args:
        host:      URL base, ej. https://prtg.empresa.com
        username:  Usuario de PRTG
        password:  Contraseña en texto plano  (opcional si usas passhash)
        passhash:  Hash desde Setup → My Account → Passhash  (recomendado)
    """

    def __init__(self, host: str, username: str,
                 password: str = None, passhash: str = None):
        if not host or not username:
            raise PRTGAuthError("Se requieren host y username.")
        if not password and not passhash:
            raise PRTGAuthError("Debes proporcionar password o passhash.")

        self.base_url = host.rstrip("/")
        self.auth = {
            "username": username,
            "password": password or "",
            "passhash": passhash or "",
        }
        self.session = requests.Session()
        self.session.verify = False  # entornos internos con cert autofirmado

    # ── helpers ──────────────────────────────────────────────────────────────

    def _auth_params(self) -> dict:
        """Retorna los parámetros de autenticación para cada request."""
        params = {"username": self.auth["username"]}
        if self.auth["passhash"]:
            params["passhash"] = self.auth["passhash"]
        else:
            params["password"] = self.auth["password"]
        return params

    def get(self, endpoint: str, extra_params: dict = None) -> dict:
        """
        GET a la API JSON de PRTG.

        Args:
            endpoint:     Ruta relativa, ej. "/api/table.json"
            extra_params: Parámetros adicionales de la query string

        Returns:
            Respuesta JSON como dict

        Raises:
            PRTGConnectionError: Si no se puede conectar o el servidor retorna error.
        """
        url = urljoin(self.base_url, endpoint)
        params = {**self._auth_params(), **(extra_params or {})}

        try:
            resp = self.session.get(url, params=params, timeout=30)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.ConnectionError as e:
            raise PRTGConnectionError(f"No se pudo conectar a {self.base_url}: {e}") from e
        except requests.exceptions.HTTPError as e:
            raise PRTGConnectionError(f"Error HTTP {resp.status_code}: {e}") from e
        except requests.exceptions.JSONDecodeError as e:
            raise PRTGConnectionError(f"Respuesta inválida (no es JSON): {e}") from e
