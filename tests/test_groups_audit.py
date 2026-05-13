"""
tests/test_groups_audit.py
==========================
Unit tests para GroupAudit.
Ejecuta con: pytest tests/test_groups_audit.py -v
"""

import pytest
from unittest.mock import MagicMock, patch

from src.features.groups.audit import GroupAudit, GroupAuditResult
from src.features.groups.types import GroupRecord


# ─── Fixtures ────────────────────────────────────────────────────────────────

RAW_GROUPS = [
    {
        "objid": 1, "name": "Corporativo", "parentid": 0,
        "probe": "probe1", "totaldev": 10, "totalsens": 45,
        "status": "Up", "tags": "core,prod",
    },
    {
        "objid": 2, "name": "Vacío", "parentid": 1,
        "probe": "probe1", "totaldev": 0, "totalsens": 0,
        "status": "Up", "tags": "",
    },
    {
        "objid": 3, "name": "Pausado Producción", "parentid": 1,
        "probe": "probe1", "totaldev": 5, "totalsens": 20,
        "status": "Paused by User", "tags": "prod",
    },
    {
        "objid": 4, "name": "New Group", "parentid": 0,
        "probe": "probe2", "totaldev": 3, "totalsens": 12,
        "status": "Up", "tags": "",
    },
]


@pytest.fixture
def mock_client():
    client = MagicMock()
    client.get.return_value = {"groups": RAW_GROUPS}
    return client


# ─── Tests ────────────────────────────────────────────────────────────────────

class TestGroupAuditParse:
    """Verifica el parseo correcto de registros crudos de la API."""

    def test_parse_normal_group(self):
        record = GroupAudit._parse(RAW_GROUPS[0])
        assert record.objid == 1
        assert record.name == "Corporativo"
        assert record.device_count == 10
        assert record.sensor_count == 45
        assert record.has_no_devices is False
        assert record.has_no_sensors is False
        assert record.is_paused is False
        assert "core" in record.tags
        assert "prod" in record.tags

    def test_parse_empty_group(self):
        record = GroupAudit._parse(RAW_GROUPS[1])
        assert record.has_no_devices is True
        assert record.has_no_sensors is True

    def test_parse_paused_group(self):
        record = GroupAudit._parse(RAW_GROUPS[2])
        assert record.is_paused is True
        assert record.has_no_devices is False

    def test_parse_no_tags(self):
        record = GroupAudit._parse(RAW_GROUPS[3])
        assert record.tags == []


class TestGroupAuditRun:
    """Verifica la clasificación de hallazgos en run()."""

    def test_run_returns_result(self, mock_client):
        ga = GroupAudit(mock_client)
        result = ga.run()
        assert isinstance(result, GroupAuditResult)

    def test_total_groups(self, mock_client):
        result = GroupAudit(mock_client).run()
        assert result.total == 4

    def test_empty_groups_detected(self, mock_client):
        result = GroupAudit(mock_client).run()
        assert len(result.empty_groups) == 1
        assert result.empty_groups[0].name == "Vacío"

    def test_paused_groups_detected(self, mock_client):
        result = GroupAudit(mock_client).run()
        assert len(result.paused_groups) == 1
        assert result.paused_groups[0].name == "Pausado Producción"

    def test_generic_names_detected(self, mock_client):
        result = GroupAudit(mock_client).run()
        assert len(result.generic_names) == 1
        assert result.generic_names[0].name == "New Group"

    def test_has_issues_true(self, mock_client):
        result = GroupAudit(mock_client).run()
        assert result.has_issues is True

    def test_api_error_returns_empty(self):
        client = MagicMock()
        client.get.side_effect = Exception("Timeout")
        result = GroupAudit(client).run()
        assert result.total == 0


class TestGroupAuditRecord:
    """Verifica el método to_dict() del tipo GroupRecord."""

    def test_to_dict_keys(self):
        record = GroupAudit._parse(RAW_GROUPS[0])
        d = record.to_dict()
        expected_keys = {"ID", "Nombre", "Dispositivos", "Sensores", "Estado", "Tags"}
        assert expected_keys.issubset(d.keys())

    def test_to_dict_tags_joined(self):
        record = GroupAudit._parse(RAW_GROUPS[0])
        assert "core" in record.to_dict()["Tags"]
        assert "prod" in record.to_dict()["Tags"]
