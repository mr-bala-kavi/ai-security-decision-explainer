"""
Logger Utilities

Provides easy access to configured logger throughout the application.
"""
from loguru import logger
from config.logging_config import setup_logging

# Ensure logging is configured
setup_logging()

# Export logger for convenience
__all__ = ['logger']
