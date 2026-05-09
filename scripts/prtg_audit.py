#!/usr/bin/env python3
"""
PRTG Audit Script
=================
Script de auditoría para instancias PRTG multi-sitio.
Genera reportes CSV con estado de dispositivos, sensores caídos
y sensores sin umbrales configurados.

Uso:
    python prtg_audit.py --host https://mi-prtg-server --user admin --pass MiPass
    python prtg_audit.py --host https://mi-prtg --user admin --passhash 123456789

Autor: PRTG-Audit-Dashboard
Requerimientos: pip install requests
"""

import requests
import json
import csv
import argparse
import sys
from datetime import datetime
from pathlib import Path
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ─────────────────────────────────────────────
# CONFIGURACIÓN MULTI-SITIO
# Puedes definir múltiples instancias PRTG aquí
# ─────────────────────────────────────────────
SITES = [
    # {
    #     "name": "Sitio-Principal",
    #     "host": "https://prtg-site1.miempresa.com",
    #     "username": "admin",
    #     "password": "pass",   # usar password O passhash, no ambos
    #     "passhash": None,
    # },
    # {
    #     "name": "Sitio-DR",
    #     "host": "https://prtg-site2.miempresa.com",
    #     "username": "auditor",
    #     "password": None,
    #     "passhash": "1234567890",
    # },
]


