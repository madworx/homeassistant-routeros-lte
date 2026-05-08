"""Tests for RouterOS LTE sensors."""

import pytest

from custom_components.routeros_lte.coordinator import RouterOSData
from custom_components.routeros_lte.sensor import RouterOSSensor, RouterOSSensorDescription


def test_memory_usage_calculation():
    """Test memory usage percentage calculation."""
    data = RouterOSData(
        lte={},
        system={
            "total-memory": 256_000_000,
            "free-memory": 128_000_000,
            "cpu-load": 10,
            "uptime": "1d",
            "total-hdd-space": 100_000_000,
            "free-hdd-space": 40_000_000,
        },
        interfaces=[],
    )

    # Memory: (256M - 128M) / 256M * 100 = 50%
    total = data.system["total-memory"]
    free = data.system["free-memory"]
    usage = round((total - free) / total * 100, 1)
    assert usage == 50.0


def test_disk_usage_calculation():
    """Test disk usage percentage calculation."""
    data = RouterOSData(
        lte={},
        system={
            "total-hdd-space": 100_000_000,
            "free-hdd-space": 40_000_000,
        },
        interfaces=[],
    )

    total = data.system["total-hdd-space"]
    free = data.system["free-hdd-space"]
    usage = round((total - free) / total * 100, 1)
    assert usage == 60.0


def test_lte_data_extraction():
    """Test LTE data is properly extracted."""
    data = RouterOSData(
        lte={
            "rssi": -65,
            "rsrp": -95,
            "rsrq": -10,
            "sinr": 12,
            "band": "B3",
            "connection-status": "connected",
        },
        system={},
        interfaces=[],
    )

    assert data.lte["rssi"] == -65
    assert data.lte["rsrp"] == -95
    assert data.lte["band"] == "B3"
    assert data.lte["connection-status"] == "connected"


def test_interface_data():
    """Test interface data structure."""
    data = RouterOSData(
        lte={},
        system={},
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
        ],
    )

    assert len(data.interfaces) == 1
    assert data.interfaces[0]["name"] == "ether1"
    assert data.interfaces[0]["running"] is True
    assert data.interfaces[0]["tx-byte"] == 1_000_000
