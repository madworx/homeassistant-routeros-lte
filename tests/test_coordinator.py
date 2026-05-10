"""Tests for RouterOS LTE coordinator."""

from unittest.mock import MagicMock, patch

import librouteros.exceptions
import pytest
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.routeros_lte.const import (
    CONF_HOST,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_USERNAME,
)
from custom_components.routeros_lte.coordinator import RouterOSCoordinator, RouterOSData


@pytest.fixture
def mock_entry():
    """Return a mock config entry."""
    entry = MagicMock()
    entry.data = {
        CONF_HOST: "192.168.1.1",
        CONF_PORT: 8728,
        CONF_USERNAME: "admin",
        CONF_PASSWORD: "password",
    }
    return entry


@pytest.fixture
def coordinator(hass, mock_entry):
    """Return a RouterOSCoordinator instance."""
    return RouterOSCoordinator(hass, mock_entry)


@pytest.fixture
def mock_api():
    """Return a mock API with default responses."""
    api = MagicMock()
    api.close = MagicMock()

    def api_call(path, **kwargs):
        responses = {
            "/interface/lte/print": [{"name": "lte1", ".id": "*1"}],
            "/interface/lte/monitor": [
                {"rssi": -65, "rsrp": -95, "rsrq": -10, "sinr": 12}
            ],
            "/system/resource/print": [
                {
                    "cpu-load": 15,
                    "free-memory": 128_000_000,
                    "total-memory": 256_000_000,
                }
            ],
            "/interface/print": [
                {
                    "name": "ether1",
                    "type": "ether",
                    "running": True,
                    "tx-byte": 1000,
                    "rx-byte": 2000,
                    "tx-packet": 10,
                    "rx-packet": 20,
                }
            ],
            "/interface/lte/at-chat": [],
            "/system/routerboard/print": [
                {
                    "serial-number": "TESTSERIAL123",
                    "model": "D53G-5HacD2HnD",
                    "current-firmware": "7.18.2",
                    "upgrade-firmware": "7.22.2",
                }
            ],
            "/system/identity/print": [{"name": "MikroTik"}],
            "/interface/wireless/registration-table/print": [
                {"mac-address": "AA:BB:CC:DD:EE:FF"},
                {"mac-address": "11:22:33:44:55:66"},
            ],
        }
        return responses.get(path, [])

    api.side_effect = api_call
    return api


# --- _connect / disconnect / _ensure_connected ---


def test_connect(coordinator):
    """Test _connect calls librouteros.connect with correct params."""
    with patch(
        "custom_components.routeros_lte.coordinator.librouteros.connect"
    ) as mock_connect:
        mock_connect.return_value = MagicMock()
        api = coordinator._connect()
        mock_connect.assert_called_once_with(
            host="192.168.1.1",
            username="admin",
            password="password",
            port=8728,
            timeout=10.0,
        )
        assert api is mock_connect.return_value


def test_disconnect_with_api(coordinator):
    """Test disconnect closes the API connection."""
    mock_api = MagicMock()
    coordinator._api = mock_api
    coordinator.disconnect()
    mock_api.close.assert_called_once()
    assert coordinator._api is None


def test_disconnect_without_api(coordinator):
    """Test disconnect is safe when no API is connected."""
    coordinator._api = None
    coordinator.disconnect()
    assert coordinator._api is None


def test_disconnect_close_exception(coordinator):
    """Test disconnect handles exceptions from close()."""
    mock_api = MagicMock()
    mock_api.close.side_effect = OSError("connection reset")
    coordinator._api = mock_api
    coordinator.disconnect()
    assert coordinator._api is None


def test_ensure_connected_creates_connection(coordinator):
    """Test _ensure_connected creates a new connection when none exists."""
    with patch.object(coordinator, "_connect") as mock_connect:
        mock_connect.return_value = MagicMock()
        api = coordinator._ensure_connected()
        mock_connect.assert_called_once()
        assert api is mock_connect.return_value


def test_ensure_connected_reuses_connection(coordinator):
    """Test _ensure_connected reuses existing connection."""
    existing = MagicMock()
    coordinator._api = existing
    with patch.object(coordinator, "_connect") as mock_connect:
        api = coordinator._ensure_connected()
        mock_connect.assert_not_called()
        assert api is existing


