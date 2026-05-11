#!/usr/bin/env python3
"""
scripts/prtg_audit.py
=====================
Entry point CLI para la auditoría PRTG.

Mejoras v2:
  - Carga automática de .env con python-dotenv
  - Logging estructurado con niveles configurables
  - --no-verify-ssl explícito (ya no hardcodeado)
  - --format csv|json|both
  - --dry-run para verificar conectividad sin generar reporte
  - --log-file para guardar logs en archivo
  - Multi-sitio lee variables de entorno automáticamente

Uso rápido:
    cp .env.example .env  # edita con tus credenciales
    python scripts/prtg_audit.py                        # lee desde .env
    python scripts/prtg_audit.py --host https://... --user admin --passhash XXXX
    python scripts/prtg_audit.py --multi-site
    python scripts/prtg_audit.py --dry-run
"""

import sys
import os
import argparse
import logging
from pathlib import Path

# Agregar raíz del proyecto al path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Cargar .env automáticamente si existe
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
except ImportError:
    pass  # python-dotenv opcional; parámetros CLI tienen prioridad

from src.core.client import PRTGClient
from src.core.exceptions import PRTGError
from src.features.devices.audit import DeviceAudit
from src.features.sensors.audit import SensorAudit
from src.features.users.audit import UserAudit
from src.features.notifications.audit import NotificationAudit
from src.shared.exporter import CSVExporter
from src.shared.logger import AuditLogger, setup_logging


def build_sites_from_env() -> list:
    """Construye la lista de sitios desde variables de entorno."""
    sites = []
    # Sitio principal
    host = os.getenv("PRTG_HOST")
    user = os.getenv("PRTG_USER")
    if host and user:
        sites.append({
            "name":     os.getenv("PRTG_SITE_NAME", "Principal"),
            "host":     host,
            "username": user,
            "password": os.getenv("PRTG_PASSWORD"),
            "passhash": os.getenv("PRTG_PASSHASH"),
        })
    # Sitio DR
    host_dr = os.getenv("PRTG_HOST_DR")
    user_dr = os.getenv("PRTG_USER_DR")
    if host_dr and user_dr:
        sites.append({
            "name":     os.getenv("PRTG_SITE_NAME_DR", "DR"),
            "host":     host_dr,
            "username": user_dr,
            "password": os.getenv("PRTG_PASSWORD_DR"),
            "passhash": os.getenv("PRTG_PASSHASH_DR"),
        })
    return sites


# ── Configuración multi-sitio — 13 instancias reales gap.net ─────────────────
# Rellena username y passhash de cada sitio antes de usar --multi-site.
# El passhash se obtiene en PRTG: Setup → My Account → Passhash
SITES_MANUAL = [
    {
        "name":     "SIAP Corporativo",
        "host":     "https://prtg.gap.net",
        "username": "",   # <-- completar
        "passhash": "",   # <-- completar
    },
    {
        "name":     "Aguascalientes",
        "host":     "https://aguprtg.gap.net",
        "username": "",
        "passhash": "",
    },
    {
        "name":     "Baja California",
        "host":     "https://bjxprtg.gap.net",
        "username": "",
        "passhash": "",
    },
    {
        "name":     "Guadalajara",
        "host":     "https://gdlprtg.gap.net",
        "username": "",
        "passhash": "",
    },
    {
        "name":     "Hermosillo",
        "host":     "https://hmoprtg.gap.net",
        "username": "",
        "passhash": "",
    },
    {
        "name":     "La Paz",
        "host":     "https://lapprtg.gap.net",
        "username": "",
        "passhash": "",
    },
    {
        "name":     "Los Mochis",
        "host":     "https://lmmprtg.gap.net",
        "username": "",
        "passhash": "",
    },
    {
        "name":     "Morelia",
        "host":     "https://mlmprtg.gap.net",
        "username": "",
        "passhash": "",
    },
    {
        "name":     "Mexicali",
        "host":     "https://mxlprtg.gap.net",
        "username": "",
        "passhash": "",
    },
    {
        "name":     "Puerto Vallarta",
        "host":     "https://pvrprtg.gap.net",
        "username": "",
        "passhash": "",
    },
    {
        "name":     "San José del Cabo",
        "host":     "https://sjdprtg.gap.net",
        "username": "",
        "passhash": "",
    },
    {
        "name":     "Tijuana",
        "host":     "https://tijprtg.gap.net",
        "username": "",
        "passhash": "",
    },
    {
        "name":     "Manzanillo",
        "host":     "https://zloprtg.gap.net",
        "username": "",
        "passhash": "",
    },
]


