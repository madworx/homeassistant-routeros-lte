"""Binary sensor platform for MikroTik RouterOS LTE."""

from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import RouterOSCoordinator
from .entity import RouterOSEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up RouterOS LTE binary sensors from a config entry."""
    coordinator: RouterOSCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[BinarySensorEntity] = []

    # LTE connection status
    if coordinator.data.lte:
        entities.append(RouterOSLTEConnectionSensor(coordinator))

    # Interface running state
    for iface in coordinator.data.interfaces:
        entities.append(
            RouterOSInterfaceRunningSensor(coordinator, iface["name"])
        )

    async_add_entities(entities)


class RouterOSLTEConnectionSensor(RouterOSEntity, BinarySensorEntity):
    """Binary sensor for LTE connection status."""

    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_name = "LTE Connected"

    def __init__(self, coordinator: RouterOSCoordinator) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.entry.entry_id}_lte_connected"

    @property
    def is_on(self) -> bool | None:
        """Return true if LTE is connected."""
        status = self.coordinator.data.lte.get("connection-status", "")
        return status.lower() == "connected" if status else None


class RouterOSInterfaceRunningSensor(RouterOSEntity, BinarySensorEntity):
    """Binary sensor for interface running state."""

    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY

    def __init__(
        self, coordinator: RouterOSCoordinator, interface_name: str
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self._interface_name = interface_name
        self._attr_unique_id = (
            f"{coordinator.entry.entry_id}_iface_{interface_name}_running"
        )
        self._attr_name = f"{interface_name} Running"

    @property
    def is_on(self) -> bool | None:
        """Return true if interface is running."""
        for iface in self.coordinator.data.interfaces:
            if iface["name"] == self._interface_name:
                return iface.get("running", False)
        return None