# --- _fetch_data ---


def test_fetch_data_success(coordinator, mock_api):
    """Test successful data fetch."""
    with patch.object(coordinator, "_ensure_connected", return_value=mock_api):
        data = coordinator._fetch_data()

    assert isinstance(data, RouterOSData)
    assert data.lte["rssi"] == -65
    assert data.system["cpu-load"] == 15
    assert len(data.interfaces) == 1
    assert data.interfaces[0]["name"] == "ether1"
    assert data.routerboard["serial-number"] == "TESTSERIAL123"
    assert data.routerboard["current-firmware"] == "7.18.2"
    assert data.routerboard["upgrade-firmware"] == "7.22.2"
    assert data.identity == "MikroTik"
    assert data.wifi_client_count == 2


def test_fetch_data_connection_refused(coordinator):
    """Test _fetch_data raises UpdateFailed on connection error."""
    with (
        patch.object(
            coordinator, "_ensure_connected", side_effect=ConnectionRefusedError
        ),
        pytest.raises(UpdateFailed, match="Cannot connect"),
    ):
        coordinator._fetch_data()
    assert coordinator._api is None


def test_fetch_data_timeout(coordinator):
    """Test _fetch_data raises UpdateFailed on timeout."""
    with (
        patch.object(coordinator, "_ensure_connected", side_effect=TimeoutError),
        pytest.raises(UpdateFailed, match="Cannot connect"),
    ):
        coordinator._fetch_data()


def test_fetch_data_os_error(coordinator):
    """Test _fetch_data raises UpdateFailed on OS error."""
    with (
        patch.object(
            coordinator, "_ensure_connected", side_effect=OSError("network unreachable")
        ),
        pytest.raises(UpdateFailed, match="Cannot connect"),
    ):
        coordinator._fetch_data()


def test_fetch_data_auth_failed(coordinator):
    """Test _fetch_data raises UpdateFailed on auth failure."""
    with (
        patch.object(
            coordinator,
            "_ensure_connected",
            side_effect=librouteros.exceptions.TrapError("invalid user"),
        ),
        pytest.raises(UpdateFailed, match="Authentication failed"),
    ):
        coordinator._fetch_data()


def test_fetch_data_no_lte_interfaces(coordinator, mock_api):
    """Test fetch when no LTE interfaces exist."""

    def api_call(path, **kwargs):
        if path == "/interface/lte/print":
            return []
        if path == "/system/resource/print":
            return [{"cpu-load": 5}]
        if path == "/interface/print":
            return []
        return []

    mock_api.side_effect = api_call
    with patch.object(coordinator, "_ensure_connected", return_value=mock_api):
        data = coordinator._fetch_data()
    assert data.lte == {}


def test_fetch_data_lte_trap_error(coordinator, mock_api):
    """Test fetch continues when LTE data raises TrapError."""

    def api_call(path, **kwargs):
        if path == "/interface/lte/print":
            raise librouteros.exceptions.TrapError("no such command")
        if path == "/system/resource/print":
            return [{"cpu-load": 10}]
        if path == "/interface/print":
            return []
        return []

    mock_api.side_effect = api_call
    with patch.object(coordinator, "_ensure_connected", return_value=mock_api):
        data = coordinator._fetch_data()
    assert data.lte == {}
    assert data.system["cpu-load"] == 10


def test_fetch_data_system_trap_error(coordinator, mock_api):
    """Test fetch continues when system resources raises TrapError."""

    def api_call(path, **kwargs):
        if path == "/interface/lte/print":
            return []
        if path == "/system/resource/print":
            raise librouteros.exceptions.TrapError("access denied")
        if path == "/interface/print":
            return []
        return []

    mock_api.side_effect = api_call
    with patch.object(coordinator, "_ensure_connected", return_value=mock_api):
        data = coordinator._fetch_data()
    assert data.system == {}


def test_fetch_data_interface_trap_error(coordinator, mock_api):
    """Test fetch continues when interface stats raises TrapError."""

    def api_call(path, **kwargs):
        if path == "/interface/lte/print":
            return []
        if path == "/system/resource/print":
            return []
        if path == "/interface/print":
            raise librouteros.exceptions.TrapError("access denied")
        return []

    mock_api.side_effect = api_call
    with patch.object(coordinator, "_ensure_connected", return_value=mock_api):
        data = coordinator._fetch_data()
    assert data.interfaces == []


