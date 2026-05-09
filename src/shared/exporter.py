"""
shared/exporter.py
==================
Exportador de reportes CSV para los resultados de auditoría PRTG.
Reutilizable por cualquier feature del proyecto.
"""

import csv
from datetime import datetime
from pathlib import Path


class CSVExporter:
    """
    Exporta resultados de auditoría a un archivo CSV consolidado.
    """

    FIELDNAMES = [
        "sitio", "tipo", "id", "nombre", "dispositivo_host",
        "grupo", "estado", "mensaje", "prioridad", "ultimo_valor", "hallazgo"
    ]

    def __init__(self, site_name: str, output_dir: str = "reports"):
        self.site_name = site_name
        self.output_dir = Path(output_dir)
        self.rows = []

    def _row(self, tipo: str, obj: dict, hallazgo: str, dispositivo_host_key: str = "device") -> dict:
        """Construye una fila del CSV a partir de un objeto PRTG."""
        return {
            "sitio":           self.site_name,
            "tipo":            tipo,
            "id":              obj.get("objid"),
            "nombre":          obj.get("name"),
            "dispositivo_host": obj.get(dispositivo_host_key) or obj.get("device") or obj.get("host"),
            "grupo":           obj.get("group") or obj.get("type"),
            "estado":          obj.get("status", ""),
            "mensaje":         obj.get("message", ""),
            "prioridad":       obj.get("priority", ""),
            "ultimo_valor":    obj.get("lastvalue", ""),
            "hallazgo":        hallazgo,
        }

    def add_devices(self, devices: list):
        for d in devices:
            self.rows.append(self._row("Dispositivo", d, "Inventario", "host"))

    def add_sensors_down(self, sensors: list):
        for s in sensors:
            self.rows.append(self._row("Sensor-Down", s, "CRITICO: Sensor caído"))

    def add_sensors_warning(self, sensors: list):
        for s in sensors:
            self.rows.append(self._row("Sensor-Warning", s, "ADVERTENCIA: Sensor en warning"))

    def add_sensors_no_limits(self, sensors: list):
        for s in sensors:
            self.rows.append(self._row("Sensor-SinUmbrales", s, "RIESGO: Sin umbrales de alerta configurados"))

    def add_sensors_paused(self, sensors: list):
        for s in sensors:
            self.rows.append(self._row("Sensor-Pausado", s, "REVISION: Sensor pausado — verificar justificación"))

    def add_users(self, users: list):
        for u in users:
            self.rows.append(self._row("Usuario", u, "Inventario de usuarios — verificar contraseñas por defecto", "email"))

    def add_notifications_paused(self, notifications: list):
        for n in notifications:
            self.rows.append(self._row("Notificacion-Pausada", n, "RIESGO: Notificación pausada — posible pérdida de alertas"))

    def export(self) -> str:
        """
        Escribe el archivo CSV con todos los hallazgos acumulados.

        Returns:
            Ruta absoluta del archivo generado.
        """
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        filename = self.output_dir / f"prtg_audit_{self.site_name}_{ts}.csv"

        with open(filename, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=self.FIELDNAMES)
            writer.writeheader()
            writer.writerows(self.rows)

        print(f"\n  ✅ Reporte exportado: {filename}")
        return str(filename)
