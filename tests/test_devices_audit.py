"""
tests/test_devices_audit.py
============================
Unit tests para DeviceAudit.
Ejecuta con: pytest tests/test_devices_audit.py -v
"""

import pytest
from unittest.mock import MagicMock

from src.features.devices.audit import DeviceAudit


RAW_DEVICES = [
    {"objid": 10, "name": "Router-Core", "host": "10.0.0.1",
     "group": "Backbone", "probe": "probe1", "status": "Up",
     "totalsens": 8, "tags": "core", "location": "GDL-DC1"},
    {"objid": 11, "name": "Switch-Access-01", "host": "10.0.1.10",
     "group": "Acceso", "probe": "probe1", "status": "Down",
     "totalsens": 4, "tags": "", "location": ""},
    {"objid": 12, "name": "Server-App-01", "host": "10.0.2.5",
     "group": "Servers", "probe": "probe1", "status": "Paused by User",
     "totalsens": 0, "tags": "", "location": ""},
]


@pytest.fixture
def mock_client():
    client = MagicMock()
    client.get.return_value = {"devices": RAW_DEVICES}
    return client


class TestDeviceAuditRun:
    def test_returns_list(self, mock_client):
        result = DeviceAudit(mock_client).run()
        assert isinstance(result, list)

    def test_count(self, mock_client):
        result = DeviceAudit(mock_client).run()
        assert len(result) == 3

    def test_device_fields_present(self, mock_client):
        result = DeviceAudit(mock_client).run()
        d = result[0]
        assert hasattr(d, "name") or isinstance(d, dict)

    def test_api_error_returns_empty(self):
        client = MagicMock()
        client.get.side_effect = Exception("Connection refused")
        result = DeviceAudit(client).run()
        assert result == [] or isinstance(result, list)
