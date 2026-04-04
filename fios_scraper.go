package main

import (
	"crypto/tls"
	"fmt"
	"io"
	"log"
	"net/http"
	"os"
	"path/filepath"
	"strings"
	"time"

	"github.com/PuerkitoBio/goquery"
)

// FiosScraper scrapes FIOS G1100 router
type FiosScraper struct {
	config ScraperConfig
}

// Scrape implements the Scraper interface
func (s *FiosScraper) Scrape(verbose bool, saveResponses bool) (map[string]interface{}, error) {
	log.Printf("FIOS scraper starting: %s", s.config.URL)

	client := &http.Client{
		Timeout: time.Duration(s.config.Timeout) * time.Second,
		Transport: &http.Transport{
			TLSClientConfig: &tls.Config{InsecureSkipVerify: true}, // Note: Use proper cert verification in production
		},
	}

	if verbose {
		log.Printf("Making request to: %s (timeout: %ds)", s.config.URL, s.config.Timeout)
	}

	resp, err := client.Get(s.config.URL)
	if err != nil {
		return nil, fmt.Errorf("request error: %w", err)
	}
	defer resp.Body.Close()

	if verbose {
		log.Printf("Response status: %s", resp.Status)
		log.Printf("Response headers: %v", resp.Header)
	}

	if resp.StatusCode != http.StatusOK {
		if verbose {
			body, _ := io.ReadAll(resp.Body)
			log.Printf("Error response body: %s", string(body))
		}
		return nil, fmt.Errorf("bad status: %s", resp.Status)
	}

	// Read body for inspection and parsing
	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("failed to read response body: %w", err)
	}

	if verbose {
		log.Printf("Response body size: %d bytes", len(body))
		if len(body) > 0 {
			end := len(body)
			if end > 1000 {
				end = 1000
			}
			log.Printf("Response body (first %d chars):\n%s", end, string(body[:end]))
		}
	}

	if saveResponses {
		filename := filepath.Join("responses", strings.ReplaceAll(s.config.Name, " ", "_")+".html")
		os.MkdirAll("responses", 0755)
		if err := os.WriteFile(filename, body, 0644); err != nil {
			log.Printf("Warning: failed to save response to %s: %v", filename, err)
		} else {
			log.Printf("Saved response to: %s", filename)
		}
	}

	doc, err := goquery.NewDocumentFromReader(strings.NewReader(string(body)))
	if err != nil {
		return nil, fmt.Errorf("failed to parse HTML: %w", err)
	}

	metrics := s.extractMetrics(doc, client, verbose)
	
	return metrics, nil
}

// extractMetrics extracts actual metrics from the FIOS G1100 page
func (s *FiosScraper) extractMetrics(doc *goquery.Document, client *http.Client, verbose bool) map[string]interface{} {
	metrics := map[string]interface{}{
		"device": "fios_g1100",
		"name":   s.config.Name,
		"status": "offline",
	}

	// Try to find status information on the page
	doc.Find("body").Each(func(i int, sel *goquery.Selection) {
		text := sel.Text()
		if strings.Contains(strings.ToLower(text), "connected") || 
		   strings.Contains(strings.ToLower(text), "online") {
			metrics["status"] = "online"
		}
	})

	// Look for page title
	title := doc.Find("title").Text()
	metrics["page_title"] = title

	// Extract content text for metrics (common patterns)
	contentText := doc.Text()
	metrics["content_length"] = len(contentText)

	// Common FIOS metrics to look for
	extractedMetrics := map[string]interface{}{}

	// Look for IP addresses in the page
	if ipAddr := findIPAddress(contentText); ipAddr != "" {
		extractedMetrics["ip_address"] = ipAddr
	}

	// Look for uptime information
	if uptime := findUptime(contentText); uptime != "" {
		extractedMetrics["uptime"] = uptime
	}

	// Look for device status
	if status := findStatus(contentText); status != "" {
		extractedMetrics["device_status"] = status
	}

	// Look for signal strength
	if signal := findSignalStrength(contentText); signal != "" {
		extractedMetrics["signal_strength"] = signal
	}

	if len(extractedMetrics) > 0 {
		metrics["extracted_data"] = extractedMetrics
	}

	// Attempt to fetch status from common endpoints
	if verbose {
		log.Printf("Attempting to fetch detailed status from router endpoints")
	}

	statusData := s.fetchStatusEndpoints(client, verbose)
	if statusData != nil {
		metrics["endpoint_data"] = statusData
	}

	return metrics
}

