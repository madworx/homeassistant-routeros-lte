"""Tests for RouterOS LTE sensors."""

from custom_components.routeros_lte.coordinator import RouterOSCoordinator, RouterOSData


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
