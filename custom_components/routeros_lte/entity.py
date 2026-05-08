"""Base entity for RouterOS LTE integration."""

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import RouterOSCoordinator


class RouterOSEntity(CoordinatorEntity[RouterOSCoordinator]):
    """Base class for RouterOS entities."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: RouterOSCoordinator) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.entry.entry_id)},
            name=f"RouterOS ({coordinator._host})",
            manufacturer="MikroTik",
            model=coordinator.data.system.get("board-name", "RouterOS"),
            sw_version=coordinator.data.system.get("version"),
        )
