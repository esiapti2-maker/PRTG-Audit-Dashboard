"""
Proxy Flask — resuelve CORS entre el dashboard HTML y la API de PRTG.

Endpoints:
  POST /api/audit          — ejecuta auditoría completa y retorna JSON
  POST /api/proxy          — reenvía petición arbitraria a PRTG (pass-through)
  GET  /api/health         — healthcheck
  GET  /api/export/csv     — descarga el último CSV generado
"""
from __future__ import annotations

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, request, jsonify, Response
from flask_cors import CORS

from src.shared.config import config
from src.core.prtg_client import PRTGClient
from src.core.audit_engine import AuditEngine
from src.features.export import findings_to_csv, save_csv

app = Flask(__name__)
app.secret_key = config.secret_key
CORS(app, origins=config.cors_origins)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _client_from_request() -> PRTGClient:
    """
    Construye un PRTGClient desde el JSON del request.
    Si no viene host/user/passhash en el body, usa las variables de entorno.
    """
    data = request.get_json(force=True, silent=True) or {}
    host = data.get("host") or config.default_prtg_host
    username = data.get("username") or config.default_prtg_user
    passhash = data.get("passhash") or config.default_prtg_passhash
    verify_ssl = data.get("verify_ssl", config.default_verify_ssl)
    timeout = int(data.get("timeout", 30))

    if not all([host, username, passhash]):
        raise ValueError("Faltan credenciales: host, username, passhash")

    return PRTGClient(host=host, username=username, passhash=passhash,
                      verify_ssl=verify_ssl, timeout=timeout)


# ---------------------------------------------------------------------------
# Rutas
# ---------------------------------------------------------------------------

@app.get("/api/health")
def health():
    return jsonify({"status": "ok", "version": "1.0.0"})


@app.post("/api/audit")
def full_audit():
    """
    Ejecuta los 6 módulos de auditoría y devuelve resultados consolidados.
    Body JSON (opcional si están seteadas las vars de entorno):
      { host, username, passhash, site_name, modules, verify_ssl }
    """
    try:
        data = request.get_json(force=True, silent=True) or {}
        client = _client_from_request()
        engine = AuditEngine(client)
        site_name = data.get("site_name", "default")
        modules = data.get("modules", ["inventory", "critical", "paused",
                                        "no_thresholds", "users", "notifications"])

        results: dict = {"site": site_name, "modules": {}}

        if "inventory" in modules:
            results["modules"]["inventory"] = engine.audit_inventory()
        if "critical" in modules:
            results["modules"]["critical"] = engine.audit_critical_sensors()
        if "paused" in modules:
            results["modules"]["paused"] = engine.audit_paused_sensors()
        if "no_thresholds" in modules:
            results["modules"]["no_thresholds"] = engine.audit_no_thresholds()
        if "users" in modules:
            results["modules"]["users"] = engine.audit_users()
        if "notifications" in modules:
            results["modules"]["notifications"] = engine.audit_notifications()

        # Generar CSV si se pide
        if data.get("export_csv"):
            all_findings = []
            for mod_results in results["modules"].values():
                if isinstance(mod_results, list):
                    all_findings.extend(mod_results)
            csv_path = save_csv(all_findings, config.export_dir, site_name)
            results["csv_exported_to"] = csv_path

        return jsonify(results)

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Error interno: {str(e)}"}), 500


@app.post("/api/proxy")
def prtg_proxy():
    """
    Pass-through: el dashboard envía { host, username, passhash, endpoint, params }.
    El proxy reenvía a PRTG y devuelve el JSON resultante.
    Resuelve el bloqueo CORS del browser.
    """
    try:
        data = request.get_json(force=True, silent=True) or {}
        client = _client_from_request()
        endpoint = data.get("endpoint", "table.json")
        params = data.get("params", {})
        result = client._get(endpoint, params)
        return jsonify(result)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Error al conectar con PRTG: {str(e)}"}), 502


@app.post("/api/export/csv")
def export_csv():
    """
    Recibe lista de hallazgos y devuelve un CSV descargable.
    Body: { findings: [...], site_name: "..." }
    """
    try:
        data = request.get_json(force=True, silent=True) or {}
        findings = data.get("findings", [])
        site_name = data.get("site_name", "export")
        content = findings_to_csv(findings, site_name)
        return Response(
            content,
            mimetype="text/csv",
            headers={"Content-Disposition": f'attachment; filename="prtg_audit_{site_name}.csv"'}
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    app.run(
        host=config.proxy_host,
        port=config.proxy_port,
        debug=config.proxy_debug,
    )
