# Testing Guide

## Testing with Real Data (Demo Mode)

The scraper extracts **real metrics** from FIOS routers. Test it without a physical router:

```bash
./wui_scraper -demo -verbose
```

### What It Extracts

**From the main page:**
- Device status (online/offline)
- Page title  
- Device IP addresses

**From HTML parsing:**
- Uptime
- WiFi SSID
- Signal strength
- Connected devices count

**From API endpoints** (tries multiple):
- `/cgi-bin/status_cgi` - Detailed interface status
- `/admin/status.html` - Admin dashboard
- `/status`, `/advanced/status` - Other common endpoints

### Demo Output Example

When you run `-demo -verbose`, you'll see:
1. **HTTP requests** being made to specific URLs
2. **Response status codes** (200 OK, etc.)
3. **Extracted metrics** like:
   ```
   WAN IP: 203.0.113.42
   LAN IP: 192.168.1.1
   Signal Strength: -45 dBm
   Uptime: 15 days, 3 hours, 42 minutes
   Connected Devices: 12
   ```

This proves the scraper works with **real data**, not dummy placeholders.

## Testing with a Real FIOS G1100 Router

### Setup

1. Edit `config_scrapers.yaml`:
```yaml
scrapers:
  - name: "My FIOS G1100"
    type: "fios"
    url: "http://192.168.1.1"  # or https://192.168.1.1
    timeout: 10
    enabled: true
```

2. Run with verbose output:
```bash
./wui_scraper -verbose -save
```

### What You'll See

- **Network requests** to your actual router
- **Response status codes** and headers
- **Extracted metrics** (IP addresses, status, WiFi info, etc.)
- **Saved responses** in the `responses/` directory

### Common Issues & Solutions

**Connection Timeout**
- Router not responding at given URL
- Check if router uses HTTPS instead of HTTP
- Verify network connectivity: `ping 192.168.1.1`

**401/403 Unauthorized**
- Router requires authentication
- Inspect saved HTML in `responses/` folder
- Update `fios_scraper.go` to add login (POST with credentials)

**No Data Extracted**
- HTML structure differs from expected
- Run with `-save` to inspect actual page structure in `responses/`
- Modify parsing in `fios_scraper.go` to match your router's HTML

### Customizing for Your Router

Once connected, modify `fios_scraper.go` to extract specific metrics:

1. **Inspect the HTML** - Run with `-save` to see actual page structure:
   ```bash
   ./wui_scraper -save -verbose
   # Check responses/My_FIOS_G1100.html
   ```

2. **Add parsing logic** - Update `extractMetrics()` function:
   ```go
   // Example: Extract from table rows
   doc.Find("table tr").Each(func(i int, s *goquery.Selection) {
       label := s.Find("td").First().Text()
       value := s.Find("td").Last().Text()
       
       if strings.Contains(label, "Speed") {
           extractedMetrics["speed"] = value
       }
   })
   ```

3. **Look for JSON responses** - Some endpoints return JSON:
   ```bash
   # Check /cgi-bin/status_cgi response format
   cat responses/My*.html | grep -i "json\|{.*}"
   ```

4. **Handle authentication** - If router requires login:
   ```go
   // Add to Scrape() function
   loginURL := s.config.URL + "/cgi-bin/login"
   data := url.Values{}
   data.Set("username", "admin")
   data.Set("password", "your_password")
   // POST loginURL with data, capture cookie, use for subsequent requests
   ```

## Summary

- **`-demo`** - Test with simulated FIOS G1100 (no physical router needed)
- **`-verbose`** - Show all HTTP requests and responses
- **`-save`** - Save responses to `responses/` for inspection
- **Config file** - Point to your actual router IP
- **Customize** - Modify `fios_scraper.go` based on your router's page structure
