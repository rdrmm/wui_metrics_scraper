"""
Configuration loader for scraper definitions
"""
import logging
from pathlib import Path
import yaml

logger = logging.getLogger(__name__)


class ConfigLoader:
    """Load YAML configuration file"""
    
    def __init__(self, config_path):
        self.config_path = Path(config_path)
    
    def load(self):
        """Load and parse YAML config"""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")
        
        try:
            with self.config_path.open() as f:
                config = yaml.safe_load(f)
                logger.info(f"Loaded config from {self.config_path}")
                return config or {}
        except yaml.YAMLError as e:
            logger.error(f"YAML parse error: {e}")
            raise
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            raise