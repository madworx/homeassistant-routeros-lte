"""Tests for integration and platform setup behavior."""

from copy import deepcopy
from unittest.mock import AsyncMock, MagicMock, patch

from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.routeros_lte import (
    _async_update_listener,
    async_unload_entry,
)
from custom_components.routeros_lte import (
    async_setup_entry as integration_async_setup_entry,
)
from custom_components.routeros_lte.binary_sensor import (
    RouterOSInterfaceRunningSensor,
    RouterOSLTEConnectionSensor,
)
from custom_components.routeros_lte.binary_sensor import (
    async_setup_entry as binary_sensor_async_setup_entry,
)
from custom_components.routeros_lte.const import (
    CONF_HOST,
    CONF_MONITORED_INTERFACES,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_USERNAME,
    DOMAIN,
    PLATFORMS,
)
from custom_components.routeros_lte.coordinator import RouterOSData
from custom_components.routeros_lte.entity import RouterOSEntity
from custom_components.routeros_lte.sensor import (
    LTE_SENSORS,
    SYSTEM_SENSORS,
    WIFI_CLIENT_SENSOR,
    RouterOSInterfaceSensor,
    RouterOSSensor,
)
from custom_components.routeros_lte.sensor import (
    async_setup_entry as sensor_async_setup_entry,
)
from custom_components.routeros_lte.update import (
    RouterOSFirmwareUpdate,
)
from custom_components.routeros_lte.update import (
    async_setup_entry as update_async_setup_entry,
)


def _create_entry(
    *,
    options: dict | None = None,
) -> MockConfigEntry:
    """Create a config entry for RouterOS tests."""
    return MockConfigEntry(
        domain=DOMAIN,
        title="RouterOS",
        data={
            CONF_HOST: "192.168.88.1",
            CONF_PORT: 8728,
            CONF_USERNAME: "admin",
            CONF_PASSWORD: "secret",
        },
        options=options or {},
    )


def _create_coordinator(entry: MockConfigEntry, data: RouterOSData) -> MagicMock:
    """Create a coordinator stub for setup tests."""
    coordinator = MagicMock()
    coordinator.data = data
    coordinator.entry = entry
    coordinator._host = entry.data[CONF_HOST]
    coordinator.disconnect = MagicMock()
    coordinator.async_config_entry_first_refresh = AsyncMock()
    return coordinator


async def test_async_setup_entry_stores_coordinator_and_forwards_platforms(
    hass,
) -> None:
    """Test integration setup stores the coordinator and forwards platforms."""
    entry = _create_entry()
    entry.add_to_hass(hass)
    coordinator = _create_coordinator(entry, RouterOSData())

    with (
        patch(
            "custom_components.routeros_lte.RouterOSCoordinator",
            return_value=coordinator,
        ),
        patch.object(
            hass.config_entries,
            "async_forward_entry_setups",
            AsyncMock(return_value=None),
        ) as mock_forward,
    ):
        assert await integration_async_setup_entry(hass, entry) is True

    coordinator.async_config_entry_first_refresh.assert_awaited_once()
    mock_forward.assert_awaited_once_with(entry, PLATFORMS)
    assert hass.data[DOMAIN][entry.entry_id] is coordinator


async def test_async_update_listener_reloads_entry(hass) -> None:
    """Test options updates reload the integration."""
    entry = _create_entry()

    with patch.object(
        hass.config_entries,
        "async_reload",
        AsyncMock(return_value=True),
    ) as mock_reload:
        await _async_update_listener(hass, entry)

    mock_reload.assert_awaited_once_with(entry.entry_id)


async def test_async_unload_entry_disconnects_on_success(hass) -> None:
    """Test integration unload disconnects the coordinator on success."""
    entry = _create_entry()
    coordinator = _create_coordinator(entry, RouterOSData())
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    with patch.object(
        hass.config_entries,
        "async_unload_platforms",
        AsyncMock(return_value=True),
    ) as mock_unload:
        assert await async_unload_entry(hass, entry) is True

    mock_unload.assert_awaited_once_with(entry, PLATFORMS)
    coordinator.disconnect.assert_called_once()
    assert entry.entry_id not in hass.data[DOMAIN]


async def test_async_unload_entry_keeps_coordinator_on_failure(hass) -> None:
    """Test failed unload leaves the coordinator intact."""
    entry = _create_entry()
    coordinator = _create_coordinator(entry, RouterOSData())
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    with patch.object(
        hass.config_entries,
        "async_unload_platforms",
        AsyncMock(return_value=False),
    ) as mock_unload:
        assert await async_unload_entry(hass, entry) is False

    mock_unload.assert_awaited_once_with(entry, PLATFORMS)
    coordinator.disconnect.assert_not_called()
    assert hass.data[DOMAIN][entry.entry_id] is coordinator


