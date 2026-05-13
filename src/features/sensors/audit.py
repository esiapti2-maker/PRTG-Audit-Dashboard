"""
src/features/sensors/audit.py
==============================
Auditoría de sensores PRTG.

Resultado de SensorAudit.run():
    {
        "down":       list[dict],   # sensores en estado Down
        "warning":    list[dict],   # sensores en estado Warning
        "no_limits":  list[dict],   # sensores sin umbrales configurados
        "paused":     list[dict],   # sensores pausados (manual o scheduled)
    }

Cada dict incluye: id, nombre, device, group, probe, estado,
                   mensaje, ultimo_valor, tipo, activo
"""

from __future__ import annotations
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.core.client import PRTGClient

log = logging.getLogger(__name__)

_COLUMNS = "objid,sensor,device,group,probe,status,message,lastvalue,type,active"

# Valores de status que PRTG retorna como texto
_STATUS_DOWN    = ("down", "down (partial)", "down (acknowledged)")
_STATUS_WARNING = ("warning",)
_STATUS_PAUSED  = ("paused", "paused (by user)", "paused (by license)",
                   "paused (by dependency)", "paused (by schedule)")


class SensorAudit:
    """Clasifica sensores por estado y detecta falta de umbrales."""

    def __init__(self, client: "PRTGClient") -> None:
        self.client = client

    def run(self) -> dict[str, list[dict]]:
        log.info("[sensors] Consultando todos los sensores...")
        raw = self.client.get("/api/table.json", {
            "content": "sensors",
            "columns": _COLUMNS,
            "count":   50000,
            "output":  "json",
        })
        sensors = [self._normalize(s) for s in raw.get("sensors", [])]
        log.info("[sensors] %d sensores obtenidos", len(sensors))

        result = {
            "down":      [],
            "warning":   [],
            "no_limits": [],
            "paused":    [],
        }

        for s in sensors:
            st = s["estado"].lower()
            if st in _STATUS_DOWN:
                result["down"].append(s)
            elif st in _STATUS_WARNING:
                result["warning"].append(s)
            elif st in _STATUS_PAUSED:
                result["paused"].append(s)

            # Sensor sin umbrales: lastvalue presente pero no contiene rangos
            # Se detecta consultando los límites vía la API de objprop
            if self._has_no_limits(s):
                result["no_limits"].append(s)

        log.info(
            "[sensors] Down=%d | Warning=%d | Sin umbrales=%d | Pausados=%d",
            len(result["down"]), len(result["warning"]),
            len(result["no_limits"]), len(result["paused"]),
        )
        return result

    def _has_no_limits(self, sensor: dict) -> bool:
        """
        Heurística rápida: si el sensor tiene un valor numérico pero
        ningún límite configurado, se marca como sin umbral.

        Para una detección 100% exacta usa check_limits() con la
        endpoint /api/getobjectproperty.htm — pero eso requiere
        N llamadas (una por sensor). Esta versión usa la columna
        'lastvalue' como proxy: si tiene valor y el estado es OK,
        se consulta la propiedad limitenable.
        """
        # Solo aplica a sensores activos y no pausados
        if not sensor.get("activo", True):
            return False
        estado = sensor["estado"].lower()
        if estado in _STATUS_PAUSED:
            return False
        # Si el valor es vacío o N/A no podemos evaluar umbrales
        val = sensor.get("ultimo_valor", "").strip()
        if not val or val.lower() in ("", "no data", "n/a", "-"):
            return False
        # Consulta rápida de límites para este sensor
        try:
            return self._query_limits(sensor["id"])
        except Exception:
            return False

    def _query_limits(self, sensor_id: str) -> bool:
        """
        Consulta si el sensor tiene límites configurados.
        Retorna True si NO tiene límites (hallazgo de auditoría).
        """
        props = ["limitmaxerror", "limitmaxwarning",
                 "limitminwarning", "limitminerror"]
        for prop in props:
            try:
                resp = self.client.get("/api/getobjectproperty.htm", {
                    "id":       sensor_id,
                    "name":     prop,
                    "output":   "json",
                })
                val = str(resp.get("result", "")).strip()
                if val not in ("", "0", "None", "none"):
                    return False  # tiene al menos un límite → OK
            except Exception:
                continue
        return True  # ningún límite encontrado

    @staticmethod
    def _normalize(raw: dict) -> dict:
        return {
            "id":           raw.get("objid", ""),
            "nombre":       raw.get("sensor", ""),
            "device":       raw.get("device", ""),
            "grupo":        raw.get("group", ""),
            "probe":        raw.get("probe", ""),
            "estado":       raw.get("status", ""),
            "mensaje":      raw.get("message", ""),
            "ultimo_valor": raw.get("lastvalue", ""),
            "tipo":         raw.get("type", ""),
            "activo":       raw.get("active", True),
        }
