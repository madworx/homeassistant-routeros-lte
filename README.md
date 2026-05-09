# MikroTik RouterOS LTE Integration for Home Assistant

[![HACS](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://hacs.xyz)
[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=madworx&repository=homeassistant-routeros-lte&category=integration)

A Home Assistant custom integration that polls MikroTik RouterOS routers for LTE status, system resources, and interface statistics via the RouterOS API.

## Features

- **LTE Monitoring**: RSSI, RSRP, RSRQ, SINR, band, cell ID, LAC, MCC, MNC
- **System Resources**: CPU load, memory usage, uptime, disk usage
- **Interface Statistics**: TX/RX bytes and packets per interface
- **Connection Status**: Binary sensors for LTE and interface states

## Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Click "Integrations"
3. Click the three dots menu → "Custom repositories"
4. Add `https://github.com/madworx/homeassistant-routeros-lte` with category "Integration"
5. Install "MikroTik RouterOS LTE"
6. Restart Home Assistant

### Manual

1. Copy `custom_components/routeros_lte` to your `config/custom_components/` directory
2. Restart Home Assistant

## Configuration

1. Go to Settings → Devices & Services → Add Integration
2. Search for "MikroTik RouterOS LTE"
3. Enter your router's IP, port (default 8728), username, and password

### Selecting Interfaces

By default, all interfaces discovered on the router are monitored. To choose which interfaces create entities:

1. Go to Settings → Devices & Services
2. Find the "MikroTik RouterOS LTE" integration and click **Configure**
3. Select which interfaces to monitor — unselected interfaces will not create entities

Changing this setting reloads the integration automatically.

### RouterOS API Setup

Ensure the API service is enabled on your MikroTik router:

```
/ip service enable api
```

## Sensors

### LTE Sensors
| Sensor | Unit | Description |
|--------|------|-------------|
| RSSI | dBm | Received Signal Strength Indicator |
| RSRP | dBm | Reference Signal Received Power |
| RSRQ | dB | Reference Signal Received Quality |
| SINR | dB | Signal to Interference+Noise Ratio |
| Band | - | Current LTE band |
| Cell ID | - | Current cell identifier |
| LAC | - | Location Area Code |
| MCC | - | Mobile Country Code |
| MNC | - | Mobile Network Code |

### System Sensors
| Sensor | Unit | Description |
|--------|------|-------------|
| CPU Load | % | Current CPU utilization |
| Memory Usage | % | RAM utilization |
| Uptime | - | System uptime duration |
| Disk Usage | % | Disk utilization |

### Interface Sensors (per monitored interface)
| Sensor | Unit | Description |
|--------|------|-------------|
| TX Bytes | B | Total transmitted bytes |
| RX Bytes | B | Total received bytes |
| TX Packets | - | Total transmitted packets |
| RX Packets | - | Total received packets |

### Binary Sensors
| Sensor | Description |
|--------|-------------|
| LTE Connected | Whether the LTE modem is connected |
| {interface} Running | Whether a monitored interface is running |

## Requirements

- Home Assistant 2024.1.0+
- MikroTik RouterOS with API enabled (port 8728)
- User with API access permissions

## License

MIT