async def test_sensor_async_setup_entry_respects_interface_filter(
    hass,
    mock_routeros_data,
) -> None:
    """Test sensor setup only adds interface sensors for monitored interfaces."""
    entry = _create_entry(options={CONF_MONITORED_INTERFACES: ["ether1"]})
    coordinator = _create_coordinator(entry, mock_routeros_data)
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    entities = []

    await sensor_async_setup_entry(hass, entry, entities.extend)

    assert len(
        [entity for entity in entities if isinstance(entity, RouterOSSensor)]
    ) == (len(LTE_SENSORS) + len(SYSTEM_SENSORS) + 1)
    interface_sensors = [
        entity for entity in entities if isinstance(entity, RouterOSInterfaceSensor)
    ]
    assert len(interface_sensors) == 4
    assert {entity._interface_name for entity in interface_sensors} == {"ether1"}


async def test_sensor_async_setup_entry_skips_wifi_sensor_when_unavailable(
    hass,
    mock_routeros_data,
) -> None:
    """Test sensor setup skips WiFi client count when no data is available."""
    entry = _create_entry()
    data = deepcopy(mock_routeros_data)
    data.wifi_client_count = None
    coordinator = _create_coordinator(entry, data)
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    entities = []

    await sensor_async_setup_entry(hass, entry, entities.extend)

    assert WIFI_CLIENT_SENSOR.key not in {
        entity.entity_description.key
        for entity in entities
        if isinstance(entity, RouterOSSensor)
    }


async def test_binary_sensor_async_setup_entry_respects_interface_filter(
    hass,
    mock_routeros_data,
) -> None:
    """Test binary sensor setup only adds monitored interface sensors."""
    entry = _create_entry(options={CONF_MONITORED_INTERFACES: ["ether1"]})
    coordinator = _create_coordinator(entry, mock_routeros_data)
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    entities = []

    await binary_sensor_async_setup_entry(hass, entry, entities.extend)

    assert (
        len(
            [
                entity
                for entity in entities
                if isinstance(entity, RouterOSLTEConnectionSensor)
            ]
        )
        == 1
    )
    interface_sensors = [
        entity
        for entity in entities
        if isinstance(entity, RouterOSInterfaceRunningSensor)
    ]
    assert len(interface_sensors) == 1
    assert interface_sensors[0]._interface_name == "ether1"


def test_interface_running_sensor_state_comes_from_matching_interface(
    mock_routeros_data,
) -> None:
    """Test interface running sensors read the matching interface state."""
    entry = _create_entry()
    coordinator = _create_coordinator(entry, mock_routeros_data)
    sensor = RouterOSInterfaceRunningSensor(coordinator, "ether1")

    assert sensor.is_on is True


async def test_update_async_setup_entry_adds_firmware_entity(
    hass,
    mock_routeros_data,
) -> None:
    """Test update setup adds a firmware entity when routerboard data exists."""
    entry = _create_entry()
    coordinator = _create_coordinator(entry, mock_routeros_data)
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    entities = []

    await update_async_setup_entry(hass, entry, entities.extend)

    assert len(entities) == 1
    assert isinstance(entities[0], RouterOSFirmwareUpdate)
    assert entities[0].installed_version == "7.18.2"
    assert entities[0].latest_version == "7.22.2"


async def test_update_async_setup_entry_skips_missing_routerboard_data(
    hass,
    mock_routeros_data,
) -> None:
    """Test update setup does not add entities without routerboard data."""
    entry = _create_entry()
    data = deepcopy(mock_routeros_data)
    data.routerboard = {}
    coordinator = _create_coordinator(entry, data)
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    entities = []

    await update_async_setup_entry(hass, entry, entities.extend)

    assert entities == []


def test_routeros_entity_device_info_uses_identity_and_serial(
    mock_routeros_data,
) -> None:
    """Test base entity device metadata uses identity and serial number."""
    entry = _create_entry()
    entity = RouterOSEntity(_create_coordinator(entry, mock_routeros_data))

    assert entity.device_info["name"] == "RouterOS (MikroTik)"
    assert entity.device_info["manufacturer"] == "MikroTik"
    assert entity.device_info["model"] == "D53G-5HacD2HnD"
    assert entity.device_info["sw_version"] == "7.14"
    assert entity.device_info["serial_number"] == "TESTSERIAL123"
    assert entity.device_info["hw_version"] == "7.18.2"
    assert entity.device_info["identifiers"] == {
        (DOMAIN, entry.entry_id),
        (DOMAIN, "TESTSERIAL123"),
    }
