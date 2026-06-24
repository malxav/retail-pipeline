"""
Centralized logging utility for the ETL pipeline.

This module provides a unified logger configuration that outputs to both the 
console and a persistent file, standardizing error tracking across the project.
"""

import logging
from pathlib import Path
from config import LOG_DIR


def get_logger(name: str) -> logging.Logger:
    """
    Returns a configured logger that writes to both the terminal
    and a persistent log file. Call this at the top of every module:

        from utils.logger import get_logger
        logger = get_logger(__name__)

    Uses __name__ means the log entry shows exactly which module used it.
    """
    logger = logging.getLogger(name)

    # Guard against adding duplicate handlers if this function
    # is called multiple times (e.g. during testing)
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter(
        fmt='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # File handler — DEBUG and above, persists across runs
    log_file = LOG_DIR / 'pipeline.log'
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    # Console handler — INFO and above (don't flood terminal with DEBUG)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger