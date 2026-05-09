"""Fixtures for RouterOS LTE tests."""

import sys
from unittest.mock import MagicMock, patch

import pytest

# Remove editable install path hooks that confuse HA's integration loader
sys.path[:] = [p for p in sys.path if "__path_hook__" not in p]

from custom_components.routeros_lte.coordinator import RouterOSData  # noqa: E402


@pytest.fixture
def mock_routeros_data():
    """Return mock RouterOS data."""
    return RouterOSData(
        lte={
            "rssi": -65,
            "rsrp": -95,
            "rsrq": -10,
            "sinr": 12,
            "band": "B3",
            "cell-id": "12345",
            "lac": "678",
            "mcc": "244",
            "mnc": "05",
            "connection-status": "connected",
            "imei": "860561044494441",
            "iccid": "89460851027003480376",
            "current-operator": "Telenor SE",
            "session-uptime": "1h30m",
            "cqi": 11,
            "ca-band": "B7@20Mhz earfcn: 2850 phy-cellid: 6",
            "enb-id": 131380,
            "phy-cellid": 84,
            "data-class": "LTE",
        },
        system={
            "cpu-load": 15,
            "free-memory": 128_000_000,
            "total-memory": 256_000_000,
            "uptime": "3d12h05m",
            "free-hdd-space": 50_000_000,
            "total-hdd-space": 128_000_000,
            "board-name": "RBM33G",
            "version": "7.14",
        },
        interfaces=[
            {
                "name": "ether1",
                "type": "ether",
                "running": True,
                "tx-byte": 1_000_000,
                "rx-byte": 2_000_000,
                "tx-packet": 5000,
                "rx-packet": 8000,
            },
            {
                "name": "lte1",
                "type": "lte",
                "running": True,
                "tx-byte": 500_000,
                "rx-byte": 3_000_000,
                "tx-packet": 2000,
                "rx-packet": 6000,
            },
        ],
        routerboard={
            "serial-number": "HHD0AAWV5ZG",
            "model": "D53G-5HacD2HnD",
            "current-firmware": "7.18.2",
            "upgrade-firmware": "7.22.2",
            "firmware-type": "ipq4000L",
        },
        identity="MikroTik",
        wifi_client_count=3,
    )


@pytest.fixture
def mock_api():
    """Return a mock librouteros API."""
    api = MagicMock()
    api.close = MagicMock()

    def api_call(path, **kwargs):
        if path == "/interface/print":
            return [
                {"name": "ether1", "type": "ether", "running": True},
                {"name": "lte1", "type": "lte", "running": True},
            ]
        if path == "/system/routerboard/print":
            return [
                {
                    "serial-number": "HHD0AAWV5ZG",
                    "model": "D53G-5HacD2HnD",
                    "current-firmware": "7.18.2",
                    "upgrade-firmware": "7.22.2",
                }
            ]
        if path == "/system/identity/print":
            return [{"name": "MikroTik"}]
        if path == "/interface/wireless/registration-table/print":
            return [{"mac-address": "AA:BB:CC:DD:EE:FF"}]
        return []

    api.side_effect = api_call
    return api


@pytest.fixture
def mock_connect(mock_api):
    """Patch librouteros.connect."""
    with patch(
        "custom_components.routeros_lte.config_flow.librouteros.connect",
        return_value=mock_api,
    ) as mock:
        yield mock
