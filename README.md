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

## Extending for Specific Devices

To add scraping for specific metrics on the FIOS G1100 (or other devices), modify the `Scrape` method in `fios_scraper.go`. For example, parse HTML elements or make authenticated requests.

For FIOS G1100, you may need to handle login: POST to login endpoint with credentials, then scrape protected pages.

### Run

```bash
cd src
python main.py
```

## Adding a New Device Type

1. Create a new scraper in `src/scrapers/`:

```python
from .base_scraper import BaseScraper

class NewDeviceScraper(BaseScraper):
    def scrape(self):
        # Implement scraping logic
        return {"metrics": "here"}
```

2. Register in `src/scraper_factory.py`:

```python
from scrapers.new_device_scraper import NewDeviceScraper

SCRAPER_REGISTRY = {
    'netgear': NetgearScraper,
    'asus': AsusScraper,
    'new_device': NewDeviceScraper,  # Add here
}
```

3. Update `config/scrapers.yaml` to use the new type.

## Project Structure

```
wui_metrics_scraper/
├── README.md
├── requirements.txt
├── config/
│   └── scrapers.yaml          # Configuration
├── src/
│   ├── main.py                # Entry point
│   ├── config_loader.py       # Config parser
│   ├── scraper_factory.py     # Factory pattern
│   └── scrapers/
│       ├── base_scraper.py    # Base class
│       ├── netgear_scraper.py # Netgear impl.
│       └── asus_scraper.py    # ASUS impl.
└── tests/                      # Test files
```

## Logging

Control log level in `src/main.py`:

```python
logging.basicConfig(level=logging.DEBUG)  # DEBUG, INFO, WARNING, ERROR
```

## License

MIT