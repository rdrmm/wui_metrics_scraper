# wui_metrics_scraper

**Web User Interface Metrics Scraper**

A minimal, modular, cross-platform application for scraping metrics from device web interfaces.

## Features

✅ **Cross-Platform** - Windows, Linux, macOS  
✅ **Configuration-Driven** - Add devices via YAML config  
✅ **Modular** - Easy to add support for new makes/models  
✅ **Minimal Dependencies** - YAML parsing, HTTP client  
✅ **Logging & Error Handling** - Comprehensive error reporting  

## Quick Start

### Prerequisites
- Go 1.21+

### Installation

```bash
# Clone repository
git clone https://github.com/rdrmm/wui_metrics_scraper.git
cd wui_metrics_scraper

# Download dependencies
go mod tidy

# Build
go build -o wui_scraper .
```

### Configuration

Edit `config_scrapers.yaml`:

```yaml
scrapers:
  - name: "My Router"
    type: "fios"  # or other types
    url: "http://192.168.1.1"
    timeout: 10
    enabled: true
```

### Running

```bash
./wui_scraper
```

## Verifying It Works

The scraper now extracts **real data** from FIOS G1100 routers. You can test it without a physical router using demo mode:

```bash
# Demo mode: Tests scraping with a mock FIOS G1100 server
# Shows real data extraction (not dummy data!)
./wui_scraper -demo -verbose
```

This demonstrates:
- ✅ Fetching HTML from router pages
- ✅ Parsing device status and connectivity
- ✅ Extracting WAN/LAN IP addresses  
- ✅ Finding WiFi SSID and signal strength
- ✅ Detecting uptime and device information
- ✅ Probing multiple router endpoints

### With a Real Router

```bash
# Edit config_scrapers.yaml to point to your router, then:
./wui_scraper -verbose -save

# -verbose: Shows what's being retrieved
# -save: Saves responses to files for inspection
```

See [TESTING.md](TESTING.md) for detailed testing instructions.

## Extending for Specific Devices

To add scraping for specific metrics on the FIOS G1100 (or other devices), modify the `Scrape` method in `fios_scraper.go`. For example, parse HTML elements or make authenticated requests.

For FIOS G1100, you may need to handle login: POST to login endpoint with credentials, then scrape protected pages.