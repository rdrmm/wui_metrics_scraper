#!/usr/bin/env python3
"""
WUI Metrics Scraper - Main entry point
"""
import sys
import logging
from pathlib import Path

from config_loader import ConfigLoader
from scraper_factory import ScraperFactory

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("wui_metrics_scraper")


def main():
    """Main function to orchestrate scraping"""
    config_path = Path(__file__).parent.parent / 'config' / 'scrapers.yaml'
    
    if not config_path.exists():
        logger.error(f"Config file not found: {config_path}")
        return 1

    try:
        loader = ConfigLoader(config_path)
        config = loader.load()
        
        for scraper_cfg in config.get('scrapers', []):
            if not scraper_cfg.get('enabled', True):
                logger.debug(f"Skipping disabled scraper: {scraper_cfg.get('name')}")
                continue
            
            scraper = ScraperFactory.create(scraper_cfg)
            if not scraper:
                logger.warning(f"Could not create scraper for type: {scraper_cfg.get('type')}")
                continue
            
            logger.info(f"Scraping: {scraper_cfg.get('name')}")
            try:
                result = scraper.scrape()
                logger.info(f"Results for {scraper_cfg.get('name')}: {result}")
            except Exception as e:
                logger.error(f"Error scraping {scraper_cfg.get('name')}: {e}", exc_info=True)
        
        logger.info("Scraping complete")
        return 0
        
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())