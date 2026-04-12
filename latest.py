from prometheus_client import start_http_server, Gauge
import requests
import hashlib
import time
import urllib3
import os
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

BASE = (os.getenv("ROUTER_BASE") or "https://192.168.1.1").rstrip("/")
PASSWORD = os.getenv("ROUTER_PASSWORD")

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

session = requests.Session()
session.verify = False
session.headers.update({
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json",
    "Referer": f"{BASE}/",
    "Origin": BASE,
    "Content-Type": "application/json;charset=UTF-8"
})

# --- Metrics Configuration ---
metrics = {
    # Device Metrics
    'device_status': Gauge('router_device_online', '1 if online, 0 if offline', ['name', 'mac', 'ip', 'ssid']),
    'device_rssi': Gauge('router_device_rssi', 'Signal strength (if wireless)', ['name', 'mac']),
    'device_connection_rate': Gauge('router_device_connection_rate', 'Connection rate in Mbps', ['name', 'mac']),
    
    # Network/Interface Metrics
    'net_bytes': Gauge('router_network_bytes_total', 'Cumulative bytes', ['interface', 'direction']),
    'net_errors': Gauge('router_network_errors_total', 'Cumulative errors', ['interface', 'direction']),
    'net_packets': Gauge('router_network_packets_total', 'Cumulative packets', ['interface', 'direction']),
    
    # WiFi-specific Metrics (from /api/wireless)
    'wifi_channel_occupancy': Gauge('router_wifi_channel_occupancy_percent', 'WiFi channel occupancy percentage', ['ssid']),
    'wifi_channel_idle': Gauge('router_wifi_channel_idle_percent', 'WiFi channel idle percentage', ['ssid']),
    'wifi_rx_errors': Gauge('router_wifi_rx_errors_total', 'WiFi RX error count', ['ssid']),
    'wifi_rx_bytes': Gauge('router_wifi_rx_bytes_total', 'WiFi RX bytes total', ['ssid']),
    'wifi_tx_bytes': Gauge('router_wifi_tx_bytes_total', 'WiFi TX bytes total', ['ssid']),
    'wifi_max_rate': Gauge('router_wifi_max_rate_mbps', 'WiFi maximum supported rate in Mbps', ['ssid']),
    'wifi_radio_enabled': Gauge('router_wifi_radio_enabled', '1 if radio enabled, 0 if disabled', ['ssid']),
    'wifi_clients_per_ssid': Gauge('router_wifi_clients_per_ssid', 'Number of clients connected to SSID', ['ssid']),
    
    # Summary Metrics
    'active_client_count': Gauge('router_clients_active_total', 'Total number of online clients')
}

# Cache for wireless networks to map frequency->SSID
wireless_networks_cache = {}

def safe_json(resp):
    try:
        return resp.json()
    except:
        return None

def login():
    attempts = 0
    while attempts < 3:
        try:
            r = session.get(f"{BASE}/api/login", timeout=10)
            j = safe_json(r)
            if not j or "passwordSalt" not in j:
                time.sleep(2); attempts += 1; continue

            hashed = hashlib.sha512((PASSWORD + j["passwordSalt"]).encode()).hexdigest()
            session.post(f"{BASE}/api/login", json={"password": hashed}, timeout=10)

            # Domain setup for cookies
            domain = BASE.split("//")[-1].split(":")[0]
            session.cookies.set("bhr4HasEnteredAdvanced", "false", domain=domain)
            session.cookies.set("test", "1", domain=domain)
            
            logger.info("Login successful.")
            return True
        except Exception as e:
            logger.error(f"Login failed: {e}")
            attempts += 1; time.sleep(2)
    return False

def api(path):
    xsrf = session.cookies.get("XSRF-TOKEN")
    try:
        r = session.get(BASE + path, headers={"X-XSRF-TOKEN": xsrf}, timeout=15)
        if r.status_code in (401, 403) or "<html" in r.text.lower():
            if login():
                return api(path)
            return None
        return safe_json(r)
    except Exception as e:
        logger.error(f"API {path} error: {e}")
        return None

