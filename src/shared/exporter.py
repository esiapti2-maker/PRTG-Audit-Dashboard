"""
src/shared/exporter.py
=======================
Exportador multi-formato: CSV y JSON.
Recibe los resultados de todos los features y los escribe en disco,
listo para revisión de auditoría interna o carga en el dashboard HTML.

Mejoras v2:
  - Soporte JSON con --format json  (para el dashboard y otras integraciones)
  - CSV con encoding UTF-8 BOM (compatible con Excel español)
  - Método export_json() independiente
"""
import csv
import json
import logging
from datetime import datetime
from pathlib import Path

log = logging.getLogger(__name__)


class CSVExporter:
    """
    Acumula hallazgos y exporta a CSV y/o JSON.

    Args:
        site_name:  Nombre del sitio PRTG auditado
        output_dir: Directorio de salida
    """

    SECTION_HEADERS = {
        "devices":              ["Sección", "ID", "Dispositivo", "Host", "Grupo", "Probe", "Estado", "Mensaje"],
        "sensors_down":        ["Sección", "ID", "Sensor", "Dispositivo", "Grupo", "Probe", "Estado", "Último Valor", "Prioridad", "Mensaje"],
        "sensors_warning":     ["Sección", "ID", "Sensor", "Dispositivo", "Grupo", "Probe", "Estado", "Último Valor", "Prioridad", "Mensaje"],
        "sensors_no_limits":   ["Sección", "ID", "Sensor", "Dispositivo", "Grupo", "Probe", "Estado", "Último Valor", "Prioridad", "Mensaje"],
        "sensors_paused":      ["Sección", "ID", "Sensor", "Dispositivo", "Grupo", "Probe", "Estado", "Último Valor", "Prioridad", "Mensaje"],
        "users":               ["Sección", "ID", "Nombre", "Email", "Grupo", "Grupo Usuario"],
        "notifications_paused":["Sección", "ID", "Nombre", "Activa", "Estado", "Último Trigger"],
    }

    def __init__(self, site_name: str, output_dir: str = "reports"):
        self.site_name  = site_name
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._data: dict = {}   # almacén para export JSON
        self._sections: list   = []

    # ── add_* ─────────────────────────────────────────────────────────────────

    def add_devices(self, devices: list):
        self._data["devices"] = devices
        rows = [["INVENTARIO", d["id"], d["name"], d["host"],
                 d["group"], d["probe"], d["status"], d["message"]]
                for d in devices]
        self._sections.append(("devices", self.SECTION_HEADERS["devices"], rows))

    def add_sensors_down(self, sensors: list):
        self._data["sensors_down"] = sensors
        self._add_sensor_section("sensors_down", "SENSOR DOWN", sensors)

    def add_sensors_warning(self, sensors: list):
        self._data["sensors_warning"] = sensors
        self._add_sensor_section("sensors_warning", "SENSOR WARNING", sensors)

    def add_sensors_no_limits(self, sensors: list):
        self._data["sensors_no_limits"] = sensors
        self._add_sensor_section("sensors_no_limits", "SIN UMBRALES", sensors)

    def add_sensors_paused(self, sensors: list):
        self._data["sensors_paused"] = sensors
        self._add_sensor_section("sensors_paused", "SENSOR PAUSADO", sensors)

    def add_users(self, users: list):
        self._data["users"] = users
        rows = [["USUARIO", u["id"], u["name"], u["email"],
                 u["group"], u["user_group"]] for u in users]
        self._sections.append(("users", self.SECTION_HEADERS["users"], rows))

    def add_notifications_paused(self, notifs: list):
        self._data["notifications_paused"] = notifs
        rows = [["NOTIF PAUSADA", n["id"], n["name"], n["active"],
                 n["status"], n["last_trigger"]] for n in notifs]
        self._sections.append(("notifications_paused",
                                self.SECTION_HEADERS["notifications_paused"], rows))

    # ── export ────────────────────────────────────────────────────────────────

    def export(self, fmt: str = "csv") -> str:
        """
        Exporta los datos al formato indicado.

        Args:
            fmt: "csv" (default) | "json" | "both"

        Returns:
            Ruta del archivo principal generado (CSV o JSON)
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base      = self.output_dir / f"prtg_audit_{self.site_name}_{timestamp}"
        result    = ""

        if fmt in ("csv", "both"):
            result = self._write_csv(str(base) + ".csv")
        if fmt in ("json", "both"):
            json_path = self._write_json(str(base) + ".json")
            if fmt == "json":
                result = json_path

        return result

    def _write_csv(self, path: str) -> str:
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            for _key, headers, rows in self._sections:
                writer.writerow(headers)
                writer.writerows(rows)
                writer.writerow([])
        log.info("[exporter] CSV guardado: %s", path)
        return path

    def _write_json(self, path: str) -> str:
        """
        Genera un JSON estructurado compatible con el dashboard HTML.

        Formato:
        {
          "meta": { "site": "...", "generated_at": "..." },
          "summary": { "devices": N, "sensors_down": N, ... },
          "devices": [...],
          "sensors_down": [...],
          ...
        }
        """
        output = {
            "meta": {
                "site":         self.site_name,
                "generated_at": datetime.now().isoformat(),
            },
            "summary": {
                k: len(v) for k, v in self._data.items()
            },
        }
        output.update(self._data)

        with open(path, "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        log.info("[exporter] JSON guardado: %s", path)
        return path

    # ── private ───────────────────────────────────────────────────────────────

    def _add_sensor_section(self, key: str, label: str, sensors: list):
        rows = [[label, s["id"], s["name"], s["device"], s[