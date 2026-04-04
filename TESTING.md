# Testing Guide

## Testing with Mock Data (No Router Required)

The scraper includes a test mode that uses mock data:

```bash
./wui_scraper -verbose
```

This uses the `test` scraper type in `config_scrapers.yaml` and returns simulated FIOS G1100 metrics without needing an actual router.

### Output Example
```
Results for FIOS G1100 Router (Test): map[
  device:fios_g1100
  mock_metrics:map[
    connected_devices:12
    lan_ip:192.168.1.1
    signal_strength:-45
    throughput_mbps:450
    uptime_seconds:3600
    wan_ip:203.0.113.42
    wifi_enabled:true
    wifi_ssid:FIOS-ABC123
  ]
  ...
]
```

## Testing with Verbose Output

Enable verbose logging to see HTTP requests, responses, and debugging details:

```bash
./wui_scraper -verbose
```

This shows:
- Request URL and timeout
- Response status code
- Response headers
- Response body (first 1000 characters)
- Any errors encountered

## Testing with Response Saving

Save HTTP responses to files for inspection:

```bash
./wui_scraper -save
```

This creates a `responses/` directory with HTML files of each response you can inspect in a text editor or browser.

## Testing with a Real FIOS G1100 Router

### Prerequisites
1. FIOS G1100 accessible at the URL in your config
2. May require login credentials (see below)

### Configuration

Edit `config_scrapers.yaml`:

```yaml
scrapers:
  - name: "My FIOS G1100"
    type: "fios"
    url: "http://192.168.1.1"  # or https://192.168.1.1
    timeout: 10
    enabled: true
```

### Testing Connection

```bash
# Test verbose mode to see what's being retrieved
./wui_scraper -verbose

# Save responses to inspect HTML structure
./wui_scraper -save -verbose
```

### Common Issues

**Connection Timeout**
- Router not responding at given URL
- Try `ping 192.168.1.1` first
- Check if router uses HTTPS instead of HTTP

**401/403 Unauthorized**
- Router requires authentication
- Check response saved in `responses/` folder
- Update scraper to handle login (POST request with credentials)

**No Metrics Extracted**
- HTML structure doesn't match what parser expects
- Use `-save` flag to inspect actual HTML
- Modify `fios_scraper.go` to parse correct page structure

### Custom Parsing for Your Router

Once you can connect successfully, modify `fios_scraper.go`:

```go
// Look for specific elements in the HTML
doc.Find(".status-row").Each(func(i int, s *goquery.Selection) {
    key := s.Find(".label").Text()
    value := s.Find(".value").Text()
    // Extract metric...
})
```

Use `-save` flag to inspect the HTML in `responses/` folder and update selectors accordingly.