def update_metrics():
    logger.info("Starting metrics update")
    global wireless_networks_cache
    
    # 0. Process Wireless Networks first (to build SSID cache)
    wireless = api("/api/wireless")
    if isinstance(wireless, list):
        logger.info(f"Found {len(wireless)} wireless networks")
        for wnet in wireless:
            ssid = wnet.get('ssid', f"Network_{wnet.get('id', 0)}")
            enabled = wnet.get('enabled', wnet.get('radioEnabled', False))
            
            # Store mapping of frequency->SSID based on mode
            # mode: 8=802.11n (2.4GHz), 16=802.11ac (5GHz), 32=802.11ax
            mode = wnet.get('mode')
            if mode == 8:
                wireless_networks_cache['2.4'] = ssid
            elif mode in (16, 32):  # 802.11ac or 802.11ax
                wireless_networks_cache['5'] = ssid
            
            # Emit WiFi metrics
            metrics['wifi_radio_enabled'].labels(ssid=ssid).set(1 if enabled else 0)
            
            if enabled:
                # Channel metrics
                channel_occ = wnet.get('channelOccupancy', 0)
                channel_idle = wnet.get('channelIdle', 0)
                
                metrics['wifi_channel_occupancy'].labels(ssid=ssid).set(channel_occ)
                metrics['wifi_channel_idle'].labels(ssid=ssid).set(channel_idle)
                
                # Traffic metrics
                metrics['wifi_rx_errors'].labels(ssid=ssid).set(wnet.get('rxErrors', 0))
                metrics['wifi_rx_bytes'].labels(ssid=ssid).set(wnet.get('rxBytes', 0))
                metrics['wifi_tx_bytes'].labels(ssid=ssid).set(wnet.get('txBytes', 0))
                
                # Max rate
                rate_str = wnet.get('maxBitRate', '')
                if 'Mbps' in rate_str:
                    try:
                        rate = float(rate_str.replace(' Mbps', ''))
                        metrics['wifi_max_rate'].labels(ssid=ssid).set(rate)
                    except ValueError:
                        pass
    
    # 1. Process Devices
    devices = api("/api/devices")
    if isinstance(devices, list):
        logger.info(f"Found {len(devices)} devices")
        online_count = 0
        ssid_clients = {}
        
        for dev in devices:
            name = dev.get('name', 'Unknown')
            mac = dev.get('mac', '00:00:00:00:00:00')
            ip = dev.get('ipAddress', '0.0.0.0')
            
            # Determine SSID from frequency field using wireless cache
            frequency = dev.get('frequency', '')
            if frequency in wireless_networks_cache:
                ssid = wireless_networks_cache[frequency]
            elif frequency == '2.4':
                ssid = 'FiOS-2.4GHz'  # Fallback
            elif frequency == '5':
                ssid = 'FiOS-5GHz'  # Fallback
            elif frequency == '6':
                ssid = 'FiOS-6GHz'  # Fallback
            else:
                ssid = 'Wired'  # For wired devices
            
            # Status is a boolean in your JSON
            status_val = 1 if dev.get('status') is True else 0
            if status_val: 
                online_count += 1
                # Count clients per SSID
                if ssid not in ssid_clients:
                    ssid_clients[ssid] = 0
                ssid_clients[ssid] += 1
            
            metrics['device_status'].labels(name=name, mac=mac, ip=ip, ssid=ssid).set(status_val)
            
            # Track RSSI if it's not 0 (0 usually means Ethernet or offline)
            if dev.get('rssi', 0) != 0:
                metrics['device_rssi'].labels(name=name, mac=mac).set(dev['rssi'])
            
            # Track connection rate if available (use currentRxModulationRate for wireless)
            rate_str = dev.get('currentRxModulationRate') or dev.get('modulationRate', '')
            if rate_str and 'Mbps' in rate_str:
                try:
                    rate = float(rate_str.replace(' Mbps', ''))
                    metrics['device_connection_rate'].labels(name=name, mac=mac).set(rate)
                except ValueError:
                    pass
        
        metrics['active_client_count'].set(online_count)
        
        # Set client counts per SSID
        for ssid, count in ssid_clients.items():
            metrics['wifi_clients_per_ssid'].labels(ssid=ssid).set(count)

    # 2. Process Network Interfaces
    networks = api("/api/network")
    if isinstance(networks, list):
        logger.info(f"Found {len(networks)} network interfaces")
        for net in networks:
            iface_name = net.get('name', 'Unknown')
            
            # Throughput
            metrics['net_bytes'].labels(interface=iface_name, direction='rx').set(net.get('rxBytes', 0))
            metrics['net_bytes'].labels(interface=iface_name, direction='tx').set(net.get('txBytes', 0))
            
            # Errors (Critical for "slowness" troubleshooting)
            metrics['net_errors'].labels(interface=iface_name, direction='rx').set(net.get('rxErrors', 0))
            metrics['net_errors'].labels(interface=iface_name, direction='tx').set(net.get('txErrors', 0))
            
            # Packets
            metrics['net_packets'].labels(interface=iface_name, direction='rx').set(net.get('rxPackets', 0))
            metrics['net_packets'].labels(interface=iface_name, direction='tx').set(net.get('txPackets', 0))

if __name__ == "__main__":
    if not PASSWORD:
        logger.critical("No ROUTER_PASSWORD found in environment!")
    elif login():
        start_http_server(9100)
        logger.info("Metrics available at http://localhost:9100/metrics")
        while True:
            update_metrics()
            time.sleep(90) # Scrape every 90s for better speed resolution