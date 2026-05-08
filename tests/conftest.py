"""Fixtures for RouterOS LTE tests."""

from unittest.mock import MagicMock, patch

import pytest

from custom_components.routeros_lte.coordinator import RouterOSData


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
    )


@pytest.fixture
def mock_api():
    """Return a mock librouteros API."""
    api = MagicMock()
    api.close = MagicMock()
    return api


@pytest.fixture
def mock_connect(mock_api):
    """Patch librouteros.connect."""
    with patch(
        "custom_components.routeros_lte.config_flow.librouteros.connect",
        return_value=mock_api,
    ) as mock:
        yield mock
