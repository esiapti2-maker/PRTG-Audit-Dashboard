"""
src/core/client.py
==================
Cliente HTTP base para la API JSON de PRTG.
Toda comunicación con el servidor pasa por aquí.

Mejoras v2:
  - Reintentos automáticos con backoff exponencial (3 intentos)
  - Validación de URL con mensaje descriptivo
  - SSL verify configurable (advertencia explícita si se desactiva)
  - Timeout configurable
"""
import warnings
import logging
import requests
from urllib.parse import urljoin, urlparse
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
from .exceptions import PRTGAuthError, PRTGConnectionError

log = logging.getLogger(__name__)


class PRTGClient:
    """
    Encapsula las credenciales y realiza GET requests a la API de PRTG.

    Args:
        host:       URL base, ej. https://prtg.empresa.com
        username:   Usuario de PRTG
        password:   Contraseña en texto plano  (opcional si usas passhash)
        passhash:   Hash desde Setup → My Account → Passhash  (recomendado)
        verify_ssl: True verifica certificados (default). False para certs autofirmados.
        timeout:    Segundos por request (default 30).
        retries:    Intentos ante fallo de conexión (default 3).
    """

    def __init__(self, host: str, username: str,
                 password: str = None, passhash: str = None,
                 verify_ssl: bool = True, timeout: int = 30, retries: int = 3):

        if not host or not username:
            raise PRTGAuthError("Se requieren host y username.")
        if not password and not passhash:
            raise PRTGAuthError("Debes proporcionar password o passhash.")

        # Validar formato de URL
        parsed = urlparse(host)
        if not parsed.scheme or not parsed.netloc:
            raise PRTGAuthError(
                f"URL inválida: '{host}'. Debe incluir esquema, ej: https://prtg.empresa.com"
            )

        self.base_url   = host.rstrip("/")
        self.timeout    = timeout
        self.verify_ssl = verify_ssl
        self.auth = {
            "username": username,
            "password": password or "",
            "passhash": passhash or "",
        }

        # Advertencia explícita si SSL está desactivado
        if not verify_ssl:
            warnings.warn(
                f"[PRTG] verify_ssl=False para {host}. "
                "Los certificados TLS NO serán verificados (solo usar en redes internas).",
                stacklevel=2
            )
            requests.packages.urllib3.disable_warnings()

        # Session con reintentos automáticos
        self.session = requests.Session()
        self.session.verify = verify_ssl
        retry_strategy = Retry(
            total=retries,
            backoff_factor=1,          # 1s, 2s, 4s entre intentos
            status_forcelist=[500, 502, 503, 504],
            allowed_methods=["GET"],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("https://", adapter)
        self.session.mount("http://",  adapter)

        log.debug("PRTGClient listo: host=%s user=%s ssl=%s retries=%d",
                  self.base_url, username, verify_ssl, retries)

    # ── helpers ──────────────────────────────────────────────────────────────

    def _auth_params(self) -> dict:
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
        url    = urljoin(self.base_url + "/", endpoint.lstrip("/"))
        params = {**self._auth_params(), **(extra_params or {})}
        log.debug("GET %s  params=%s", url, {k: v for k, v in params.items() if k not in ("password", "passhash")})

        try:
            resp = self.session.get(url, params=params, timeout=self.timeout)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.ConnectionError as e:
            raise PRTGConnectionError(f"No se pudo conectar a {self.base_url}: {e}") from e
        except requests.exceptions.HTTPError as e:
            raise PRTGConnectionError(f"Error HTTP {resp.status_code} en {url}: {e}") from e
        except requests.exceptions.JSONDecodeError as e:
            raise PRTGConnectionError(f"Respuesta inválida (no es JSON) de {url}: {e}") from e
        except requests.exceptions.Timeout:
            raise PRTGConnectionError(f"Timeout ({self.timeout}s) al conectar con {self.base_url}.")
