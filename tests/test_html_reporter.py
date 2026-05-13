"""
tests/test_html_reporter.py
============================
Unit tests para HTMLReporter.
Ejecuta con: pytest tests/test_html_reporter.py -v
"""

import os
import tempfile
import pytest

from src.shared.reporter import HTMLReporter


SAMPLE_ROWS = [
    {"ID": 101, "Sensor": "CPU Load", "Estado": "Down", "Dispositivo": "SRV-CORE-01"},
    {"ID": 102, "Sensor": "Disk Free", "Estado": "Down", "Dispositivo": "SRV-CORE-02"},
]

SAMPLE_CHECKLIST = [
    {"check": "Sensores con umbrales configurados", "passed": True, "detail": "100% de sensores tienen límites"},
    {"check": "Sin usuarios con acceso de solo lectura a todo", "passed": False, "detail": "3 usuarios con acceso global"},
    {"check": "Grupos sin dispositivos", "passed": True, "detail": "Sin grupos vacíos"},
]


@pytest.fixture
def reporter():
    return HTMLReporter(
        site_name="Test Site",
        host="https://test.prtg.local",
        username="auditor",
    )


class TestHTMLReporterBuild:
    """Verifica la construcción correcta del HTML."""

    def test_html_contains_site_name(self, reporter):
        reporter.add_kpis(dispositivos=50)
        html = reporter._build_html()
        assert "Test Site" in html

    def test_html_contains_host(self, reporter):
        html = reporter._build_html()
        assert "https://test.prtg.local" in html

    def test_html_contains_score(self, reporter):
        reporter.add_checklist(SAMPLE_CHECKLIST)
        html = reporter._build_html()
        assert "Score" in html
        assert "67%" in html  # 2/3 passed

    def test_score_zero_without_checklist(self, reporter):
        html = reporter._build_html()
        assert "Score 0%" in html

    def test_kpis_rendered(self, reporter):
        reporter.add_kpis(dispositivos=50, sensores_down=3)
        html = reporter._build_html()
        assert "50" in html
        assert "dispositivos" in html.lower()

    def test_section_rendered(self, reporter):
        reporter.add_section("Sensores Down", SAMPLE_ROWS, severity="critical")
        html = reporter._build_html()
        assert "Sensores Down" in html
        assert "CPU Load" in html
        assert "SRV-CORE-01" in html

    def test_empty_section_skipped(self, reporter):
        reporter.add_section("Vacía", [], severity="warning")
        html = reporter._build_html()
        assert "Vacía" not in html

    def test_checklist_rendered(self, reporter):
        reporter.add_checklist(SAMPLE_CHECKLIST)
        html = reporter._build_html()
        assert "Checklist de Auditoría" in html
        assert "✅" in html
        assert "❌" in html

    def test_valid_html_structure(self, reporter):
        html = reporter._build_html()
        assert html.startswith("<!DOCTYPE html>")
        assert "</html>" in html
        assert "<body" in html
        assert "</body>" in html


class TestHTMLReporterExport:
    """Verifica la exportación a archivo."""

    def test_export_creates_file(self, reporter):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = reporter.export(output_dir=tmpdir)
            assert os.path.isfile(path)

    def test_export_filename_contains_site(self, reporter):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = reporter.export(output_dir=tmpdir)
            assert "Test_Site" in os.path.basename(path)

    def test_export_filename_ends_html(self, reporter):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = reporter.export(output_dir=tmpdir)
            assert path.endswith(".html")

    def test_export_creates_output_dir(self, reporter):
        with tempfile.TemporaryDirectory() as tmpdir:
            nested = os.path.join(tmpdir, "new", "reports")
            path = reporter.export(output_dir=nested)
            assert os.path.isdir(nested)
            assert os.path.isfile(path)

    def test_exported_file_not_empty(self, reporter):
        reporter.add_kpis(total=10)
        reporter.add_section("Sensores", SAMPLE_ROWS)
        with tempfile.TemporaryDirectory() as tmpdir:
            path = reporter.export(output_dir=tmpdir)
            assert os.path.getsize(path) > 1000
