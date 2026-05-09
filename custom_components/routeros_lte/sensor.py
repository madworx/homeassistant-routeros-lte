"""Sensor platform for MikroTik RouterOS LTE."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    SIGNAL_STRENGTH_DECIBELS,
    SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
    EntityCategory,
    UnitOfInformation,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util

from .const import CONF_MONITORED_INTERFACES, DOMAIN
from .coordinator import RouterOSCoordinator
from .entity import RouterOSEntity


@dataclass(frozen=True, kw_only=True)
class RouterOSSensorDescription(SensorEntityDescription):
    """Describe a RouterOS sensor."""

    data_path: str  # "lte", "system", or "interface"
    data_key: str


LTE_SENSORS: tuple[RouterOSSensorDescription, ...] = (
    RouterOSSensorDescription(
        key="lte_rssi",
        translation_key="lte_rssi",
        name="LTE RSSI",
        native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        state_class=SensorStateClass.MEASUREMENT,
        data_path="lte",
        data_key="rssi",
    ),
    RouterOSSensorDescription(
        key="lte_rsrp",
        translation_key="lte_rsrp",
        name="LTE RSRP",
        native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        state_class=SensorStateClass.MEASUREMENT,
        data_path="lte",
        data_key="rsrp",
    ),
    RouterOSSensorDescription(
        key="lte_rsrq",
        translation_key="lte_rsrq",
        name="LTE RSRQ",
        native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS,
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        state_class=SensorStateClass.MEASUREMENT,
        data_path="lte",
        data_key="rsrq",
    ),
    RouterOSSensorDescription(
        key="lte_sinr",
        translation_key="lte_sinr",
        name="LTE SINR",
        native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS,
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        state_class=SensorStateClass.MEASUREMENT,
        data_path="lte",
        data_key="sinr",
    ),
    RouterOSSensorDescription(
        key="lte_band",
        translation_key="lte_band",
        name="LTE Band",
        data_path="lte",
        data_key="band",
    ),
    RouterOSSensorDescription(
        key="lte_cell_id",
        translation_key="lte_cell_id",
        name="LTE Cell ID",
        data_path="lte",
        data_key="cell-id",
    ),
    RouterOSSensorDescription(
        key="lte_lac",
        translation_key="lte_lac",
        name="LTE LAC",
        data_path="lte",
        data_key="lac",
    ),
    RouterOSSensorDescription(
        key="lte_mcc",
        translation_key="lte_mcc",
        name="LTE MCC",
        data_path="lte",
        data_key="mcc",
    ),
    RouterOSSensorDescription(
        key="lte_mnc",
        translation_key="lte_mnc",
        name="LTE MNC",
        data_path="lte",
        data_key="mnc",
    ),
    RouterOSSensorDescription(
        key="lte_imei",
        translation_key="lte_imei",
        name="LTE IMEI",
        data_path="lte",
        data_key="imei",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    RouterOSSensorDescription(
        key="lte_iccid",
        translation_key="lte_iccid",
        name="LTE ICCID",
        data_path="lte",
        data_key="iccid",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    RouterOSSensorDescription(
        key="lte_operator",
        translation_key="lte_operator",
        name="LTE Operator",
        data_path="lte",
        data_key="current-operator",
    ),
    RouterOSSensorDescription(
        key="lte_session_uptime",
        translation_key="lte_session_uptime",
        name="LTE Session Uptime",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement="s",
        data_path="lte",
        data_key="session-uptime",
    ),
    RouterOSSensorDescription(
        key="lte_cqi",
        translation_key="lte_cqi",
        name="LTE CQI",
        state_class=SensorStateClass.MEASUREMENT,
        data_path="lte",
        data_key="cqi",
    ),
    RouterOSSensorDescription(
        key="lte_ca_band",
        translation_key="lte_ca_band",
        name="LTE CA Band",
        data_path="lte",
        data_key="ca-band",
    ),
    RouterOSSensorDescription(
        key="lte_enb_id",
        translation_key="lte_enb_id",
        name="LTE eNB ID",
        data_path="lte",
        data_key="enb-id",
    ),
    RouterOSSensorDescription(
        key="lte_phy_cellid",
        translation_key="lte_phy_cellid",
        name="LTE Physical Cell ID",
        data_path="lte",
        data_key="phy-cellid",
    ),
    RouterOSSensorDescription(
        key="lte_data_class",
        translation_key="lte_data_class",
        name="LTE Data Class",
        data_path="lte",
        data_key="data-class",
    ),
)

SYSTEM_SENSORS: tuple[RouterOSSensorDescription, ...] = (
    RouterOSSensorDescription(
        key="cpu_load",
        translation_key="cpu_load",
        name="CPU Load",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        data_path="system",
        data_key="cpu-load",
    ),
    RouterOSSensorDescription(
        key="memory_usage",
        translation_key="memory_usage",
        name="Memory Usage",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        data_path="system",
        data_key="memory-usage",
    ),
    RouterOSSensorDescription(
        key="uptime",
        translation_key="uptime",
        name="Uptime",
        device_class=SensorDeviceClass.TIMESTAMP,
        data_path="system",
        data_key="uptime",
    ),
    RouterOSSensorDescription(
        key="disk_usage",
        translation_key="disk_usage",
        name="Disk Usage",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        data_path="system",
        data_key="disk-usage",
    ),
)

WIFI_CLIENT_SENSOR = RouterOSSensorDescription(
    key="wifi_client_count",
    translation_key="wifi_client_count",
    name="WiFi Clients",
    state_class=SensorStateClass.MEASUREMENT,
    data_path="wifi",
    data_key="client_count",
    icon="mdi:wifi",
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up RouterOS LTE sensors from a config entry."""
    coordinator: RouterOSCoordinator = hass.data[DOMAIN][entry.entry_id]

    monitored = entry.options.get(CONF_MONITORED_INTERFACES)

    entities: list[SensorEntity] = []

    # LTE sensors
    for description in LTE_SENSORS:
        entities.append(RouterOSSensor(coordinator, description))

    # System sensors
    for description in SYSTEM_SENSORS:
        entities.append(RouterOSSensor(coordinator, description))

    # WiFi client count sensor
    if coordinator.data.wifi_client_count is not None:
        entities.append(RouterOSSensor(coordinator, WIFI_CLIENT_SENSOR))

    # Interface sensors (dynamic based on discovered interfaces)
    for iface in coordinator.data.interfaces:
        iface_name = iface["name"]
        if monitored is not None and iface_name not in monitored:
            continue
        for stat_key, stat_name, unit, dev_class, suggested_unit in (
            (
                "tx-byte",
                "TX Bytes",
                UnitOfInformation.BYTES,
                SensorDeviceClass.DATA_SIZE,
                UnitOfInformation.GIGABYTES,
            ),
            (
                "rx-byte",
                "RX Bytes",
                UnitOfInformation.BYTES,
                SensorDeviceClass.DATA_SIZE,
                UnitOfInformation.GIGABYTES,
            ),
            ("tx-packet", "TX Packets", None, None, None),
            ("rx-packet", "RX Packets", None, None, None),
        ):
            desc = RouterOSSensorDescription(
                key=f"iface_{iface_name}_{stat_key}",
                name=f"{iface_name} {stat_name}",
                native_unit_of_measurement=unit,
                device_class=dev_class,
                suggested_unit_of_measurement=suggested_unit,
                state_class=SensorStateClass.TOTAL_INCREASING,
                data_path="interface",
                data_key=stat_key,
            )
            entities.append(RouterOSInterfaceSensor(coordinator, desc, iface_name))

    async_add_entities(entities)


