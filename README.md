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

The scraper includes a **test mode** with mock data so you can verify it's working before connecting to a real router:

```bash
# Verbose mode shows all HTTP requests, responses, and metrics
./wui_scraper -verbose

# Save mode saves HTTP responses to files for inspection
./wui_scraper -save

# Combine both for maximum debugging
./wui_scraper -verbose -save
```

See [TESTING.md](TESTING.md) for detailed testing instructions.

## Extending for Specific Devices

To add scraping for specific metrics on the FIOS G1100 (or other devices), modify the `Scrape` method in `fios_scraper.go`. For example, parse HTML elements or make authenticated requests.

For FIOS G1100, you may need to handle login: POST to login endpoint with credentials, then scrape protected pages.