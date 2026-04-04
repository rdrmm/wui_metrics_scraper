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

	// Placeholder: Extract some metrics from the page
	// For FIOS G1100, you might need to login first or scrape specific endpoints
	// This is a basic example; adjust based on actual page structure

	title := doc.Find("title").Text()
	metrics := map[string]interface{}{
		"device":       "fios_g1100",
		"name":         s.config.Name,
		"status":       "online",
		"page_title":   title,
		"response_size": len(doc.Text()),
	}

	return metrics, nil
}