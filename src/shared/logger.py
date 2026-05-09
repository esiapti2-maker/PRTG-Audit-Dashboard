"""
src/shared/logger.py
=====================
Logger de consola reutilizable para el CLI de auditoría.
Formatea mensajes de inicio, resumen y finalización multi-sitio.
"""
from datetime import datetime


class AuditLogger:

    @staticmethod
    def header(site_name: str, host: str):
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print()
        print("=" * 60)
        print(f"  PRTG Audit  |  {site_name}")
        print(f"  Host:  {host}")
        print(f"  Fecha: {ts}")
        print("=" * 60)

    @staticmethod
    def summary(site_name: str, counts: dict):
        print()
        print(f"  ── Resumen: {site_name} ──")
        labels = {
            "devices":              "Dispositivos totales",
            "sensors_down":         "Sensores DOWN",
            "sensors_warning":      "Sensores WARNING",
            "sensors_no_limits":    "Sensores sin umbrales",
            "sensors_paused":       "Sensores pausados",
            "users":                "Usuarios",
            "notifications_paused": "Notificaciones pausadas",
        }
        for key, count in counts.items():
            label = labels.get(key, key)
            flag  = " ⚠" if count > 0 and key != "devices" and key != "users" else ""
            print(f"    {label:<30} {count:>6}{flag}")

    @staticmethod
    def multi_site_done(output_dir: str, reports: list[str]):
        print()
        print("=" * 60)
        print(f"  Multi-sitio finalizado. {len(reports)} reporte(s) generado(s).")
        print(f"  Directorio: {output_dir}")
        for r in reports:
            print(f"    • {r}")
        print("=" * 60)
