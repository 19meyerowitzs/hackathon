"""
Logging configuration for Reputation Intelligence App.
"""
import logging
import sys
from typing import Optional

# Configure logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ],
)


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a logger instance.
    
    Args:
        name: Logger name (defaults to "reputation_app")
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name or "reputation_app")


# Create default logger
logger = get_logger()