def test_fetch_data_lte_monitor_empty(coordinator, mock_api):
    """Test fetch when LTE monitor returns empty."""

    def api_call(path, **kwargs):
        if path == "/interface/lte/print":
            return [{"name": "lte1", ".id": "*1"}]
        if path == "/interface/lte/monitor":
            return []
        if path == "/interface/lte/at-chat":
            return []
        if path == "/system/resource/print":
            return []
        if path == "/interface/print":
            return []
        return []

    mock_api.side_effect = api_call
    with patch.object(coordinator, "_ensure_connected", return_value=mock_api):
        data = coordinator._fetch_data()
    assert data.lte == {}


# --- _fetch_tac_via_at ---


def test_fetch_tac_via_at_success():
    """Test TAC parsing from AT command output."""
    api = MagicMock()
    api.side_effect = lambda *args, **kwargs: [
        {
            "output": '+QENG: "servingcell","NOCONN","LTE","FDD",'
            "244,05,1A2B3C4,123,1606,3,5,5,1A2B,"
        }
    ]
    result = RouterOSCoordinator._fetch_tac_via_at(api, "*1")
    assert result == str(int("1A2B", 16))


def test_fetch_tac_via_at_no_result():
    """Test TAC returns None when AT command returns no data."""
    api = MagicMock()
    api.side_effect = lambda *args, **kwargs: []
    result = RouterOSCoordinator._fetch_tac_via_at(api, "*1")
    assert result is None


def test_fetch_tac_via_at_no_match():
    """Test TAC returns None when output doesn't match pattern."""
    api = MagicMock()
    api.side_effect = lambda *args, **kwargs: [{"output": "ERROR"}]
    result = RouterOSCoordinator._fetch_tac_via_at(api, "*1")
    assert result is None


def test_fetch_tac_via_at_exception():
    """Test TAC returns None when AT command raises exception."""
    api = MagicMock()
    api.side_effect = OSError("not supported")
    result = RouterOSCoordinator._fetch_tac_via_at(api, "*1")
    assert result is None


def test_fetch_data_tac_fallback(coordinator, mock_api):
    """Test TAC is fetched via AT command when lac is not in LTE data."""

    def api_call(path, **kwargs):
        if path == "/interface/lte/print":
            return [{"name": "lte1", ".id": "*1"}]
        if path == "/interface/lte/monitor":
            return [{"rssi": -65}]
        if path == "/interface/lte/at-chat":
            return [
                {
                    "output": '+QENG: "servingcell","NOCONN","LTE","FDD",'
                    "244,05,1A2B3C4,123,1606,3,5,5,00FF,"
                }
            ]
        if path == "/system/resource/print":
            return []
        if path == "/interface/print":
            return []
        return []

    mock_api.side_effect = api_call
    with patch.object(coordinator, "_ensure_connected", return_value=mock_api):
        data = coordinator._fetch_data()
    assert data.lte["lac"] == str(int("00FF", 16))


def test_fetch_data_no_tac_when_lac_present(coordinator, mock_api):
    """Test TAC is not fetched when lac is already in LTE data."""

    def api_call(path, **kwargs):
        if path == "/interface/lte/print":
            return [{"name": "lte1", ".id": "*1"}]
        if path == "/interface/lte/monitor":
            return [{"rssi": -65, "lac": "999"}]
        if path == "/interface/lte/at-chat":
            raise AssertionError("Should not be called")
        if path == "/system/resource/print":
            return []
        if path == "/interface/print":
            return []
        return []

    mock_api.side_effect = api_call
    with patch.object(coordinator, "_ensure_connected", return_value=mock_api):
        data = coordinator._fetch_data()
    assert data.lte["lac"] == "999"


