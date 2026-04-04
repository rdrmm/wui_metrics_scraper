package main

import (
	"fmt"
	"log"
	"net/http"
	"strings"
)

// StartMockFiosServer starts a mock FIOS G1100 server for testing
func StartMockFiosServer(port int) {
	mux := http.NewServeMux()

	// Main status page
	mux.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		html := `
<!DOCTYPE html>
<html>
<head>
    <title>Fios Gateway G1100 Admin</title>
</head>
<body>
    <h1>Fios Gateway G1100</h1>
    <div class="status">
        <p>Device Status: Connected and Online</p>
        <p>WAN IP Address: 203.0.113.42</p>
        <p>LAN IP Address: 192.168.1.1</p>
        <p>System Uptime: 15 days, 3 hours, 42 minutes</p>
    </div>
    <div class="network">
        <p>WiFi SSID: FIOS-ABC123</p>
        <p>Signal Strength: -45 dBm (Strong)</p>
        <p>Connected Devices: 12</p>
        <p>Throughput: 450 Mbps</p>
    </div>
</body>
</html>
`
		w.Header().Set("Content-Type", "text/html")
		fmt.Fprint(w, html)
	})

	// Status endpoint
	mux.HandleFunc("/cgi-bin/status_cgi", func(w http.ResponseWriter, r *http.Request) {
		data := `
Interface: WAN
Status: Connected
IP Address: 203.0.113.42
Gateway: 203.0.113.1
Primary DNS: 208.67.222.222
Secondary DNS: 208.67.220.220

Interface: LAN
Status: Connected
IP Address: 192.168.1.1
Subnet Mask: 255.255.255.0
Connected Devices: 12

WiFi: Enabled
SSID: FIOS-ABC123
Channel: 6
Signal: -45 dBm

System Uptime: 15 days 03:42:18
`
		w.Header().Set("Content-Type", "text/plain")
		fmt.Fprint(w, data)
	})

	addr := fmt.Sprintf("127.0.0.1:%d", port)
	log.Printf("Starting mock FIOS G1100 server on http://%s", addr)
	go func() {
		if err := http.ListenAndServe(addr, mux); err != nil && !strings.Contains(err.Error(), "use of closed network connection") {
			log.Printf("Server error: %v", err)
		}
	}()
}