class RouterOSSensor(RouterOSEntity, SensorEntity):
    """Representation of a RouterOS sensor."""

    entity_description: RouterOSSensorDescription

    def __init__(
        self,
        coordinator: RouterOSCoordinator,
        description: RouterOSSensorDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.entry.entry_id}_{description.key}"

    @property
    def native_value(self) -> Any | None:
        """Return the sensor value."""
        data = self.coordinator.data
        if self.entity_description.data_path == "lte":
            value = data.lte.get(self.entity_description.data_key)
            if self.entity_description.data_key == "session-uptime" and value:
                return self._parse_uptime(str(value))
            return value
        if self.entity_description.data_path == "system":
            return self._get_system_value()
        if self.entity_description.data_path == "wifi":
            return data.wifi_client_count
        return None

    @staticmethod
    def _parse_uptime(uptime_str: str) -> int:
        """Parse RouterOS uptime string (e.g. '3w2d12h05m30s') to seconds."""
        import re

        total = 0
        for value, unit in re.findall(r"(\d+)([wdhms])", uptime_str):
            n = int(value)
            if unit == "w":
                total += n * 604800
            elif unit == "d":
                total += n * 86400
            elif unit == "h":
                total += n * 3600
            elif unit == "m":
                total += n * 60
            elif unit == "s":
                total += n
        return total

    def _get_system_value(self) -> Any | None:
        """Calculate system sensor values."""
        system = self.coordinator.data.system
        key = self.entity_description.data_key

        if key == "uptime":
            raw = system.get("uptime")
            if raw is None:
                return None
            from datetime import timedelta

            if isinstance(raw, timedelta):
                seconds = int(raw.total_seconds())
            elif isinstance(raw, str):
                seconds = self._parse_uptime(raw)
            else:
                seconds = int(raw)
            return dt_util.utcnow() - timedelta(seconds=seconds)

        if key == "memory-usage":
            total = system.get("total-memory", 0)
            free = system.get("free-memory", 0)
            if total > 0:
                return round((total - free) / total * 100, 1)
            return None

        if key == "disk-usage":
            total = system.get("total-hdd-space", 0)
            free = system.get("free-hdd-space", 0)
            if total > 0:
                return round((total - free) / total * 100, 1)
            return None

        return system.get(key)


class RouterOSInterfaceSensor(RouterOSEntity, SensorEntity):
    """Representation of a RouterOS interface sensor."""

    entity_description: RouterOSSensorDescription

    def __init__(
        self,
        coordinator: RouterOSCoordinator,
        description: RouterOSSensorDescription,
        interface_name: str,
    ) -> None:
        """Initialize the interface sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._interface_name = interface_name
        self._attr_unique_id = f"{coordinator.entry.entry_id}_{description.key}"

    @property
    def native_value(self) -> Any | None:
        """Return the sensor value."""
        for iface in self.coordinator.data.interfaces:
            if iface["name"] == self._interface_name:
                return iface.get(self.entity_description.data_key)
        return None
