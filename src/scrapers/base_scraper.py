"""
Abstract base class for all scrapers
"""
from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)


class BaseScraper(ABC):
    """Base class for device-specific scrapers"""
    
    def __init__(self, config):
        """Initialize scraper with configuration"""
        self.config = config
        self.name = config.get('name', 'unknown')
        self.url = config.get('url')
        self.timeout = config.get('timeout', 10)
    
    @abstractmethod
    def scrape(self):
        """Scrape metrics from device - must be implemented by subclass"""
        pass