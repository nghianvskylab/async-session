import logging
import os
from pathlib import Path
from logging.handlers import RotatingFileHandler


def setup_logging():
    """Setup logging configuration to write to logs/.log file."""
    # Create logs directory if it doesn't exist
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    # Log file path
    log_file = logs_dir / ".log"
    
    # Configure root logger - only log errors
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.ERROR)
    
    # Remove existing handlers to avoid duplicates
    root_logger.handlers = []
    
    # File handler with rotation (max 10MB, keep 5 backup files)
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding="utf-8",
    )
    file_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler.setFormatter(file_formatter)
    file_handler.setLevel(logging.ERROR)  # Only log errors
    
    # Console handler - only show errors
    console_handler = logging.StreamHandler()
    console_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    console_handler.setFormatter(console_formatter)
    console_handler.setLevel(logging.ERROR)  # Only log errors
    
    # Add handlers to root logger
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the given name."""
    # Setup logging if not already configured
    root_logger = logging.getLogger()
    if not root_logger.handlers:
        setup_logging()
    
    return logging.getLogger(name)

