# log_module.py
import logging
import os
from logging.handlers import RotatingFileHandler

def setup_logger(name: str = None):
    """
    Central logging setup.
    Usage in modules:
        logger = setup_logger(__name__)
    """

    # Create logs folder if not exists
    os.makedirs("logs", exist_ok=True)

    # Logging format
    log_format = (
        "%(asctime)s | %(levelname)s | %(name)s | "
        "%(filename)s:%(lineno)d | %(message)s"
    )

    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # Avoid duplicate handlers if logger is created multiple times
    if logger.hasHandlers():
        logger.handlers.clear()

    formatter = logging.Formatter(log_format)

    # ---- Console Handler ----
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    # ---- File Handler (Rotating) ----
    file_handler = RotatingFileHandler(
        "logs/app.log",
        maxBytes=5_000_000,   # 5 MB per file
        backupCount=3         # keep 3 backups
    )
    file_handler.setFormatter(formatter)

    # Add handlers
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger
