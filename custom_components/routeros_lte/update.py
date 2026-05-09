"""Update platform for MikroTik RouterOS LTE."""

from __future__ import annotations

from homeassistant.components.update import UpdateEntity
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
    """Set up RouterOS firmware update entity."""
    coordinator: RouterOSCoordinator = hass.data[DOMAIN][entry.entry_id]

    if coordinator.data.routerboard:
        async_add_entities([RouterOSFirmwareUpdate(coordinator)])


class RouterOSFirmwareUpdate(RouterOSEntity, UpdateEntity):
    """Firmware update entity for RouterOS."""

    _attr_name = "Firmware Update"

    def __init__(self, coordinator: RouterOSCoordinator) -> None:
        """Initialize the update entity."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.entry.entry_id}_firmware_update"

    @property
    def installed_version(self) -> str | None:
        """Return the current firmware version."""
        return self.coordinator.data.routerboard.get("current-firmware")

    @property
    def latest_version(self) -> str | None:
        """Return the latest available firmware version."""
        return self.coordinator.data.routerboard.get(
            "upgrade-firmware",
            self.coordinator.data.routerboard.get("current-firmware"),
        )
