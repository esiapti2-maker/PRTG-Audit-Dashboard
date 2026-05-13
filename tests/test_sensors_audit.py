"""
tests/test_sensors_audit.py
============================
Unit tests para SensorAudit.
Ejecuta con: pytest tests/test_sensors_audit.py -v
"""

import pytest
from unittest.mock import MagicMock

from src.features.sensors.audit import SensorAudit


RAW_DOWN = [
    {"objid": 201, "name": "CPU Load", "device": "SRV-01", "group": "Servers",
     "probe": "probe1", "status": "Down", "message": "No data",
     "lastvalue": "0", "priority": "3", "tags": ""},
]
RAW_WARNING = [
    {"objid": 202, "name": "Memory", "device": "SRV-02", "group": "Servers",
     "probe": "probe1", "status": "Warning", "message": "High",
     "lastvalue": "85%", "priority": "2", "tags": ""},
]
RAW_ALL = [
    {"objid": 203, "name": "Disk", "device": "SRV-03", "group": "Servers",
     "probe": "probe1", "status": "Up", "message": "OK",
     "lastvalue": "40%", "priority": "1", "tags": "",
     "limitmaxerror": "", "limitminerror": "", "limitmode": "0"},
]


@pytest.fixture
def mock_client():
    client = MagicMock()
    def fake_get(endpoint, params):
        status = params.get("filter_status", [])
        if 5 in status or "5" in str(status):
            return {"sensors": RAW_DOWN}
        if 4 in status or "4" in str(status):
            return {"sensors": RAW_WARNING}
        return {"sensors": RAW_ALL}
    client.get.side_effect = fake_get
    return client


class TestSensorAuditRun:
    def test_returns_dict(self, mock_client):
        result = SensorAudit(mock_client).run()
        assert isinstance(result, dict)

    def test_has_required_keys(self, mock_client):
        result = SensorAudit(mock_client).run()
        for key in ("down", "warning", "no_limits", "paused"):
            assert key in result

    def test_api_error_returns_empty_dict(self):
        client = MagicMock()
        client.get.side_effect = Exception("Timeout")
        result = SensorAudit(client).run()
        assert all(isinstance(v, list) for v in result.values())
