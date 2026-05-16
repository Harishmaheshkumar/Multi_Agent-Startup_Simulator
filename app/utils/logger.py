"""
Logging configuration for the Multi-Agent Startup Simulator.
"""

import logging
import logging.handlers
from pathlib import Path
from typing import Optional

from .config import config


def setup_logger(name: str, level: Optional[str] = None) -> logging.Logger:
    """Set up logger with appropriate configuration."""
    logger = logging.getLogger(name)

    if logger.handlers:
        return logger

    # Set log level
    log_level = level or config.log_level
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    # Create formatters
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler
    if config.logs_dir:
        log_file = config.logs_dir / "startup_simulator.log"
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def get_logger(name: str) -> logging.Logger:
    """Get logger instance."""
    return logging.getLogger(name)


class LoggerMixin:
    """Mixin class to add logging to any class."""

    @property
    def logger(self) -> logging.Logger:
        """Get logger for this class."""
        return get_logger(self.__class__.__name__)