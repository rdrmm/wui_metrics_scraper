package main

import (
	"log"
)

// TestScraper provides mock data for testing
type TestScraper struct {
	config ScraperConfig
}

// Scrape returns mock FIOS G1100 data for testing
func (s *TestScraper) Scrape(verbose bool, saveResponses bool) (map[string]interface{}, error) {
	log.Printf("TEST SCRAPER: Returning mock data for %s", s.config.Name)
	
	mockData := map[string]interface{}{
		"device":       "fios_g1100",
		"name":         s.config.Name,
		"status":       "online",
		"page_title":   "Fios Gateway G1100 Admin",
		"response_size": 12534,
		"mock_metrics": map[string]interface{}{
			"uptime_seconds":      3600,
			"wan_ip":              "203.0.113.42",
			"lan_ip":              "192.168.1.1",
			"connected_devices":   12,
			"wifi_enabled":        true,
			"wifi_ssid":           "FIOS-ABC123",
			"signal_strength":     -45,
			"throughput_mbps":     450,
		},
	}
	
	if verbose {
		log.Printf("Mock metrics generated: %+v", mockData)
	}
	
	return mockData, nil
}
