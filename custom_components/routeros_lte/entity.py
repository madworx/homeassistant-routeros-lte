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
        identity = coordinator.data.identity
        host = coordinator._host
        device_name = f"RouterOS ({identity})" if identity else f"RouterOS ({host})"
        serial = coordinator.data.routerboard.get("serial-number")
        identifiers: set[tuple[str, str]] = {(DOMAIN, coordinator.entry.entry_id)}
        if serial:
            identifiers.add((DOMAIN, serial))
        self._attr_device_info = DeviceInfo(
            identifiers=identifiers,
            name=device_name,
            manufacturer="MikroTik",
            model=coordinator.data.routerboard.get(
                "model", coordinator.data.system.get("board-name", "RouterOS")
            ),
            sw_version=coordinator.data.system.get("version"),
            serial_number=serial,
            hw_version=coordinator.data.routerboard.get("current-firmware"),
        )
