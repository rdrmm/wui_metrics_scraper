from prometheus_client import start_http_server, Gauge
import requests
import hashlib
import time
import urllib3

BASE = "https://192.168.1.1"
PASSWORD = "TOPSECRET"

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

session = requests.Session()
session.verify = False

# Browser-like headers required by your router
session.headers.update({
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json, text/plain, */*",
    "Referer": BASE + "/",
    "Origin": BASE,
    "Content-Type": "application/json;charset=UTF-8"
})

metric_cache = {}

def safe_json(resp):
    """Return JSON or None if HTML or invalid."""
    try:
        return resp.json()
    except:
        print("Non-JSON:", resp.text[:200])
        return None

# def login():
#     print("Logging in?")

#     # 1. Get salt
#     r = session.get(f"{BASE}/api/login")
#     j = safe_json(r)
#     if not j or "passwordSalt" not in j:
#         time.sleep(1)
#         return login()

#     salt = j["passwordSalt"]

#     # 2. Hash password + salt
#     hashed = hashlib.sha512((PASSWORD + salt).encode()).hexdigest()

#     # 3. Login
#     r = session.post(f"{BASE}/api/login", json={"password": hashed})

#     # 4. Required cookies
#     session.cookies.set("bhr4HasEnteredAdvanced", "false", domain="192.168.1.1")
#     session.cookies.set("test", "1", domain="192.168.1.1")

#     print("Logged in. Cookies:", session.cookies.get_dict())

def login():
    print("Logging in?")

    r = session.get(f"{BASE}/api/login")
    print("GET /api/login status:", r.status_code)
    print("GET /api/login headers:", r.headers)
    print("GET /api/login body (first 300 chars):")
    print(r.text[:300])
    print("-" * 60)

    j = safe_json(r)
    if not j:
        print("No JSON from /api/login, stopping here.")
        return

    print("Parsed JSON from /api/login:", j)

    if "passwordSalt" not in j:
        print("No passwordSalt in JSON, stopping here.")
        return

    salt = j["passwordSalt"]
    hashed = hashlib.sha512((PASSWORD + salt).encode()).hexdigest()

    r = session.post(f"{BASE}/api/login", json={"password": hashed})
    print("POST /api/login status:", r.status_code)
    print("POST /api/login body (first 300 chars):")
    print(r.text[:300])

    session.cookies.set("bhr4HasEnteredAdvanced", "false", domain="192.168.1.1")
    session.cookies.set("test", "1", domain="192.168.1.1")

    print("Cookies after login:", session.cookies.get_dict())


def renew_session():
    """Keep the router session alive."""
    xsrf = session.cookies.get("XSRF-TOKEN")
    headers = {"X-XSRF-TOKEN": xsrf}

    r = session.put(f"{BASE}/api/session/renew", headers=headers)
    return r.status_code == 200

def api(path):
    """Fetch JSON from router API with auto-relogin."""
    xsrf = session.cookies.get("XSRF-TOKEN")
    headers = {"X-XSRF-TOKEN": xsrf}

    r = session.get(BASE + path, headers=headers)

    # Router returns HTML login page on expiration
    if r.status_code in (401, 403) or "<html" in r.text.lower():
        print("Session expired ? re-login")
        login()
        return api(path)

    return safe_json(r)

def export_metrics(prefix, data):
    """Recursively export all numeric fields as Prometheus metrics."""
    if isinstance(data, dict):
        for key, value in data.items():
            export_metrics(f"{prefix}_{key}", value)

    elif isinstance(data, list):
        for idx, item in enumerate(data):
            export_metrics(f"{prefix}_{idx}", item)

    else:
        if isinstance(data, (int, float)):
            metric_name = prefix.lower().replace("-", "_")

            if metric_name not in metric_cache:
                metric_cache[metric_name] = Gauge(metric_name, metric_name)

            metric_cache[metric_name].set(data)

def update_all():
    # Keep session alive
    if not renew_session():
        print("Session expired ? re-login")
        login()

    # Scrape all available endpoints
    export_metrics("router_devices", api("/api/devices"))
    export_metrics("router_network", api("/api/network"))
    export_metrics("router_ipv6", api("/api/ipv6"))

if __name__ == "__main__":
    login()
    # print(api("/api/devices"))
    start_http_server(9100)

    while True:
        update_all()
        time.sleep(5)
