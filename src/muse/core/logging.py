"""
Logging configuration for Muse Client.
"""

import logging
import os
import sys
from typing import Optional


def setup_logger(
    name: str = "muse",
    level: Optional[str] = None,
    log_format: Optional[str] = None,
) -> logging.Logger:
    """Configures and returns a hierarchical logger."""
    env_level = os.getenv("MUSE_LOG_LEVEL", "INFO").upper()
    effective_level = (level or env_level).upper()

    default_format = "[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s"
    formatter = logging.Formatter(
        log_format or default_format,
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, effective_level, logging.INFO))

    # Avoid duplicate handlers on re-initialization
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger
