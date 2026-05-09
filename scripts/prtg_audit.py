#!/usr/bin/env python3
"""
scripts/prtg_audit.py
=====================
Entry point CLI para la auditoría PRTG.
Orquesta los módulos de src/features/ y genera el reporte CSV.

Estructura del proyecto (Híbrido Tipo + Feature):
    src/
      core/       — cliente API, autenticación, excepciones
      features/   — módulos independientes por funcionalidad
        devices/       inventario de dispositivos
        sensors/       down, warning, sin umbrales, pausados
        users/         usuarios y permisos
        notifications/ alertas activas vs pausadas
      shared/     — exportador CSV y logger reutilizables

Uso:
    python scripts/prtg_audit.py --host https://prtg.empresa.com --user admin --passhash 1234567890
    python scripts/prtg_audit.py --host https://prtg.empresa.com --user admin --pass MiPass
    python scripts/prtg_audit.py --multi-site --output /tmp/reportes

Requerimientos:
    pip install -r requirements.txt
"""

import sys
import argparse
from pathlib import Path

# Agregar raíz del proyecto al path para importar src/
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.core.client import PRTGClient
from src.core.exceptions import PRTGError
from src.features.devices.audit import DeviceAudit
from src.features.sensors.audit import SensorAudit
from src.features.users.audit import UserAudit
from src.features.notifications.audit import NotificationAudit
from src.shared.exporter import CSVExporter
from src.shared.logger import AuditLogger


# ─────────────────────────────────────────────
# CONFIGURACIÓN MULTI-SITIO
# Agrega aquí tus instancias PRTG para --multi-site
# ─────────────────────────────────────────────
SITES = [
    # {
    #     "name":     "Sitio-Principal",
    #     "host":     "https://prtg-site1.miempresa.com",
    #     "username": "admin",
    #     "password": None,
    #     "passhash": "1234567890",   # recomendado sobre password
    # },
    # {
    #     "name":     "Sitio-DR",
    #     "host":     "https://prtg-site2.miempresa.com",
    #     "username": "auditor",
    #     "password": None,
    #     "passhash": "0987654321",
    # },
]


def run_audit(host: str, username: str, password: str = None, passhash: str = None,
              site_name: str = "sitio", output_dir: str = "reports") -> str:
    """
    Ejecuta la auditoría completa para un sitio PRTG.

    Args:
        host:       URL base del servidor PRTG
        username:   Usuario de PRTG
        password:   Contraseña en texto plano (usar passhash es más seguro)
        passhash:   Hash de contraseña desde Setup → My Account → Passhash
        site_name:  Nombre descriptivo del sitio
        output_dir: Directorio donde se guardará el reporte CSV

    Returns:
        Ruta del archivo CSV generado
    """
    AuditLogger.header(site_name, host)

    # ── 1. Cliente base ──────────────────────
    client = PRTGClient(host=host, username=username, password=password, passhash=passhash)

    # ── 2. Ejecutar features ─────────────────
    devices    = DeviceAudit(client).run()
    sensors    = SensorAudit(client).run()
    users      = UserAudit(client).run()
    notifs     = NotificationAudit(client).run()

    # ── 3. Resumen en consola ─────────────────
    AuditLogger.summary(site_name, {
        "devices":              len(devices),
        "sensors_down":         len(sensors["down"]),
        "sensors_warning":      len(sensors["warning"]),
        "sensors_no_limits":    len(sensors["no_limits"]),
        "sensors_paused":       len(sensors["paused"]),
        "users":                len(users),
        "notifications_paused": len(notifs["paused"]),
    })

    # ── 4. Exportar CSV ───────────────────────
    exporter = CSVExporter(site_name=site_name, output_dir=output_dir)
    exporter.add_devices(devices)
    exporter.add_sensors_down(sensors["down"])
    exporter.add_sensors_warning(sensors["warning"])
    exporter.add_sensors_no_limits(sensors["no_limits"])
    exporter.add_sensors_paused(sensors["paused"])
    exporter.add_users(users)
    exporter.add_notifications_paused(notifs["paused"])
    return exporter.export()


def run_multi_site(sites: list, output_dir: str = "reports"):
    """Audita múltiples instancias PRTG en secuencia."""
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
            )
            reports.append(report)
        except PRTGError as e:
            print(f"[ERROR] Sitio {site.get('name', site['host'])}: {e}")
    AuditLogger.multi_site_done(output_dir, reports)


# ──────────────────────────────────────────────
# CLI ENTRY POINT
# ──────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="PRTG Audit Script — Auditoría de servidores PRTG para revisión interna"
    )
    parser.add_argument("--host",       help="URL base del servidor PRTG (ej: https://prtg.empresa.com)")
    parser.add_argument("--user",       help="Usuario de PRTG")
    parser.add_argument("--pass",       dest="password", help="Contraseña de PRTG")
    parser.add_argument("--passhash",   help="Passhash de PRTG (más seguro que --pass)")
    parser.add_argument("--site-name",  default="sitio", help="Nombre descriptivo del sitio (default: sitio)")
    parser.add_argument("--output",     default="reports", help="Directorio de salida para reportes (default: reports/)")
    parser.add_argument("--multi-site", action="store_true", help="Usar configuración multi-sitio definida en SITES[]")

    args = parser.parse_args()

    try:
        if args.multi_site:
            if not SITES:
                print("[ERROR] No hay sitios en SITES[]. Edita scripts/prtg_audit.py y agrega tus instancias.")
                sys.exit(1)
            run_multi_site(SITES, output_dir=args.output)

        elif args.host and args.user:
            if not args.password and not args.passhash:
                print("[ERROR] Debes proporcionar --pass o --passhash.")
                sys.exit(1)
            run_audit(
                host=args.host,
                username=args.user,
                password=args.password,
                passhash=args.passhash,
                site_name=args.site_name,
                output_dir=args.output,
            )
        else:
            parser.print_help()
            print("\nEjemplos de uso:")
            print("  python scripts/prtg_audit.py --host https://prtg.empresa.com --user admin --passhash 1234567890")
            print("  python scripts/prtg_audit.py --host https://prtg.empresa.com --user admin --pass MiPass")
            print("  python scripts/prtg_audit.py --multi-site --output /tmp/reportes")

    except PRTGError as e:
        print(f"[ERROR] {e}")
        sys.exit(1)
