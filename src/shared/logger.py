"""
src/shared/logger.py
=====================
Logger reutilizable para el CLI de auditoría.

Mejoras v2:
  - Usa el módulo `logging` estándar en lugar de print() directo
  - setup_logging() configura nivel y salida a archivo opcional
  - AuditLogger mantiene la misma interfaz pública para compatibilidad
"""
import logging
from datetime import datetime


def setup_logging(level: str = "INFO", log_file: str = None):
    """
    Configura el logger raíz del proyecto.

    Args:
        level:    Nivel de verbosidad: DEBUG | INFO | WARNING | ERROR
        log_file: Ruta opcional a archivo de log (además de consola)
    """
    numeric = getattr(logging, level.upper(), logging.INFO)
    handlers = [logging.StreamHandler()]
    if log_file:
        handlers.append(logging.FileHandler(log_file, encoding="utf-8"))

    logging.basicConfig(
        level=numeric,
        format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=handlers,
    )


log = logging.getLogger(__name__)


class AuditLogger:
    """Interfaz de alto nivel para mensajes de auditoría."""

    @staticmethod
    def header(site_name: str, host: str):
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log.info("=" * 60)
        log.info("  PRTG Audit  |  %s", site_name)
        log.info("  Host:  %s", host)
        log.info("  Fecha: %s", ts)
        log.info("=" * 60)

    @staticmethod
    def summary(site_name: str, counts: dict):
        labels = {
            "devices":              "Dispositivos totales",
            "sensors_down":         "Sensores DOWN",
            "sensors_warning":      "Sensores WARNING",
            "sensors_no_limits":    "Sensores sin umbrales",
            "sensors_paused":       "Sensores pausados",
            "users":                "Usuarios",
            "notifications_paused": "Notificaciones pausadas",
        }
        log.info("  ── Resumen: %s ──", site_name)
        for key, count in counts.items():
            label = labels.get(key, key)
            lvl   = logging.WARNING if (count > 0 and key not in ("devices", "users")) else logging.INFO
            log.log(lvl, "    %-30s %6d%s", label, count,
                    "  ⚠" if lvl == logging.WARNING else "")

    @staticmethod
    def multi_site_done(output_dir: str, reports: list):
        log.info("=" * 60)
        log.info("  Multi-sitio finalizado. %d reporte(s) generado(s).", len(reports))
        log.info("  Directorio: %s", output_dir)
        for r in reports:
            log.info("    • %s", r)
        log.info("=" * 60)
