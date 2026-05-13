"""
src/shared/reporter.py
=======================
Generador de reporte HTML de auditoría PRTG.

Genera un archivo HTML standalone (sin dependencias externas) con:
  - Resumen ejecutivo / KPIs
  - Tabla de hallazgos por módulo
  - Checklist de auditoría
  - Metadata del reporte (sitio, fecha, usuario)

Uso:
    from src.shared.reporter import HTMLReporter
    r = HTMLReporter(site_name="Guadalajara", host="https://gdlprtg.gap.net")
    r.add_kpis(devices=120, sensors_down=3, ...)
    r.add_section("Sensores Down", rows, columns)
    r.add_checklist(checklist_results)
    path = r.export(output_dir="reports")
"""

import os
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional


class HTMLReporter:
    """
    Genera un reporte HTML completo de auditoría PRTG.
    El archivo es standalone — no necesita internet ni CSS externo.
    """

    def __init__(self, site_name: str, host: str, username: str = ""):
        self.site_name = site_name
        self.host = host
        self.username = username
        self.generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        self._kpis: Dict[str, Any] = {}
        self._sections: List[Dict[str, Any]] = []
        self._checklist: List[Dict[str, Any]] = []

    # ─── API pública ──────────────────────────────────────────────────────────

    def add_kpis(self, **kwargs):
        """Agrega KPIs al resumen. Ej: add_kpis(devices=120, sensors_down=3)"""
        self._kpis.update(kwargs)

    def add_section(
        self,
        title: str,
        rows: List[Dict[str, Any]],
        columns: Optional[List[str]] = None,
        severity: str = "info",  # info | warning | critical
    ):
        """
        Agrega una sección de tabla al reporte.

        Args:
            title:    Título de la sección
            rows:     Lista de dicts con los datos
            columns:  Lista de columnas a mostrar (None = todas)
            severity: 'info' | 'warning' | 'critical'
        """
        if not rows:
            return
        cols = columns or (list(rows[0].keys()) if rows else [])
        self._sections.append(
            {"title": title, "rows": rows, "columns": cols, "severity": severity}
        )

    def add_checklist(self, items: List[Dict[str, Any]]):
        """
        Agrega los resultados del checklist.

        Cada item debe tener:
            {"check": str, "passed": bool, "detail": str}
        """
        self._checklist = items

    def export(self, output_dir: str = "reports") -> str:
        """Genera el archivo HTML y devuelve su ruta."""
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = self.site_name.replace(" ", "_").replace("/", "-")
        filename = f"prtg_audit_{safe_name}_{ts}.html"
        path = os.path.join(output_dir, filename)

        html = self._build_html()
        with open(path, "w", encoding="utf-8") as f:
            f.write(html)

        return path

    # ─── Construcción HTML ───────────────────────────────────────────────────

    def _build_html(self) -> str:
        score = self._compute_score()
        score_color = "#437a22" if score >= 80 else ("#d19900" if score >= 50 else "#a12c2c")
        sections_html = "".join(self._render_section(s) for s in self._sections)
        checklist_html = self._render_checklist()
        kpis_html = self._render_kpis()

        return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Reporte de Auditoría PRTG — {self.site_name}</title>
