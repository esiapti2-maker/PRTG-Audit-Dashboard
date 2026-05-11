"""
src/shared/logger.py
======================
Logging estructurado para el proceso de auditoría.
Provee helpers visuales (header, summary, multi-site done)
que se imprimen en consola al ejecutar el script.
"""
from __future__ import annotations
import logging
import sys


def setup_logging(level: str = "INFO", log_file: str | None = None) -> None:
    """
    Configura el logger raíz con formato enriquecido.

    Args:
        level:    DEBUG | INFO | WARNING | ERROR
        log_file: Ruta opcional de archivo de log adicional
    """
    fmt     = "%(asctime)s  %(levelname)-8s  %(name)s — %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"

    handlers: list[logging.Handler] = [logging.StreamHandler(sys.stdout)]
    if log_file:
        handlers.append(logging.FileHandler(log_file, encoding="utf-8"))

    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format=fmt,
        datefmt=datefmt,
        handlers=handlers,
        force=True,
    )


class AuditLogger:
    """Métodos de utilidad para imprimir bloques visuales en consola."""

    _SEP = "─" * 60

    @classmethod
    def header(cls, site_name: str, host: str) -> None:
        print()
        print(cls._SEP)
        print(f"  PRTG Audit — {site_name}")
        print(f"  Host: {host}")
        print(cls._SEP)

    @classmethod
    def summary(cls, site_name: str, counts: dict) -> None:
        print()
        print(f"  ── Resumen: {site_name} ──")
        for key, val in counts.items():
            label = key.replace("_", " ").capitalize()
            marker = " ⚠" if val > 0 and key != "devices" else ""
            print(f"     {label:<28} {val:>5}{marker}")
        print()

    @classmethod
    def multi_site_done(cls, output_dir: str, reports: list[str]) -> None:
        print()
        print(cls._SEP)
        print(f"  Multi-sitio completado — {len(reports)} reporte(s) en '{output_dir}'")
        for r in reports:
            print(f"    • {r}")
        print(cls._SEP)
        print()