def test_fetch_data_no_tac_when_no_lte_id(coordinator, mock_api):
    """Test TAC is not fetched when LTE interface has no .id."""

    def api_call(path, **kwargs):
        if path == "/interface/lte/print":
            return [{"name": "lte1"}]  # No .id
        if path == "/interface/lte/monitor":
            return [{"rssi": -65}]
        if path == "/system/resource/print":
            return []
        if path == "/interface/print":
            return []
        return []

    mock_api.side_effect = api_call
    with patch.object(coordinator, "_ensure_connected", return_value=mock_api):
        data = coordinator._fetch_data()
    assert "lac" not in data.lte


# --- _async_update_data ---


async def test_async_update_data_success(coordinator):
    """Test async_update_data delegates to _fetch_data."""
    expected = RouterOSData(lte={"rssi": -70}, system={}, interfaces=[])
    with patch.object(coordinator, "_fetch_data", return_value=expected):
        result = await coordinator._async_update_data()
    assert result is expected


async def test_async_update_data_update_failed(coordinator):
    """Test async_update_data re-raises UpdateFailed."""
    with (
        patch.object(
            coordinator, "_fetch_data", side_effect=UpdateFailed("conn error")
        ),
        pytest.raises(UpdateFailed, match="conn error"),
    ):
        await coordinator._async_update_data()


async def test_async_update_data_unexpected_error(coordinator):
    """Test async_update_data wraps unexpected errors and disconnects."""
    coordinator._api = MagicMock()
    with (
        patch.object(coordinator, "_fetch_data", side_effect=RuntimeError("boom")),
        patch.object(coordinator, "disconnect") as mock_disconnect,
        pytest.raises(UpdateFailed, match="Error communicating"),
    ):
        await coordinator._async_update_data()
    mock_disconnect.assert_called_once()


# --- routerboard / identity / wifi ---


def test_fetch_data_routerboard(coordinator, mock_api):
    """Test routerboard data is fetched."""
    with patch.object(coordinator, "_ensure_connected", return_value=mock_api):
        data = coordinator._fetch_data()
    assert data.routerboard["serial-number"] == "TESTSERIAL123"
    assert data.routerboard["model"] == "D53G-5HacD2HnD"
    assert data.routerboard["current-firmware"] == "7.18.2"
    assert data.routerboard["upgrade-firmware"] == "7.22.2"


def test_fetch_data_routerboard_trap_error(coordinator, mock_api):
    """Test fetch continues when routerboard raises TrapError."""
    original = mock_api.side_effect

    def api_call(path, **kwargs):
        if path == "/system/routerboard/print":
            raise librouteros.exceptions.TrapError("no such command")
        return original(path, **kwargs)

    mock_api.side_effect = api_call
    with patch.object(coordinator, "_ensure_connected", return_value=mock_api):
        data = coordinator._fetch_data()
    assert data.routerboard == {}
    assert data.system["cpu-load"] == 15


def test_fetch_data_identity(coordinator, mock_api):
    """Test identity is fetched."""
    with patch.object(coordinator, "_ensure_connected", return_value=mock_api):
        data = coordinator._fetch_data()
    assert data.identity == "MikroTik"


def test_fetch_data_identity_trap_error(coordinator, mock_api):
    """Test fetch continues when identity raises TrapError."""
    original = mock_api.side_effect

    def api_call(path, **kwargs):
        if path == "/system/identity/print":
            raise librouteros.exceptions.TrapError("access denied")
        return original(path, **kwargs)

    mock_api.side_effect = api_call
    with patch.object(coordinator, "_ensure_connected", return_value=mock_api):
        data = coordinator._fetch_data()
    assert data.identity is None


def test_fetch_data_wifi_client_count(coordinator, mock_api):
    """Test WiFi client count is fetched."""
    with patch.object(coordinator, "_ensure_connected", return_value=mock_api):
        data = coordinator._fetch_data()
    assert data.wifi_client_count == 2


def test_fetch_data_wifi_trap_error(coordinator, mock_api):
    """Test fetch continues when wireless table raises TrapError."""
    original = mock_api.side_effect

    def api_call(path, **kwargs):
        if path == "/interface/wireless/registration-table/print":
            raise librouteros.exceptions.TrapError("no such command")
        return original(path, **kwargs)

    mock_api.side_effect = api_call
    with patch.object(coordinator, "_ensure_connected", return_value=mock_api):
        data = coordinator._fetch_data()
    assert data.wifi_client_count is None
