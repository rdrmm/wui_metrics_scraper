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
    'device_status': Gauge('router_device_online', '1 if online, 0 if offline', ['name', 'mac', 'ip']),
    'device_rssi': Gauge('router_device_rssi', 'Signal strength (if wireless)', ['name', 'mac']),
    
    # Network/Interface Metrics
    'net_bytes': Gauge('router_network_bytes_total', 'Cumulative bytes', ['interface', 'direction']),
    'net_errors': Gauge('router_network_errors_total', 'Cumulative errors', ['interface', 'direction']),
    'net_packets': Gauge('router_network_packets_total', 'Cumulative packets', ['interface', 'direction']),
    
    # Summary Metrics
    'active_client_count': Gauge('router_clients_active_total', 'Total number of online clients')
}

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
    # 1. Process Devices
    devices = api("/api/devices")
    if isinstance(devices, list):
        online_count = 0
        for dev in devices:
            name = dev.get('name', 'Unknown')
            mac = dev.get('mac', '00:00:00:00:00:00')
            ip = dev.get('ipAddress', '0.0.0.0')
            
            # Status is a boolean in your JSON
            status_val = 1 if dev.get('status') is True else 0
            if status_val: online_count += 1
            
            metrics['device_status'].labels(name=name, mac=mac, ip=ip).set(status_val)
            
            # Track RSSI if it's not 0 (0 usually means Ethernet or offline)
            if dev.get('rssi', 0) != 0:
                metrics['device_rssi'].labels(name=name, mac=mac).set(dev['rssi'])
        
        metrics['active_client_count'].set(online_count)

    # 2. Process Network Interfaces
    networks = api("/api/network")
    if isinstance(networks, list):
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
            time.sleep(30) # Scrape every 30s for better speed resolution