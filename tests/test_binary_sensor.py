"""Tests for RouterOS LTE binary sensors."""

from unittest.mock import MagicMock

from custom_components.routeros_lte.binary_sensor import RouterOSLTEConnectionSensor
from custom_components.routeros_lte.coordinator import RouterOSData


def _make_sensor(lte_data: dict) -> RouterOSLTEConnectionSensor:
    """Create a sensor with mocked coordinator."""
    coordinator = MagicMock()
    coordinator.data = RouterOSData(lte=lte_data, system={}, interfaces=[])
    coordinator.entry.entry_id = "test_entry"
    sensor = RouterOSLTEConnectionSensor(coordinator)
    return sensor


def test_lte_connected_status_connected():
    """Test LTE sensor is on when connection-status is 'connected'."""
    sensor = _make_sensor({"connection-status": "connected"})
    assert sensor.is_on is True


def test_lte_connected_status_attached():
    """Test LTE sensor is on when status is 'attached' (RouterOS v7)."""
    sensor = _make_sensor({"status": "attached"})
    assert sensor.is_on is True


def test_lte_connected_status_disconnected():
    """Test LTE sensor is off when connection-status is 'disconnected'."""
    sensor = _make_sensor({"connection-status": "disconnected"})
    assert sensor.is_on is False


def test_lte_connected_status_searching():
    """Test LTE sensor is off when status is 'searching'."""
    sensor = _make_sensor({"status": "searching"})
    assert sensor.is_on is False


def test_lte_connected_status_none():
    """Test LTE sensor returns None when no status key is present."""
    sensor = _make_sensor({"rssi": -65})
    assert sensor.is_on is None


def test_lte_connected_prefers_connection_status():
    """Test connection-status is preferred over status."""
    sensor = _make_sensor({"connection-status": "connected", "status": "searching"})
    assert sensor.is_on is True


def test_lte_connected_status_with_qualifier():
    """Test LTE sensor handles 'connected (home)' and similar suffixed statuses."""
    sensor = _make_sensor({"status": "connected (home)"})
    assert sensor.is_on is True

    sensor = _make_sensor({"status": "connected (roaming)"})
    assert sensor.is_on is True

    sensor = _make_sensor({"connection-status": "attached (home)"})
    assert sensor.is_on is True
