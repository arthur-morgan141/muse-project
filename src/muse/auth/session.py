"""
Registration session state persistence and resumption.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

from muse.core.config import MuseConfig, get_config
from muse.core.logging import setup_logger
from muse.core.models import SessionState

logger = setup_logger("muse.auth.session")


class SessionStore:
    """Manages reading and writing in-flight registration sessions with restricted 0600 permissions."""

    def __init__(self, config: Optional[MuseConfig] = None):
        self.config = config or get_config()
        self.cache_path = Path(self.config.session_cache_path)

    def has_session(self) -> bool:
        """Checks if a readable in-flight session exists on disk."""
        return self.cache_path.exists() and self.cache_path.stat().st_size > 0

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
        if not self.has_session():
            return None
        try:
            with open(self.cache_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            logger.debug(f"Session state loaded from {self.cache_path}")
            return SessionState.from_dict(data)
        except Exception as e:
            logger.warning(f"Failed to read session cache from {self.cache_path}: {e}")
            return None

    def get_summary(self) -> Optional[Dict[str, Any]]:
        """Returns a human-readable summary of the in-flight session."""
        state = self.load()
        if not state:
            return None

        last_step = "Onboarding Started (Step 1)"
        if state.completion_handle:
            last_step = "OTP Confirmed / Ready for Profile Registration (Step 4)"
        elif state.auth_state and state.contact_point:
            last_step = f"OTP Dispatched to {state.contact_point} (Step 3)"
        elif state.temp_token:
            last_step = "Temporary Access Token Acquired (Step 1)"

        return {
            "device_id": state.device_id,
            "contact_point": state.contact_point or "None",
            "region": state.region,
            "has_temp_token": bool(state.temp_token),
            "has_completion_handle": bool(state.completion_handle),
            "last_step": last_step,
            "cache_path": str(self.cache_path),
        }

    def clear(self) -> bool:
        """Deletes session cache upon completion or explicit user request."""
        if self.cache_path.exists():
            try:
                self.cache_path.unlink()
                logger.debug(f"Session state cleared at {self.cache_path}")
                return True
            except Exception as e:
                logger.warning(f"Could not remove session cache file: {e}")
                return False
        return False
