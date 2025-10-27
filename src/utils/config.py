"""
Configuration management for the SaaS platform.
"""

import yaml
import os
from typing import Dict, Any

class Config:
    """Loads and manages application configuration."""
    
    def __init__(self, config_path: str = "configs/config.yaml"):
        """Initialize with configuration file.
        
        Args:
            config_path: Path to YAML config file.
        """
        self.config_path = os.path.join(os.path.dirname(__file__), "../../", config_path)
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file.
        
        Returns:
            Dict[str, Any]: Configuration dictionary.
        """
        try:
            with open(self.config_path, "r") as f:
                return yaml.safe_load(f)
        except Exception as e:
            raise RuntimeError(f"Failed to load config: {str(e)}")

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key.
        
        Args:
            key: Configuration key.
            default: Default value if key is not found.
        
        Returns:
            Any: Configuration value.
        """
        return self.config.get(key, default)