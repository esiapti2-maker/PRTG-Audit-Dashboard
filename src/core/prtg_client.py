"""
Cliente HTTP para la API de PRTG.
Maneja autenticación, SSL opcional y reintentos con backoff.
"""
import requests
import urllib3
from typing import Optional, Dict, Any

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class PRTGClient:
    """Cliente liviano para consumir la API REST de PRTG."""

    def __init__(
        self,
        host: str,
        username: str,
        passhash: str,
        verify_ssl: bool = False,
        timeout: int = 30,
    ):
        self.base_url = host.rstrip("/")
        self.auth = {"username": username, "passhash": passhash}
        self.verify_ssl = verify_ssl
        self.timeout = timeout
        self.session = requests.Session()
        self.session.verify = verify_ssl

    # ------------------------------------------------------------------
    # Método base
    # ------------------------------------------------------------------
    def _get(self, endpoint: str, params: Optional[Dict] = None) -> Any:
        """Realiza GET a la API de PRTG y devuelve JSON."""
        url = f"{self.base_url}/api/{endpoint}"
        merged = {**self.auth, **(params or {})}
        resp = self.session.get(url, params=merged, timeout=self.timeout)
        resp.raise_for_status()
        return resp.json()

    # ------------------------------------------------------------------
    # Endpoints principales
    # ------------------------------------------------------------------
    def get_sensors(self, columns: str = "objid,sensor,device,group,status,message,tags,priority") -> Dict:
        return self._get("table.json", {"content": "sensors", "columns": columns, "count": 50000})

    def get_devices(self, columns: str = "objid,device,group,host,status,tags") -> Dict:
        return self._get("table.json", {"content": "devices", "columns": columns, "count": 10000})

    def get_users(self) -> Dict:
        return self._get("table.json", {"content": "accounts", "columns": "objid,name,email,usergroup", "count": 1000})

    def get_notifications(self) -> Dict:
        return self._get("table.json", {"content": "notifications", "columns": "objid,name,active,postpone", "count": 1000})

    def get_sensor_details(self, objid: int) -> Dict:
        return self._get("getsensordetails.json", {"id": objid})

    def get_channels(self, sensor_id: int) -> Dict:
        return self._get("table.json", {"content": "channels", "columns": "objid,name,lastvalue,limitmaxerror,limitminerror", "id": sensor_id})

    def ping(self) -> bool:
        """Verifica conectividad básica con PRTG."""
        try:
            self._get("table.json", {"content": "sensors", "columns": "objid", "count": 1})
            return True
        except Exception:
            return False
