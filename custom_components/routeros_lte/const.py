"""Constants for the MikroTik RouterOS LTE integration."""

from datetime import timedelta

DOMAIN = "routeros_lte"

DEFAULT_PORT = 8728
DEFAULT_SCAN_INTERVAL = timedelta(seconds=30)

CONF_HOST = "host"
CONF_PORT = "port"
CONF_USERNAME = "username"
CONF_PASSWORD = "password"

PLATFORMS = ["sensor", "binary_sensor"]

# LTE monitor keys
LTE_KEYS = [
    "rssi",
    "rsrp",
    "rsrq",
    "sinr",
    "band",
    "cell-id",
    "lac",
    "mcc",
    "mnc",
    "connection-status",
]

# System resource keys
SYSTEM_KEYS = [
    "cpu-load",
    "free-memory",
    "total-memory",
    "uptime",
    "free-hdd-space",
    "total-hdd-space",
    "board-name",
    "version",
]