def run_audit(host: str, username: str, password: str = None, passhash: str = None,
              site_name: str = "sitio", output_dir: str = "reports",
              verify_ssl: bool = True, fmt: str = "csv",
              dry_run: bool = False) -> str:
    """
    Ejecuta la auditoría completa para un sitio PRTG.

    Returns:
        Ruta del archivo generado (vacío en dry_run)
    """
    log = logging.getLogger(__name__)
    AuditLogger.header(site_name, host)

    client = PRTGClient(
        host=host, username=username,
        password=password, passhash=passhash,
        verify_ssl=verify_ssl,
    )

    if dry_run:
        log.info("[dry-run] Verificando conectividad con %s...", host)
        try:
            data = client.get("/api/table.json", {
                "content": "sensors", "columns": "objid", "count": 1, "output": "json"
            })
            count = len(data.get("sensors", []))
            log.info("[dry-run] OK — API responde. Sensores visibles: %d", count)
        except PRTGError as e:
            log.error("[dry-run] FALLO: %s", e)
        return ""

    devices = DeviceAudit(client).run()
    sensors = SensorAudit(client).run()
    users   = UserAudit(client).run()
    notifs  = NotificationAudit(client).run()

    AuditLogger.summary(site_name, {
        "devices":              len(devices),
        "sensors_down":         len(sensors["down"]),
        "sensors_warning":      len(sensors["warning"]),
        "sensors_no_limits":    len(sensors["no_limits"]),
        "sensors_paused":       len(sensors["paused"]),
        "users":                len(users),
        "notifications_paused": len(notifs["paused"]),
    })

    exporter = CSVExporter(site_name=site_name, output_dir=output_dir)
    exporter.add_devices(devices)
    exporter.add_sensors_down(sensors["down"])
    exporter.add_sensors_warning(sensors["warning"])
    exporter.add_sensors_no_limits(sensors["no_limits"])
    exporter.add_sensors_paused(sensors["paused"])
    exporter.add_users(users)
    exporter.add_notifications_paused(notifs["paused"])
    return exporter.export(fmt=fmt)


def run_multi_site(sites: list, output_dir: str = "reports",
                   verify_ssl: bool = True, fmt: str = "csv",
                   dry_run: bool = False):
    log = logging.getLogger(__name__)
    reports = []
    for site in sites:
        try:
            report = run_audit(
                host=site["host"],
                username=site["username"],
                password=site.get("password"),
                passhash=site.get("passhash"),
                site_name=site.get("name", site["host"]),
                output_dir=output_dir,
                verify_ssl=verify_ssl,
                fmt=fmt,
                dry_run=dry_run,
            )
            if report:
                reports.append(report)
        except PRTGError as e:
            log.error("Sitio %s: %s", site.get("name", site["host"]), e)
    AuditLogger.multi_site_done(output_dir, reports)


# ── CLI ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="PRTG Audit Script — Genera reportes de auditoría para servidores PRTG",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  python scripts/prtg_audit.py                                 # Lee desde .env
  python scripts/prtg_audit.py --host https://gdlprtg.gap.net --user admin --passhash XXXX
  python scripts/prtg_audit.py --format both --output ./reports
  python scripts/prtg_audit.py --dry-run
  python scripts/prtg_audit.py --multi-site --format json
"""
    )

    # Credenciales
    parser.add_argument("--host",     help="URL base del servidor PRTG")
    parser.add_argument("--user",     help="Usuario de PRTG")
    parser.add_argument("--pass",     dest="password", help="Contraseña de PRTG")
    parser.add_argument("--passhash", help="Passhash (más seguro que --pass)")
    parser.add_argument("--site-name",default="sitio", help="Nombre del sitio (default: sitio)")

    # Opciones de salida
    parser.add_argument("--output",   default=os.getenv("PRTG_OUTPUT_DIR", "reports"),
                        help="Directorio de salida (default: reports/)")
    parser.add_argument("--format",   choices=["csv", "json", "both"], default="csv",
                        help="Formato de exportación: csv | json | both (default: csv)")
    parser.add_argument("--log-file", help="Archivo de log adicional")
    parser.add_argument("--log-level",default=os.getenv("PRTG_LOG_LEVEL", "INFO"),
                        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
                        help="Nivel de logging (default: INFO)")

    # Opciones de modo
    parser.add_argument("--multi-site",  action="store_true",
                        help="Auditar todos los sitios definidos en .env o SITES_MANUAL")
    parser.add_argument("--dry-run",     action="store_true",
                        help="Verificar conectividad sin generar reporte")
    parser.add_argument("--no-verify-ssl", action="store_true",
                        default=(os.getenv("PRTG_NO_VERIFY_SSL", "false").lower() == "true"),
                        help="Desactivar verificación SSL (solo entornos con cert autofirmado)")

    args = parser.parse_args()
    setup_logging(level=args.log_level, log_file=args.log_file)
    verify_ssl = not args.no_verify_ssl

    try:
        if args.multi_site:
            sites = SITES_MANUAL or build_sites_from_env()
            if not sites:
                print("[ERROR] No hay sitios configurados. Define PRTG_HOST/PRTG_USER en .env "
                      "o agrega entradas a SITES_MANUAL en el script.")
                sys.exit(1)
            run_multi_site(sites, output_dir=args.output, verify_ssl=verify_ssl,
                           fmt=args.format, dry_run=args.dry_run)

        else:
            # Resolución de credenciales: CLI > .env
            host     = args.host     or os.getenv("PRTG_HOST")
            user     = args.user     or os.getenv("PRTG_USER")
            passhash = args.passhash or os.getenv("PRTG_PASSHASH")
            password = args.password or os.getenv("PRTG_PASSWORD")
            site     = args.site_name if args.site_name != "sitio" else os.getenv("PRTG_SITE_NAME", "sitio")

            if not host or not user:
                parser.print_help()
                print("\n[ERROR] Debes proporcionar --host y --user, o configurar .env")
                sys.exit(1)
            if not password and not passhash:
                print("[ERROR] Debes proporcionar --pass o --passhash (o PRTG_PASSHASH en .env)")
                sys.exit(1)

            run_audit(host=host, username=user, password=password, passhash=passhash,
                      site_name=site, output_dir=args.output, verify_ssl=verify_ssl,
                      fmt=args.format, dry_run=args.dry_run)

    except PRTGError as e:
        logging.getLogger(__name__).error("%s", e)
        sys.exit(1)
