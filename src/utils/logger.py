"""
Centralized logging configuration for the SaaS platform.
"""

import logging
import logging.config
import yaml
import os

def setup_logger(name: str) -> logging.Logger:
    """Set up a logger with YAML configuration.
    
    Args:
        name: Logger name.
    
    Returns:
        logging.Logger: Configured logger instance.
    """
    config_path = os.path.join(os.path.dirname(__file__), "../../configs/logging.yaml")
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
        logging.config.dictConfig(config)
    return logging.getLogger(name)