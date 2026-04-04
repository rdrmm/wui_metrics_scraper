"""
Factory pattern for creating scraper instances
"""
import logging
from scrapers.netgear_scraper import NetgearScraper
from scrapers.asus_scraper import AsusScraper

logger = logging.getLogger(__name__)

# Registry mapping scraper types to classes
SCRAPER_REGISTRY = {
    'netgear': NetgearScraper,
    'asus': AsusScraper,
}


class ScraperFactory:
    """Factory for creating scraper instances"""
    
    @staticmethod
    def create(config):
        """Create a scraper based on config type"""
        scraper_type = config.get('type', '').lower()
        scraper_class = SCRAPER_REGISTRY.get(scraper_type)
        
        if not scraper_class:
            logger.warning(f"Unknown scraper type: {scraper_type}")
            return None
        
        try:
            return scraper_class(config)
        except Exception as e:
            logger.error(f"Error creating scraper: {e}", exc_info=True)
            return None
    
    @staticmethod
    def register(scraper_type, scraper_class):
        """Register a new scraper type"""
        SCRAPER_REGISTRY[scraper_type.lower()] = scraper_class
        logger.info(f"Registered scraper: {scraper_type}")