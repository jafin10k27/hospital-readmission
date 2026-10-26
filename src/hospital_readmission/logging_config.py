"""Centralized logging configuration for Hospital Readmission Intelligence Platform."""

import logging
import sys
from pathlib import Path


def setup_logger(
    name: str = "hospital_readmission",
    log_level: str | int = "INFO",
    log_dir: str | Path | None = "logs",
    log_filename: str = "platform.log",
) -> logging.Logger:
    """Configures and returns a structured logger.

    Args:
        name: Name of the logger.
        log_level: Logging level (e.g. 'DEBUG', 'INFO', 'WARNING').
        log_dir: Directory where log file will be saved. None to disable file logging.
        log_filename: Filename for the log file.

    Returns:
        Configured logging.Logger instance.
    """
    logger = logging.getLogger(name)

    if isinstance(log_level, str):
        level = getattr(logging, log_level.upper(), logging.INFO)
    else:
        level = log_level

    logger.setLevel(level)

    # Avoid duplicate handlers if setup_logger is called repeatedly
    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] [%(name)s:%(funcName)s:%(lineno)d] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(level)
    logger.addHandler(console_handler)

    # File Handler
    if log_dir is not None:
        try:
            log_path = Path(log_dir)
            log_path.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_path / log_filename, encoding="utf-8")
            file_handler.setFormatter(formatter)
            file_handler.setLevel(level)
            logger.addHandler(file_handler)
        except Exception as e:
            logger.warning("Could not set up file logging at %s: %s", log_dir, e)

    return logger