<style>
  *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
  :root {{
    --bg: #f7f6f2; --surface: #ffffff; --border: rgba(0,0,0,.10);
    --text: #1a1a1a; --muted: #666; --faint: #999;
    --teal: #01696f; --teal-light: #e0f0ef;
    --warn: #d19900; --warn-light: #fdf8e6;
    --err: #a12c2c;  --err-light: #fdeaea;
    --ok: #437a22;   --ok-light: #edf7e6;
    --radius: 8px; --shadow: 0 1px 4px rgba(0,0,0,.08);
    font-size: 14px;
  }}
  body {{ font-family: 'Segoe UI', system-ui, sans-serif; background: var(--bg);
          color: var(--text); line-height: 1.5; }}
  .page {{ max-width: 1100px; margin: 0 auto; padding: 2rem 1.5rem; }}

  /* Header */
  .report-header {{ background: var(--teal); color: #fff; border-radius: var(--radius);
    padding: 1.5rem 2rem; margin-bottom: 1.5rem; display: flex;
    align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 1rem; }}
  .report-header h1 {{ font-size: 1.4rem; font-weight: 700; }}
  .report-header .meta {{ font-size: 0.85rem; opacity: .8; text-align: right; }}
  .score-badge {{ background: {score_color}; color: #fff; border-radius: 50px;
    padding: .3rem .9rem; font-size: 1.1rem; font-weight: 700; white-space: nowrap; }}

  /* KPIs */
  .kpis {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(160px,1fr));
    gap: 1rem; margin-bottom: 1.5rem; }}
  .kpi {{ background: var(--surface); border: 1px solid var(--border);
    border-radius: var(--radius); padding: 1rem; box-shadow: var(--shadow);
    text-align: center; }}
  .kpi .value {{ font-size: 2rem; font-weight: 700; color: var(--teal); }}
  .kpi .label {{ font-size: .75rem; color: var(--muted); margin-top: .2rem;
    text-transform: uppercase; letter-spacing: .04em; }}

  /* Sections */
  .section {{ background: var(--surface); border: 1px solid var(--border);
    border-radius: var(--radius); margin-bottom: 1.5rem;
    box-shadow: var(--shadow); overflow: hidden; }}
  .section-header {{ padding: .75rem 1rem; display: flex; align-items: center;
    gap: .5rem; border-bottom: 1px solid var(--border); }}
  .section-header h2 {{ font-size: 1rem; font-weight: 600; }}
  .badge {{ border-radius: 50px; padding: .15rem .55rem; font-size: .7rem;
    font-weight: 700; }}
  .badge.critical {{ background: var(--err-light); color: var(--err); }}
  .badge.warning  {{ background: var(--warn-light); color: var(--warn); }}
  .badge.info     {{ background: var(--teal-light); color: var(--teal); }}

  /* Table */
  .table-wrap {{ overflow-x: auto; }}
  table {{ width: 100%; border-collapse: collapse; font-size: .82rem; }}
  th {{ background: #f0f0ee; color: var(--muted); text-transform: uppercase;
    font-size: .68rem; letter-spacing: .05em; padding: .5rem .75rem;
    text-align: left; white-space: nowrap; }}
  td {{ padding: .45rem .75rem; border-top: 1px solid var(--border);
    vertical-align: top; word-break: break-word; max-width: 280px; }}
  tr:hover td {{ background: #f9f9f7; }}

  /* Checklist */
  .checklist {{ list-style: none; }}
  .checklist li {{ display: flex; align-items: flex-start; gap: .6rem;
    padding: .6rem 1rem; border-top: 1px solid var(--border); font-size: .88rem; }}
  .checklist li:first-child {{ border-top: none; }}
  .check-icon {{ font-size: 1rem; flex-shrink: 0; margin-top: .05rem; }}
  .check-detail {{ color: var(--muted); font-size: .78rem; margin-top: .1rem; }}

  /* Footer */
  .report-footer {{ text-align: center; color: var(--faint); font-size: .78rem;
    margin-top: 2rem; padding-top: 1rem; border-top: 1px solid var(--border); }}
  @media print {{
    .page {{ padding: 0; }}
    .section {{ break-inside: avoid; }}
  }}
</style>
</head>
<body>
<div class="page">

  <header class="report-header">
    <div>
      <h1>Reporte de Auditoría PRTG</h1>
      <div style="font-size:.9rem;opacity:.85;margin-top:.25rem">{self.site_name} &mdash; {self.host}</div>
    </div>
    <div style="display:flex;align-items:center;gap:1rem;flex-wrap:wrap;justify-content:flex-end">
      <div class="meta">
        Generado: {self.generated_at}<br>
        Usuario: {self.username or 'N/A'}
      </div>
      <div class="score-badge">Score {score}%</div>
    </div>
  </header>

  {kpis_html}
  {sections_html}
  {checklist_html}

  <footer class="report-footer">
    PRTG Audit Dashboard &mdash; Generado automáticamente &mdash; {self.generated_at}
  </footer>

</div>
</body>
</html>"""

    def _render_kpis(self) -> str:
        if not self._kpis:
            return ""
        items = "".join(
            f'<div class="kpi"><div class="value">{v}</div>'
            f'<div class="label">{k.replace("_", " ")}</div></div>'
            for k, v in self._kpis.items()
        )
        return f'<div class="kpis">{items}</div>'

    def _render_section(self, section: Dict[str, Any]) -> str:
        sev = section["severity"]
        rows = section["rows"]
        cols = section["columns"]
        badge = f'<span class="badge {sev}">{len(rows)} hallazgo{"s" if len(rows)!=1 else ""}</span>'

        header = (
            f'<div class="section-header">'  
            f'<h2>{section["title"]}</h2>{badge}'
            f'</div>'
        )

        th = "".join(f"<th>{c}</th>" for c in cols)
        tbody_rows = ""
        for row in rows:
            cells = "".join(f"<td>{row.get(c, '')}</td>" for c in cols)
            tbody_rows += f"<tr>{cells}</tr>"

        table = (
            f'<div class="table-wrap">'
            f"<table><thead><tr>{th}</tr></thead><tbody>{tbody_rows}</tbody></table>"
            f"</div>"
        )
        return f'<div class="section">{header}{table}</div>'

    def _render_checklist(self) -> str:
        if not self._checklist:
            return ""
        items_html = ""
        for item in self._checklist:
            icon = "✅" if item.get("passed") else "❌"
            detail = item.get("detail", "")
            detail_html = f'<div class="check-detail">{detail}</div>' if detail else ""
            items_html += (
                f'<li><span class="check-icon">{icon}</span>'
                f'<div><div>{item["check"]}</div>{detail_html}</div></li>'
            )
        return (
            '<div class="section">'
            '<div class="section-header"><h2>Checklist de Auditoría</h2></div>'
            f'<ul class="checklist">{items_html}</ul>'
            "</div>"
        )

    def _compute_score(self) -> int:
        """Calcula el score 0-100 basado en el checklist."""
        if not self._checklist:
            return 0
        passed = sum(1 for i in self._checklist if i.get("passed"))
        return round(passed / len(self._checklist) * 100)
