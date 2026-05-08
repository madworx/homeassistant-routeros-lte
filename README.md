# MikroTik RouterOS LTE Integration for Home Assistant

[![HACS](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://hacs.xyz)

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
4. Add `https://github.com/madworx/homeassistant-routeros` with category "Integration"
5. Install "MikroTik RouterOS LTE"
6. Restart Home Assistant

### Manual

1. Copy `custom_components/routeros_lte` to your `config/custom_components/` directory
2. Restart Home Assistant

## Configuration

1. Go to Settings → Devices & Services → Add Integration
2. Search for "MikroTik RouterOS LTE"
3. Enter your router's IP, port (default 8728), username, and password

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

### System Sensors
| Sensor | Unit | Description |
|--------|------|-------------|
| CPU Load | % | Current CPU utilization |
| Memory Usage | % | RAM utilization |
| Uptime | - | System uptime duration |
| Disk Usage | % | Disk utilization |

### Interface Sensors (per interface)
| Sensor | Unit | Description |
|--------|------|-------------|
| TX Bytes | B | Total transmitted bytes |
| RX Bytes | B | Total received bytes |
| TX Packets | - | Total transmitted packets |
| RX Packets | - | Total received packets |

## Requirements

- Home Assistant 2024.1.0+
- MikroTik RouterOS with API enabled (port 8728)
- User with API access permissions

## License

MIT
