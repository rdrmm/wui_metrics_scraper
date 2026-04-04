package main

import (
	"flag"
	"fmt"
	"log"
	"os"
	"time"

	"gopkg.in/yaml.v3"
)

// Config represents the scraper configuration
type Config struct {
	Scrapers []ScraperConfig `yaml:"scrapers"`
}

type ScraperConfig struct {
	Name    string `yaml:"name"`
	Type    string `yaml:"type"`
	URL     string `yaml:"url"`
	Timeout int    `yaml:"timeout"`
	Enabled bool   `yaml:"enabled"`
}

// Scraper interface
type Scraper interface {
	Scrape(verbose bool, saveResponses bool) (map[string]interface{}, error)
}

// ScraperFactory creates scrapers
type ScraperFactory struct{}

func (f *ScraperFactory) Create(config ScraperConfig) Scraper {
	switch config.Type {
	case "fios":
		return &FiosScraper{config: config}
	case "test":
		return &TestScraper{config: config}
	default:
		return nil
	}
}

func main() {
	verbose := flag.Bool("verbose", false, "Enable verbose output with response bodies")
	saveResponses := flag.Bool("save", false, "Save responses to files for inspection")
	demo := flag.Bool("demo", false, "Run with mock FIOS server for testing")
	flag.Parse()

	// Start mock server if demo mode
	if *demo {
		log.Println("DEMO MODE: Starting mock FIOS G1100 server")
		StartMockFiosServer(8888)
		
		// Update config to use localhost mock server
		log.Println("Using mock server at http://127.0.0.1:8888")
		time.Sleep(500 * time.Millisecond) // Give server time to start
	}

	configFile := "config_scrapers.yaml"
	data, err := os.ReadFile(configFile)
	if err != nil {
		log.Fatalf("Failed to read config file: %v", err)
	}

	var config Config
	if err := yaml.Unmarshal(data, &config); err != nil {
		log.Fatalf("Failed to parse config: %v", err)
	}

	factory := &ScraperFactory{}

	for _, scraperCfg := range config.Scrapers {
		if !scraperCfg.Enabled {
			log.Printf("Skipping disabled scraper: %s", scraperCfg.Name)
			continue
		}

		// In demo mode, override the URL
		if *demo {
			scraperCfg.URL = "http://127.0.0.1:8888"
		}

		scraper := factory.Create(scraperCfg)
		if scraper == nil {
			log.Printf("Unknown scraper type: %s", scraperCfg.Type)
			continue
		}

		log.Printf("Scraping: %s", scraperCfg.Name)
		result, err := scraper.Scrape(*verbose, *saveResponses)
		if err != nil {
			log.Printf("Error scraping %s: %v", scraperCfg.Name, err)
			continue
		}
		fmt.Printf("Results for %s: %+v\n", scraperCfg.Name, result)
	}

	log.Println("Scraping complete")
}