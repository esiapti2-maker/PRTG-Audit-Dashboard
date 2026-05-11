"""
src/shared/exporter.py
========================
Exportador de resultados de auditoría.

Soporta:
  - CSV  — un archivo con múltiples secciones separadas por encabezado
  - JSON — un archivo estructurado por sección
  - both — genera ambos formatos en la misma ejecución

El nombre de archivo incluye sitio + timestamp para historial acumulado.
"""
from __future__ import annotations
import csv
import json
import os
import logging
from datetime import datetime
from pathlib import Path

log = logging.getLogger(__name__)


class CSVExporter:
    """
    Acumula hallazgos por sección y los exporta a CSV y/o JSON.

    Uso:
        exp = CSVExporter(site_name="Guadalajara", output_dir="reports")
        exp.add_devices(devices)
        exp.add_sensors_down(down_list)
        exp.add_sensors_no_limits(no_limits_list)
        exp.add_users(users)
        exp.add_notifications_paused(paused_notifs)
        path = exp.export(fmt="csv")   # "csv" | "json" | "both"
    """

    _SECTIONS = [
        "devices",
        "sensors_down",
        "sensors_warning",
        "sensors_no_limits",
        "sensors_paused",
        "users",
        "notifications_paused",
    ]

    def __init__(self, site_name: str = "sitio", output_dir: str = "reports") -> None:
        self.site_name  = site_name
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._data: dict[str, list] = {s: [] for s in self._SECTIONS}
        self._ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    # ── add methods ──────────────────────────────────────────────────────────

    def add_devices(self,             rows: list[dict]) -> None: self._data["devices"]              = rows
    def add_sensors_down(self,        rows: list[dict]) -> None: self._data["sensors_down"]         = rows
    def add_sensors_warning(self,     rows: list[dict]) -> None: self._data["sensors_warning"]      = rows
    def add_sensors_no_limits(self,   rows: list[dict]) -> None: self._data["sensors_no_limits"]    = rows
    def add_sensors_paused(self,      rows: list[dict]) -> None: self._data["sensors_paused"]       = rows
    def add_users(self,               rows: list[dict]) -> None: self._data["users"]                = rows
    def add_notifications_paused(self,rows: list[dict]) -> None: self._data["notifications_paused"] = rows

    # ── export ───────────────────────────────────────────────────────────────

    def export(self, fmt: str = "csv") -> str:
        """
        Exporta los hallazgos al formato indicado.

        Args:
            fmt: "csv" | "json" | "both"

        Returns:
            Ruta del archivo CSV generado (o ruta CSV en modo both)
        """
        safe_name = self.site_name.replace(" ", "_").lower()
        csv_path  = self.output_dir / f"prtg_audit_{safe_name}_{self._ts}.csv"
        json_path = self.output_dir / f"prtg_audit_{safe_name}_{self._ts}.json"

        if fmt in ("csv", "both"):
            self._write_csv(csv_path)
        if fmt in ("json", "both"):
            self._write_json(json_path)

        if fmt == "json":
            return str(json_path)
        return str(csv_path)

    # ── private writers ──────────────────────────────────────────────────────

    def _write_csv(self, path: Path) -> None:
        """Escribe todas las secciones en un CSV con encabezados de sección."""
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)

            # Encabezado global
            writer.writerow([f"PRTG Audit Report — {self.site_name}"])
            writer.writerow([f"Generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"])
            writer.writerow([])

            for section in self._SECTIONS:
                rows = self._data[section]
                label = section.replace("_", " ").title()
                writer.writerow([f"=== {label} ({len(rows)} registros) ==="])

                if not rows:
                    writer.writerow(["(sin hallazgos)"])
                    writer.writerow([])
                    continue

                headers = list(rows[0].keys())
                # Excluir campos internos del CSV
                headers = [h for h in headers if h not in ("status_raw", "is_paused", "priority_raw")]
                writer.writerow(headers)

                for row in rows:
                    writer.writerow([row.get(h, "") for h in headers])

                writer.writerow([])

        log.info("CSV exportado: %s", path)
        print(f"  [exporter] CSV → {path}")

    def _write_json(self, path: Path) -> None:
        """Escribe todas las secciones como JSON estructurado."""
        payload = {
            "site":      self.site_name,
            "generated": datetime.now().isoformat(),
            "summary": {
                s: len(self._data[s]) for s in self._SECTIONS
            },
            "data": self._data,
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)

        log.info("JSON exportado: %s", path)
        print(f"  [exporter] JSON → {path}")
