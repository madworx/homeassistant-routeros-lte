"""DataUpdateCoordinator for MikroTik RouterOS LTE."""

import logging
from dataclasses import dataclass, field
from typing import Any

import librouteros

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    CONF_HOST,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_USERNAME,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    LTE_KEYS,
    SYSTEM_KEYS,
)

_LOGGER = logging.getLogger(__name__)


@dataclass
class RouterOSData:
    """Data class holding all fetched RouterOS data."""

    lte: dict[str, Any] = field(default_factory=dict)
    system: dict[str, Any] = field(default_factory=dict)
    interfaces: list[dict[str, Any]] = field(default_factory=list)


class RouterOSCoordinator(DataUpdateCoordinator[RouterOSData]):
    """Coordinator to manage fetching RouterOS data."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=DEFAULT_SCAN_INTERVAL,
        )
        self.entry = entry
        self._api: librouteros.api.Api | None = None
        self._host: str = entry.data[CONF_HOST]
        self._port: int = entry.data[CONF_PORT]
        self._username: str = entry.data[CONF_USERNAME]
        self._password: str = entry.data[CONF_PASSWORD]

    def _connect(self) -> librouteros.api.Api:
        """Establish connection to RouterOS."""
        return librouteros.connect(
            host=self._host,
            username=self._username,
            password=self._password,
            port=self._port,
        )

    def disconnect(self) -> None:
        """Disconnect from RouterOS."""
        if self._api:
            try:
                self._api.close()
            except Exception:  # noqa: BLE001
                pass
            self._api = None

    def _ensure_connected(self) -> librouteros.api.Api:
        """Ensure we have a valid connection."""
        if self._api is None:
            self._api = self._connect()
        return self._api

    def _fetch_data(self) -> RouterOSData:
        """Fetch data from the RouterOS device (runs in executor)."""
        try:
            api = self._ensure_connected()
        except (ConnectionRefusedError, OSError, TimeoutError) as err:
            self._api = None
            raise UpdateFailed(f"Cannot connect to {self._host}:{self._port}") from err
        except librouteros.exceptions.TrapError as err:
            self._api = None
            raise UpdateFailed(f"Authentication failed: {err}") from err

        data = RouterOSData()

        try:
            # Fetch LTE monitor data
            lte_interfaces = list(api("/interface/lte/print"))
            if lte_interfaces:
                lte_name = lte_interfaces[0].get("name", "lte1")
                lte_monitor = list(
                    api("/interface/lte/monitor", **{"=once": "", "=numbers": lte_name})
                )
                if lte_monitor:
                    data.lte = {
                        k: lte_monitor[0].get(k)
                        for k in LTE_KEYS
                        if k in lte_monitor[0]
                    }
        except librouteros.exceptions.TrapError as err:
            _LOGGER.debug("LTE data not available: %s", err)

        try:
            # Fetch system resources
            resources = list(api("/system/resource/print"))
            if resources:
                data.system = {
                    k: resources[0].get(k) for k in SYSTEM_KEYS if k in resources[0]
                }
        except librouteros.exceptions.TrapError as err:
            _LOGGER.warning("Failed to fetch system resources: %s", err)

        try:
            # Fetch interface statistics
            interfaces = list(api("/interface/print"))
            data.interfaces = [
                {
                    "name": iface.get("name", ""),
                    "type": iface.get("type", ""),
                    "running": iface.get("running", False),
                    "tx-byte": iface.get("tx-byte", 0),
                    "rx-byte": iface.get("rx-byte", 0),
                    "tx-packet": iface.get("tx-packet", 0),
                    "rx-packet": iface.get("rx-packet", 0),
                }
                for iface in interfaces
            ]
        except librouteros.exceptions.TrapError as err:
            _LOGGER.warning("Failed to fetch interface stats: %s", err)

        return data

    async def _async_update_data(self) -> RouterOSData:
        """Fetch data from the router."""
        try:
            return await self.hass.async_add_executor_job(self._fetch_data)
        except UpdateFailed:
            raise
        except Exception as err:
            self.disconnect()
            raise UpdateFailed(f"Error communicating with RouterOS: {err}") from err
