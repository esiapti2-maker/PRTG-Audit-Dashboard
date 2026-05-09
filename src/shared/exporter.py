"""
src/shared/exporter.py
=======================
Exportador CSV reutilizable.
Recibe los resultados de todos los features y los escribe en un único CSV
organizado por secciones, listo para revisión de auditoría interna.
"""
import csv
from datetime import datetime
from pathlib import Path


class CSVExporter:
    """
    Acumula hallazgos de todos los features y genera un CSV final.

    Args:
        site_name:  Nombre del sitio PRTG auditado (aparece en el nombre del archivo)
        output_dir: Directorio donde se guardará el reporte
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
        self._sections: list[tuple[str, list[str], list[list]]] = []

    # ── add_* methods ─────────────────────────────────────────────────────────

    def add_devices(self, devices: list[dict]):
        rows = [["INVENTARIO", d["id"], d["name"], d["host"],
                 d["group"], d["probe"], d["status"], d["message"]]
                for d in devices]
        self._sections.append(("devices", self.SECTION_HEADERS["devices"], rows))

    def add_sensors_down(self, sensors: list[dict]):
        self._add_sensor_section("sensors_down", "SENSOR DOWN", sensors)

    def add_sensors_warning(self, sensors: list[dict]):
        self._add_sensor_section("sensors_warning", "SENSOR WARNING", sensors)

    def add_sensors_no_limits(self, sensors: list[dict]):
        self._add_sensor_section("sensors_no_limits", "SIN UMBRALES", sensors)

    def add_sensors_paused(self, sensors: list[dict]):
        self._add_sensor_section("sensors_paused", "SENSOR PAUSADO", sensors)

    def add_users(self, users: list[dict]):
        rows = [["USUARIO", u["id"], u["name"], u["email"],
                 u["group"], u["user_group"]]
                for u in users]
        self._sections.append(("users", self.SECTION_HEADERS["users"], rows))

    def add_notifications_paused(self, notifs: list[dict]):
        rows = [["NOTIF PAUSADA", n["id"], n["name"], n["active"],
                 n["status"], n["last_trigger"]]
                for n in notifs]
        self._sections.append(("notifications_paused",
                                self.SECTION_HEADERS["notifications_paused"], rows))

    # ── export ────────────────────────────────────────────────────────────────

    def export(self) -> str:
        """Escribe todas las secciones en un único CSV y retorna la ruta."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename  = self.output_dir / f"prtg_audit_{self.site_name}_{timestamp}.csv"

        with open(filename, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            for _key, headers, rows in self._sections:
                writer.writerow(headers)
                writer.writerows(rows)
                writer.writerow([])  # línea en blanco entre secciones

        print(f"\n  [exporter] Reporte guardado: {filename}")
        return str(filename)

    # ── private ───────────────────────────────────────────────────────────────

    def _add_sensor_section(self, key: str, label: str, sensors: list[dict]):
        rows = [[label, s["id"], s["name"], s["device"], s["group"],
                 s["probe"], s["status"], s["lastvalue"], s["priority"], s["message"]]
                for s in sensors]
        self._sections.append((key, self.SECTION_HEADERS[key], rows))
