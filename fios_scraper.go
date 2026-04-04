package main

import (
	"crypto/tls"
	"fmt"
	"log"
	"net/http"
	"time"

	"github.com/PuerkitoBio/goquery"
)

// FiosScraper scrapes FIOS G1100 router
type FiosScraper struct {
	config ScraperConfig
}

// Scrape implements the Scraper interface
func (s *FiosScraper) Scrape() (map[string]interface{}, error) {
	log.Printf("FIOS scraper starting: %s", s.config.URL)

	client := &http.Client{
		Timeout: time.Duration(s.config.Timeout) * time.Second,
		Transport: &http.Transport{
			TLSClientConfig: &tls.Config{InsecureSkipVerify: true}, // Note: Use proper cert verification in production
		},
	}

	resp, err := client.Get(s.config.URL)
	if err != nil {
		return nil, fmt.Errorf("request error: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("bad status: %s", resp.Status)
	}

	doc, err := goquery.NewDocumentFromReader(resp.Body)
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