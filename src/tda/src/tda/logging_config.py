"""Logging configuration for Technical Debt Agent."""

import logging
import os
import tempfile
from logging.handlers import RotatingFileHandler


def setup_logging() -> str:
    """Configure logging with file and console handlers.

    Returns:
        Path to the log file
    """
    log_level = os.getenv("TDA_LOG_LEVEL", "INFO")
    log_dir = tempfile.gettempdir()
    log_file = os.path.join(log_dir, "tda.log")

    # Clear any existing handlers
    logging.root.handlers.clear()

    # Create handlers
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=5 * 1024 * 1024,  # 5 MB
        backupCount=3
    )
    console_handler = logging.StreamHandler()

    # Set format
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(logging.Formatter('%(levelname)s - %(name)s - %(message)s'))

    # Set level on handlers
    file_handler.setLevel(logging.DEBUG)  # Log everything to file
    console_handler.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    # Configure root logger
    logging.root.setLevel(logging.DEBUG)  # Capture all levels
    logging.root.addHandler(file_handler)
    logging.root.addHandler(console_handler)

    return log_file
