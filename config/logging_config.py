"""
Logging Configuration using Loguru
"""
import sys
from loguru import logger
from pathlib import Path

# Import settings
try:
    from config.settings import LOG_DIR, DEBUG_MODE
except ImportError:
    # Fallback if settings not available
    LOG_DIR = Path("logs")
    DEBUG_MODE = True
    LOG_DIR.mkdir(parents=True, exist_ok=True)


def setup_logging():
    """
    Configure loguru logger with file and console output
    """
    # Remove default handler
    logger.remove()

    # Console handler with color
    log_level = "DEBUG" if DEBUG_MODE else "INFO"
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=log_level,
        colorize=True
    )

    # File handler for all logs
    logger.add(
        LOG_DIR / "app.log",
        rotation="10 MB",
        retention="7 days",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="DEBUG"
    )

    # File handler for errors only
    logger.add(
        LOG_DIR / "errors.log",
        rotation="10 MB",
        retention="30 days",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="ERROR"
    )

    logger.info("Logging configured successfully")
    return logger


# Initialize logging on module import
setup_logging()