// fetchStatusEndpoints attempts to fetch status from common FIOS endpoints
func (s *FiosScraper) fetchStatusEndpoints(client *http.Client, verbose bool) map[string]interface{} {
	result := make(map[string]interface{})

	// Common FIOS G1100 endpoints
	endpoints := []string{
		"/cgi-bin/status_cgi",
		"/cgi-bin/statusDevice",
		"/admin/status.html",
		"/status",
		"/advanced/status",
	}

	for _, endpoint := range endpoints {
		url := strings.TrimRight(s.config.URL, "/") + endpoint
		if verbose {
			log.Printf("Trying endpoint: %s", url)
		}

		resp, err := client.Get(url)
		if err != nil {
			if verbose {
				log.Printf("Endpoint %s failed: %v", endpoint, err)
			}
			continue
		}

		if resp.StatusCode == http.StatusOK {
			body, _ := io.ReadAll(resp.Body)
			resp.Body.Close()

			if verbose {
				log.Printf("Success! Got response from %s (%d bytes)", endpoint, len(body))
				if len(body) > 500 {
					log.Printf("Response preview: %s...", string(body[:500]))
				} else {
					log.Printf("Response: %s", string(body))
				}
			}

			result[endpoint] = map[string]interface{}{
				"status": resp.Status,
				"size":   len(body),
				"preview": string(body),
			}
		}
		resp.Body.Close()
	}

	if len(result) == 0 && verbose {
		log.Printf("No standard endpoints responded. Router may require authentication.")
	}

	return result
}

// findIPAddress searches for IP addresses in text
func findIPAddress(text string) string {
	// Look for common IP address patterns in text
	lines := strings.Split(text, "\n")
	for _, line := range lines {
		if strings.Contains(line, "192.168") || 
		   strings.Contains(line, "10.0") ||
		   strings.Contains(line, "IP Address") ||
		   strings.Contains(line, "WAN") {
			// Extract potential IP
			parts := strings.Fields(line)
			for _, part := range parts {
				if strings.Count(part, ".") == 3 {
					return part
				}
			}
		}
	}
	return ""
}

// findUptime searches for uptime information
func findUptime(text string) string {
	lines := strings.Split(text, "\n")
	for _, line := range lines {
		if strings.Contains(strings.ToLower(line), "uptime") ||
		   strings.Contains(strings.ToLower(line), "up time") ||
		   (strings.Contains(line, "day") && strings.Contains(line, "hour")) {
			return strings.TrimSpace(line)
		}
	}
	return ""
}

// findStatus searches for device status
func findStatus(text string) string {
	lines := strings.Split(text, "\n")
	for _, line := range lines {
		lower := strings.ToLower(line)
		if (strings.Contains(lower, "status") || strings.Contains(lower, "state")) &&
		   (strings.Contains(lower, "online") || strings.Contains(lower, "connected") ||
		    strings.Contains(lower, "ready") || strings.Contains(lower, "active")) {
			return strings.TrimSpace(line)
		}
	}
	return ""
}

// findSignalStrength searches for signal strength
func findSignalStrength(text string) string {
	lines := strings.Split(text, "\n")
	for _, line := range lines {
		if strings.Contains(strings.ToLower(line), "signal") ||
		   strings.Contains(strings.ToLower(line), "rssi") ||
		   strings.Contains(strings.ToLower(line), "dbm") {
			return strings.TrimSpace(line)
		}
	}
	return ""
}