"""Tests for RouterOS LTE sensors."""

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch

from custom_components.routeros_lte.coordinator import RouterOSCoordinator, RouterOSData
from custom_components.routeros_lte.sensor import (
    LTE_SENSORS,
    SYSTEM_SENSORS,
    WIFI_CLIENT_SENSOR,
    RouterOSInterfaceSensor,
    RouterOSSensor,
    RouterOSSensorDescription,
)


def _make_coordinator(data: RouterOSData) -> MagicMock:
    """Create a coordinator stub for entity tests."""
    coordinator = MagicMock()
    coordinator.data = data
    coordinator.entry.entry_id = "test_entry"
    coordinator._host = "192.168.88.1"
    return coordinator


def _get_description(
    descriptions: tuple[RouterOSSensorDescription, ...],
    key: str,
) -> RouterOSSensorDescription:
    """Return a sensor description by key."""
    return next(description for description in descriptions if description.key == key)


def test_lte_sensor_native_value():
    """Test LTE sensor values are read from the entity."""
    sensor = RouterOSSensor(
        _make_coordinator(
            RouterOSData(
                lte={"rssi": -65},
                system={},
                interfaces=[],
            )
        ),
        _get_description(LTE_SENSORS, "lte_rssi"),
    )

    assert sensor.native_value == -65


def test_memory_usage_sensor_native_value():
    """Test memory usage is calculated by the entity."""
    sensor = RouterOSSensor(
        _make_coordinator(
            RouterOSData(
                lte={},
                system={
                    "total-memory": 256_000_000,
                    "free-memory": 128_000_000,
                },
                interfaces=[],
            )
        ),
        _get_description(SYSTEM_SENSORS, "memory_usage"),
    )

    assert sensor.native_value == 50.0


def test_disk_usage_sensor_native_value():
    """Test disk usage is calculated by the entity."""
    sensor = RouterOSSensor(
        _make_coordinator(
            RouterOSData(
                lte={},
                system={
                    "total-hdd-space": 100_000_000,
                    "free-hdd-space": 40_000_000,
                },
                interfaces=[],
            )
        ),
        _get_description(SYSTEM_SENSORS, "disk_usage"),
    )

    assert sensor.native_value == 60.0


def test_system_uptime_sensor_native_value_from_string():
    """Test system uptime is converted to a timestamp from a RouterOS string."""
    sensor = RouterOSSensor(
        _make_coordinator(
            RouterOSData(
                lte={},
                system={"uptime": "1d2h"},
                interfaces=[],
            )
        ),
        _get_description(SYSTEM_SENSORS, "uptime"),
    )
    frozen_now = datetime(2026, 5, 10, 12, 0, tzinfo=UTC)

    with patch(
        "custom_components.routeros_lte.sensor.dt_util.utcnow",
        return_value=frozen_now,
    ):
        assert sensor.native_value == frozen_now - timedelta(days=1, hours=2)


def test_wifi_client_sensor_native_value():
    """Test WiFi client count comes from coordinator data."""
    sensor = RouterOSSensor(
        _make_coordinator(
            RouterOSData(
                lte={},
                system={},
                interfaces=[],
                wifi_client_count=5,
            )
        ),
        WIFI_CLIENT_SENSOR,
    )

    assert sensor.native_value == 5


def test_interface_sensor_native_value():
    """Test interface sensor values are read from the matching interface."""
    description = RouterOSSensorDescription(
        key="iface_ether1_tx-byte",
        name="ether1 TX Bytes",
        data_path="interface",
        data_key="tx-byte",
    )
    sensor = RouterOSInterfaceSensor(
        _make_coordinator(
            RouterOSData(
                lte={},
                system={},
                interfaces=[
                    {
                        "name": "ether1",
                        "tx-byte": 1_000_000,
                    }
                ],
            )
        ),
        description,
        "ether1",
    )

    assert sensor.native_value == 1_000_000


def test_lte_session_uptime_sensor_native_value():
    """Test LTE session uptime is parsed by the entity."""
    sensor = RouterOSSensor(
        _make_coordinator(
            RouterOSData(
                lte={"session-uptime": "1h30m"},
                system={},
                interfaces=[],
            )
        ),
        _get_description(LTE_SENSORS, "lte_session_uptime"),
    )

    assert sensor.native_value == 5400


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


def test_normalize_lte_data_current_cellid():
    """Test that current-cellid is mapped to cell-id."""
    lte = {"current-cellid": 2514442, "rssi": -65}
    RouterOSCoordinator._normalize_lte_data(lte)
    assert lte["cell-id"] == 2514442


def test_normalize_lte_data_cell_id_not_overwritten():
    """Test that existing cell-id is not overwritten by current-cellid."""
    lte = {"cell-id": "12345", "current-cellid": 9999}
    RouterOSCoordinator._normalize_lte_data(lte)
    assert lte["cell-id"] == "12345"


def test_normalize_lte_data_mcc_mnc_from_operator_5digit():
    """Test MCC/MNC parsing from 5-digit current-operator."""
    lte = {"current-operator": 24701}
    RouterOSCoordinator._normalize_lte_data(lte)
    assert lte["mcc"] == "247"
    assert lte["mnc"] == "01"


