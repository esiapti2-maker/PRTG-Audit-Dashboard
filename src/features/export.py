"""
Exportación de resultados de auditoría a CSV.
"""
from __future__ import annotations
import csv
import io
from datetime import datetime
from typing import List, Dict, Any


def findings_to_csv(findings: List[Dict[str, Any]], site_name: str = "") -> str:
    """
    Convierte una lista de hallazgos a string CSV.
    Retorna el contenido como string listo para escribir a archivo o enviar por HTTP.
    """
    if not findings:
        return ""

    # Recolectar todas las columnas posibles
    fieldnames = list(dict.fromkeys(k for row in findings for k in row.keys()))
    # Agregar metadatos de auditoría al inicio
    meta_fields = ["audit_site", "audit_timestamp"]
    for f in meta_fields:
        if f not in fieldnames:
            fieldnames.insert(0, f)

    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()
    for row in findings:
        writer.writerow({"audit_site": site_name, "audit_timestamp": ts, **row})

    return output.getvalue()


def save_csv(findings: List[Dict[str, Any]], path: str, site_name: str = "") -> str:
    """Escribe el CSV a disco y retorna la ruta del archivo generado."""
    from pathlib import Path
    from datetime import datetime

    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = p / f"prtg_audit_{site_name}_{ts}.csv"
    content = findings_to_csv(findings, site_name)
    filename.write_text(content, encoding="utf-8")
    return str(filename)
