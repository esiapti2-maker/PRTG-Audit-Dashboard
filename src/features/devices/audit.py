"""
src/features/devices/audit.py
==============================
Feature: Auditoría de dispositivos.

Detecta:
  - Dispositivos sin sensores asignados (blind devices)
  - Dispositivos con todos sus sensores pausados
  - Dispositivos sin IP/hostname configurado
  - Cuenta total y breakdown por grupo/probe
"""
from __future__ import annotations
from src.core.client import PRTGClient
from src.core.constants import API_TABLE, DEVICE_COLS
from src.core.exceptions import PRTGDataError


class DeviceAudit:
    """
    Audita dispositivos PRTG.

    Cada registro devuelto incluye:
      id, name, host, group, probe, sensor_count,
      issue  (descripción si hay problema, vacío si OK)

    Uso:
        devices = DeviceAudit(client).run()
    """

    def __init__(self, client: PRTGClient) -> None:
        self.client = client

    def run(self) -> list[dict]:
        print("  [devices] Obteniendo dispositivos...")
        data = self.client.get(API_TABLE, {
            "content": "devices",
            "columns": DEVICE_COLS,
            "count":   10_000,
            "output":  "json",
        })

        raw = data.get("devices", [])
        if not isinstance(raw, list):
            raise PRTGDataError("La API no devolvió una lista de dispositivos.")

        result = [self._parse(d) for d in raw]

        blind      = sum(1 for d in result if "sin sensores" in d["issue"])
        no_host    = sum(1 for d in result if "sin IP" in d["issue"])
        print(
            f"  [devices] Total={len(result)} | "
            f"Sin sensores={blind} | Sin IP={no_host}"
        )
        return result

    # ── helpers ──────────────────────────────────────────────────────────────

    def _parse(self, d: dict) -> dict:
        sensor_count = int(d.get("totalsens", 0) or 0)
        host         = str(d.get("host", "")).strip()

        issues = []
        if sensor_count == 0:
            issues.append("Sin sensores asignados (blind device)")
        if not host:
            issues.append("Sin IP/hostname configurado")

        return {
            "id":           d.get("objid", ""),
            "name":         d.get("device", ""),
            "host":         host or "(no definido)",
            "group":        d.get("group", ""),
            "probe":        d.get("probe", ""),
            "sensor_count": sensor_count,
            "sensor_down":  int(d.get("downsens",   0) or 0),
            "sensor_warn":  int(d.get("warnsens",   0) or 0),
            "sensor_pause": int(d.get("pausedsens", 0) or 0),
            "status":       d.get("status", ""),
            "issue":        " | ".join(issues) if issues else "",
        }