class PRTGAudit:
    def __init__(self, host: str, username: str, password: str = None, passhash: str = None, site_name: str = "default"):
        self.host = host.rstrip("/")
        self.username = username
        self.password = password
        self.passhash = passhash
        self.site_name = site_name
        self.base_url = f"{self.host}/api"
        self.results = {
            "devices": [],
            "sensors_down": [],
            "sensors_warning": [],
            "sensors_no_limits": [],
            "sensors_paused_30d": [],
            "users": [],
            "notifications": [],
        }

    def _auth_params(self) -> dict:
        """Construye los parámetros de autenticación."""
        params = {"username": self.username, "output": "json"}
        if self.passhash:
            params["passhash"] = self.passhash
        else:
            params["password"] = self.password
        return params

    def _get(self, endpoint: str, extra_params: dict = {}) -> dict:
        """Realiza una llamada GET a la API de PRTG."""
        params = self._auth_params()
        params.update(extra_params)
        try:
            response = requests.get(
                f"{self.base_url}/{endpoint}",
                params=params,
                verify=False,
                timeout=30,
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.ConnectionError:
            print(f"[ERROR] No se puede conectar a {self.host}. Verifica la URL y conectividad.")
            sys.exit(1)
        except requests.exceptions.Timeout:
            print(f"[ERROR] Timeout al conectar a {self.host}.")
            sys.exit(1)
        except requests.exceptions.HTTPError as e:
            print(f"[ERROR] HTTP {response.status_code}: {e}")
            sys.exit(1)

    # ──────────────────────────────────────────
    # MÓDULOS DE AUDITORÍA
    # ──────────────────────────────────────────

    def audit_devices(self):
        """1. Inventario completo de dispositivos."""
        print(f"  → Obteniendo inventario de dispositivos...")
        data = self._get("table.json", {
            "content": "devices",
            "columns": "objid,name,host,group,status,message,tags",
        })
        self.results["devices"] = data.get("devices", [])
        print(f"     ✓ {len(self.results['devices'])} dispositivos encontrados.")

    def audit_sensors_down(self):
        """2. Sensores en estado Down o Warning."""
        print(f"  → Verificando sensores caídos / en warning...")
        # Status: 5=Down, 4=Warning, 14=DownAcknowledged
        for status_code in ["5", "4"]:
            data = self._get("table.json", {
                "content": "sensors",
                "columns": "objid,name,device,group,status,lastvalue,message,priority,tags",
                "filter_status": status_code,
            })
            sensors = data.get("sensors", [])
            if status_code == "5":
                self.results["sensors_down"] = sensors
            else:
                self.results["sensors_warning"] = sensors
        print(f"     ✓ Caídos: {len(self.results['sensors_down'])} | Warning: {len(self.results['sensors_warning'])}")

    def audit_sensors_no_limits(self):
        """
        3. Sensores sin umbrales configurados (riesgo de auditoría).
        Un sensor sin límites no alertará aunque el valor sea anómalo.
        """
        print(f"  → Verificando sensores sin umbrales definidos...")
        data = self._get("table.json", {
            "content": "sensors",
            "columns": "objid,name,device,group,status,lastvalue,priority,limitmaxerror,limitmaxwarning,limitmode",
        })
        sensors = data.get("sensors", [])
        # Sensores con limitmode=0 significa que los umbrales están desactivados
        risky = [
            s for s in sensors
            if str(s.get("limitmode", "0")) == "0"
            or s.get("limitmaxerror") in ["", None, "0"]
        ]
        self.results["sensors_no_limits"] = risky
        print(f"     ✓ {len(risky)} sensores sin umbrales de los {len(sensors)} totales.")

    def audit_sensors_paused(self):
        """4. Sensores pausados (status_raw=7). Pausas >30 días = riesgo de auditoría."""
        print(f"  → Verificando sensores pausados...")
        data = self._get("table.json", {
            "content": "sensors",
            "columns": "objid,name,device,group,status,message,tags",
            "filter_status": "7",  # 7 = Paused
        })
        self.results["sensors_paused_30d"] = data.get("sensors", [])
        print(f"     ✓ {len(self.results['sensors_paused_30d'])} sensores pausados.")

    def audit_users(self):
        """5. Lista de usuarios y roles (seguridad)."""
        print(f"  → Auditando usuarios y permisos...")
        data = self._get("table.json", {
            "content": "users",
            "columns": "objid,name,email,type",
        })
        self.results["users"] = data.get("users", [])
        print(f"     ✓ {len(self.results['users'])} usuarios encontrados.")

    def audit_notifications(self):
        """6. Notificaciones activas vs pausadas."""
        print(f"  → Auditando notificaciones/alertas...")
        data = self._get("table.json", {
            "content": "notifications",
            "columns": "objid,name,active",
        })
        self.results["notifications"] = data.get("notifications", [])
        active = [n for n in self.results["notifications"] if str(n.get("active", "0")) == "1"]
        paused = [n for n in self.results["notifications"] if str(n.get("active", "0")) != "1"]
        print(f"     ✓ Activas: {len(active)} | Pausadas: {len(paused)}")

    # ──────────────────────────────────────────
    # EXPORTACIÓN DE REPORTES
    # ──────────────────────────────────────────

    def export_csv(self, output_dir: str = "."):
        """Exporta todos los resultados a un CSV consolidado."""
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = Path(output_dir) / f"prtg_audit_{self.site_name}_{ts}.csv"
        filename.parent.mkdir(parents=True, exist_ok=True)

        rows = []

        # Dispositivos
        for d in self.results["devices"]:
            rows.append({
                "sitio": self.site_name,
                "tipo": "Dispositivo",
                "id": d.get("objid"),
                "nombre": d.get("name"),
                "dispositivo_host": d.get("host"),
                "grupo": d.get("group"),
                "estado": d.get("status"),
                "mensaje": d.get("message"),
                "prioridad": "",
                "ultimo_valor": "",
                "hallazgo": "Inventario",
            })

        # Sensores caídos
        for s in self.results["sensors_down"]:
            rows.append({
                "sitio": self.site_name,
                "tipo": "Sensor-Down",
                "id": s.get("objid"),
                "nombre": s.get("name"),
                "dispositivo_host": s.get("device"),
                "grupo": s.get("group"),
                "estado": s.get("status"),
                "mensaje": s.get("message"),
                "prioridad": s.get("priority"),
                "ultimo_valor": s.get("lastvalue"),
                "hallazgo": "CRITICO: Sensor caído",
            })

        # Sensores en warning
        for s in self.results["sensors_warning"]:
            rows.append({
                "sitio": self.site_name,
                "tipo": "Sensor-Warning",
                "id": s.get("objid"),
                "nombre": s.get("name"),
                "dispositivo_host": s.get("device"),
                "grupo": s.get("group"),
                "estado": s.get("status"),
                "mensaje": s.get("message"),
                "prioridad": s.get("priority"),
                "ultimo_valor": s.get("lastvalue"),
                "hallazgo": "ADVERTENCIA: Sensor en warning",
            })

        # Sensores sin umbrales
        for s in self.results["sensors_no_limits"]:
            rows.append({
                "sitio": self.site_name,
                "tipo": "Sensor-SinUmbrales",
                "id": s.get("objid"),
                "nombre": s.get("name"),
                "dispositivo_host": s.get("device"),
                "grupo": s.get("group"),
                "estado": s.get("status"),
                "mensaje": "",
                "prioridad": s.get("priority"),
                "ultimo_valor": s.get("lastvalue"),
                "hallazgo": "RIESGO: Sin umbrales de alerta configurados",
            })

        # Sensores pausados
        for s in self.results["sensors_paused_30d"]:
            rows.append({
                "sitio": self.site_name,
                "tipo": "Sensor-Pausado",
                "id": s.get("objid"),
                "nombre": s.get("name"),
                "dispositivo_host": s.get("device"),
                "grupo": s.get("group"),
                "estado": s.get("status"),
                "mensaje": s.get("message"),
                "prioridad": "",
                "ultimo_valor": "",
                "hallazgo": "REVISION: Sensor pausado — verificar justificación",
            })

        # Usuarios
        for u in self.results["users"]:
            rows.append({
                "sitio": self.site_name,
                "tipo": "Usuario",
                "id": u.get("objid"),
                "nombre": u.get("name"),
                "dispositivo_host": u.get("email"),
                "grupo": u.get("type"),
                "estado": "",
                "mensaje": "",
                "prioridad": "",
                "ultimo_valor": "",
                "hallazgo": "Inventario de usuarios — verificar contraseñas por defecto",
            })

        # Escribir CSV
        fieldnames = ["sitio", "tipo", "id", "nombre", "dispositivo_host", "grupo",
                      "estado", "mensaje", "prioridad", "ultimo_valor", "hallazgo"]

        with open(filename, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

        print(f"\n  ✅ Reporte exportado: {filename}")
        return str(filename)

    def print_summary(self):
        """Imprime un resumen ejecutivo en consola."""
        print(f"\n{'='*55}")
        print(f"  RESUMEN AUDITORÍA — {self.site_name}")
        print(f"{'='*55}")
        print(f"  Dispositivos totales       : {len(self.results['devices'])}")
        print(f"  Sensores CAÍDOS            : {len(self.results['sensors_down'])}")
        print(f"  Sensores en WARNING        : {len(self.results['sensors_warning'])}")
        print(f"  Sensores SIN UMBRALES      : {len(self.results['sensors_no_limits'])}")
        print(f"  Sensores PAUSADOS          : {len(self.results['sensors_paused_30d'])}")
        print(f"  Usuarios                   : {len(self.results['users'])}")
        notif_pausadas = [n for n in self.results['notifications'] if str(n.get('active', '0')) != '1']
        print(f"  Notificaciones PAUSADAS    : {len(notif_pausadas)}")
        print(f"{'='*55}")

    def run_full_audit(self, output_dir: str = "reports"):
        """Ejecuta todos los módulos de auditoría y exporta el reporte."""
        print(f"\n[PRTG-AUDIT] Iniciando auditoría de: {self.site_name} ({self.host})")
        print("-" * 55)
        self.audit_devices()
        self.audit_sensors_down()
        self.audit_sensors_no_limits()
        self.audit_sensors_paused()
        self.audit_users()
        self.audit_notifications()
        self.print_summary()
        return self.export_csv(output_dir=output_dir)


# ──────────────────────────────────────────────
# FUNCIÓN MULTI-SITIO: ejecutar contra varios PRTG
# ──────────────────────────────────────────────
def run_multi_site_audit(sites: list, output_dir: str = "reports"):
    """Audita múltiples instancias PRTG y genera reporte consolidado."""
    all_reports = []
    for site in sites:
        audit = PRTGAudit(
            host=site["host"],
            username=site["username"],
            password=site.get("password"),
            passhash=site.get("passhash"),
            site_name=site.get("name", site["host"]),
        )
        report_path = audit.run_full_audit(output_dir=output_dir)
        all_reports.append(report_path)

    print(f"\n[PRTG-AUDIT] Auditoría multi-sitio completada.")
    print(f"  Reportes generados en: {output_dir}/")
    for r in all_reports:
        print(f"    - {r}")


# ──────────────────────────────────────────────
# ENTRY POINT CLI
# ──────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="PRTG Audit Script — Auditoría de servidores PRTG para revisión interna"
    )
    parser.add_argument("--host", help="URL base del servidor PRTG (ej: https://prtg.miempresa.com)")
    parser.add_argument("--user", help="Usuario de PRTG")
    parser.add_argument("--pass", dest="password", help="Contraseña de PRTG")
    parser.add_argument("--passhash", help="Passhash de PRTG (alternativa a contraseña)")
    parser.add_argument("--site-name", default="sitio", help="Nombre descriptivo del sitio (default: sitio)")
    parser.add_argument("--output", default="reports", help="Directorio de salida para reportes (default: reports/)")
    parser.add_argument("--multi-site", action="store_true", help="Usar configuración multi-sitio definida en SITES[]")

    args = parser.parse_args()

    if args.multi_site:
        if not SITES:
            print("[ERROR] No hay sitios definidos en SITES[]. Edita el script y agrega tus instancias PRTG.")
            sys.exit(1)
        run_multi_site_audit(SITES, output_dir=args.output)
    elif args.host and args.user:
        if not args.password and not args.passhash:
            print("[ERROR] Debes proporcionar --pass o --passhash.")
            sys.exit(1)
        audit = PRTGAudit(
            host=args.host,
            username=args.user,
            password=args.password,
            passhash=args.passhash,
            site_name=args.site_name,
        )
        audit.run_full_audit(output_dir=args.output)
    else:
        parser.print_help()
        print("\nEjemplos de uso:")
        print("  python prtg_audit.py --host https://prtg.empresa.com --user admin --pass MiPass")
        print("  python prtg_audit.py --host https://prtg.empresa.com --user admin --passhash 1234567890")
        print("  python prtg_audit.py --multi-site --output /tmp/reportes")
