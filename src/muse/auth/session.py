"""
Registration session state persistence and resumption.
"""

import json
import os
from pathlib import Path
from typing import Optional

from muse.core.config import MuseConfig, get_config
from muse.core.logging import setup_logger
from muse.core.models import SessionState

logger = setup_logger("muse.auth.session")


class SessionStore:
    """Manages reading and writing in-flight registration sessions with restricted 0600 permissions."""

    def __init__(self, config: Optional[MuseConfig] = None):
        self.config = config or get_config()
        self.cache_path = Path(self.config.session_cache_path)

    def save(self, state: SessionState) -> None:
        """Saves session state to disk with owner-only (0600) permissions."""
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC
        mode = 0o600

        fd = os.open(self.cache_path, flags, mode)
        with open(fd, "w", encoding="utf-8") as f:
            json.dump(state.to_dict(), f, indent=2)

        try:
            os.chmod(self.cache_path, 0o600)
        except OSError:
            pass

        logger.debug(f"Session state saved to {self.cache_path} (mode 0600)")

    def load(self) -> Optional[SessionState]:
        """Loads existing session state if file exists."""
        if not self.cache_path.exists():
            return None
        try:
            with open(self.cache_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            logger.debug(f"Session state loaded from {self.cache_path}")
            return SessionState.from_dict(data)
        except Exception as e:
            logger.warning(f"Failed to read session cache from {self.cache_path}: {e}")
            return None

    def clear(self) -> None:
        """Deletes session cache upon successful completion."""
        if self.cache_path.exists():
            try:
                self.cache_path.unlink()
                logger.debug(f"Session state cleared at {self.cache_path}")
            except Exception as e:
                logger.warning(f"Could not remove session cache file: {e}")