def test_normalize_lte_data_mcc_mnc_from_operator_6digit():
    """Test MCC/MNC parsing from 6-digit current-operator."""
    lte = {"current-operator": 310260}
    RouterOSCoordinator._normalize_lte_data(lte)
    assert lte["mcc"] == "310"
    assert lte["mnc"] == "260"


def test_normalize_lte_data_mcc_mnc_not_overwritten():
    """Test that existing mcc/mnc are not overwritten."""
    lte = {"current-operator": 24701, "mcc": "244", "mnc": "05"}
    RouterOSCoordinator._normalize_lte_data(lte)
    assert lte["mcc"] == "244"
    assert lte["mnc"] == "05"


def test_normalize_lte_data_text_operator_ignored():
    """Test that non-numeric current-operator is ignored for MCC/MNC."""
    lte = {"current-operator": "LMT"}
    RouterOSCoordinator._normalize_lte_data(lte)
    assert "mcc" not in lte
    assert "mnc" not in lte


def test_normalize_lte_data_band_from_primary_band():
    """Test band extraction from primary-band field."""
    lte = {"primary-band": "B3@10Mhz earfcn: 1606 phy-cellid: 0"}
    RouterOSCoordinator._normalize_lte_data(lte)
    assert lte["band"] == "B3"


def test_normalize_lte_data_band_not_overwritten():
    """Test that existing band is not overwritten by primary-band."""
    lte = {"band": "B7", "primary-band": "B3@10Mhz earfcn: 1606 phy-cellid: 0"}
    RouterOSCoordinator._normalize_lte_data(lte)
    assert lte["band"] == "B7"


def test_normalize_lte_data_mcc_mnc_from_imsi():
    """Test MCC/MNC parsed from IMSI when operator is text."""
    lte = {"current-operator": "Telenor SE", "imsi": 240084720207125}
    RouterOSCoordinator._normalize_lte_data(lte)
    assert lte["mcc"] == "240"
    assert lte["mnc"] == "08"


def test_normalize_lte_data_mcc_mnc_from_imsi_3digit_mnc():
    """Test 3-digit MNC parsed from IMSI for North American operators."""
    lte = {"current-operator": "T-Mobile", "imsi": 310260123456789}
    RouterOSCoordinator._normalize_lte_data(lte)
    assert lte["mcc"] == "310"
    assert lte["mnc"] == "260"


def test_normalize_lte_data_mcc_mnc_not_from_imsi_when_operator_numeric():
    """Test IMSI fallback is not used when numeric operator provides MCC/MNC."""
    lte = {"current-operator": 24008, "imsi": 240084720207125}
    RouterOSCoordinator._normalize_lte_data(lte)
    assert lte["mcc"] == "240"
    assert lte["mnc"] == "08"


def test_parse_uptime_days():
    """Test parsing uptime string with days."""
    assert RouterOSSensor._parse_uptime("1d") == 86400


def test_parse_uptime_complex():
    """Test parsing uptime string with weeks, days, hours, minutes, seconds."""
    assert RouterOSSensor._parse_uptime("3d12h05m") == 3 * 86400 + 12 * 3600 + 5 * 60


def test_parse_uptime_full():
    """Test parsing uptime string with all components."""
    assert RouterOSSensor._parse_uptime("1w2d3h4m5s") == (
        604800 + 2 * 86400 + 3 * 3600 + 4 * 60 + 5
    )


def test_lte_imei_extraction():
    """Test LTE IMEI is properly extracted."""
    data = RouterOSData(
        lte={"imei": "860561044494441"},
        system={},
        interfaces=[],
    )
    assert data.lte["imei"] == "860561044494441"


def test_lte_iccid_extraction():
    """Test LTE ICCID is properly extracted."""
    data = RouterOSData(
        lte={"iccid": "89460851027003480376"},
        system={},
        interfaces=[],
    )
    assert data.lte["iccid"] == "89460851027003480376"


def test_lte_operator_extraction():
    """Test LTE operator name is properly extracted."""
    data = RouterOSData(
        lte={"current-operator": "Telenor SE"},
        system={},
        interfaces=[],
    )
    assert data.lte["current-operator"] == "Telenor SE"


def test_lte_session_uptime_parsing():
    """Test session uptime is parsed to seconds."""
    assert RouterOSSensor._parse_uptime("1h30m") == 3600 + 30 * 60
    assert RouterOSSensor._parse_uptime("28m4s") == 28 * 60 + 4


def test_wifi_client_count():
    """Test WiFi client count data."""
    data = RouterOSData(
        lte={},
        system={},
        interfaces=[],
        wifi_client_count=5,
    )
    assert data.wifi_client_count == 5


def test_routerboard_data():
    """Test routerboard data structure."""
    data = RouterOSData(
        lte={},
        system={},
        interfaces=[],
        routerboard={
            "serial-number": "TESTSERIAL123",
            "model": "D53G-5HacD2HnD",
            "current-firmware": "7.18.2",
            "upgrade-firmware": "7.22.2",
        },
    )
    assert data.routerboard["serial-number"] == "TESTSERIAL123"
    assert data.routerboard["current-firmware"] == "7.18.2"
    assert data.routerboard["upgrade-firmware"] == "7.22.2"
