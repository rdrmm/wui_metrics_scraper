# Advanced WiFi Router Metrics Scraper

This project provides comprehensive WiFi troubleshooting metrics for router performance monitoring using Prometheus and Grafana.

## Features

### Enhanced WiFi Metrics
- **Real SSID Names**: Devices are tagged with actual WiFi network names (e.g., "FiOS-0K1W5", "FiOS-0K1W5-5G")
- **Channel Health**: Monitor channel occupancy and idle time to detect interference
- **Signal Quality**: RSSI measurements and connection rates per device
- **Network Load**: Client counts and traffic patterns per SSID
- **Error Detection**: Packet error rates and interface issues

### Key Metrics Collected

#### WiFi Network Metrics
- `router_wifi_radio_enabled` - Network status (enabled/disabled)
- `router_wifi_channel_occupancy_percent` - Air time utilization
- `router_wifi_channel_idle_percent` - Available air time
- `router_wifi_rx_errors_total` - Packet errors per network
- `router_wifi_max_rate_mbps` - Maximum WiFi speed capability
- `router_wifi_clients_per_ssid` - Connected devices per network

#### Device Metrics
- `router_device_online` - Device connectivity with SSID tags
- `router_device_rssi` - Signal strength per device
- `router_device_connection_rate` - Actual connection speed

#### Network Metrics
- `router_network_bytes_total` - Traffic volume by interface
- `router_network_errors_total` - Interface error counts
- `router_clients_active_total` - Total active clients

## Setup

### 1. Environment Variables
```bash
export ROUTER_BASE="https://192.168.1.1"  # Your router IP
export ROUTER_PASSWORD="your_router_password"
```

### 2. Run the Metrics Scraper
```bash
python3 latest.py
```
Metrics will be available at `http://localhost:9100/metrics`

### 3. Import Dashboard in Grafana
1. Open Grafana and go to **Dashboards** → **Import**
2. Upload the `advanced_wifi_dashboard.json` file
3. Select your Prometheus data source
4. The dashboard will appear as "Advanced WiFi Router Performance Dashboard"

## WiFi Troubleshooting Guide

### Common Issues & Solutions

#### High Channel Occupancy (>40%)
**Symptoms**: Slow WiFi, intermittent connections
**Solutions**:
- Change WiFi channel in router settings
- Avoid channels 1, 6, 11 on 2.4GHz (most congested)
- Use 5GHz band for less interference

#### Poor Signal Strength (RSSI < -80 dBm)
**Symptoms**: Slow speeds, frequent disconnections
**Solutions**:
- Move closer to router
- Remove physical obstacles
- Change antenna orientation
- Add WiFi extenders

#### High Packet Errors
**Symptoms**: Unstable connections, slow speeds
**Solutions**:
- Check for microwave ovens/other 2.4GHz interference
- Change WiFi channels
- Reduce network congestion
- Update device WiFi drivers

#### Network Overload (>15 clients per SSID)
**Symptoms**: Slow speeds for all devices
**Solutions**:
- Enable band steering (force devices to 5GHz)
- Add additional access points
- Limit guest network usage

### Alert Recommendations

#### Critical Alerts
```promql
# Channel congestion
router_wifi_channel_occupancy_percent > 70

# Poor signal quality
router_device_rssi < -85

# High error rates
rate(router_wifi_rx_errors_total[5m]) > 100
```

#### Warning Alerts
```promql
# Moderate congestion
router_wifi_channel_occupancy_percent > 50

# Weak signals
router_device_rssi < -75

# Network overload
router_wifi_clients_per_ssid > 20
```

## Dashboard Panels Explained

### WiFi Network Overview
Shows which WiFi networks are enabled/disabled with color coding.

### Active Clients by SSID
Bar chart showing device distribution across your WiFi networks.

### WiFi Channel Health
Time series showing channel occupancy vs idle time. High occupancy indicates interference.

### WiFi Packet Errors
Error rate trends per network. Increasing errors suggest interference issues.

### WiFi Maximum Rates
Table showing the maximum speed capability of each WiFi network.

### Device Connection Rates
Actual connection speeds for wireless devices.

### Device Signal Strength (RSSI)
Gauge showing signal strength for all wireless devices.

### WAN Throughput
Internet download/upload speeds.

### WiFi Interface Errors
Packet errors on WiFi interfaces.

### WiFi Traffic per SSID
Data transfer rates per WiFi network.

## API Endpoints Used

The scraper collects data from these router API endpoints:
- `/api/devices` - Device information and status
- `/api/network` - Network interface statistics
- `/api/wireless` - WiFi network configuration and statistics

## Router Compatibility

This scraper is designed for routers with similar API structures to Verizon FiOS routers. It may work with other router brands that expose similar endpoints.

## Contributing

Feel free to submit issues and enhancement requests!