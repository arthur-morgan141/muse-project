"""
Persistent credential and token storage for registered Muse accounts.
"""

import json
import os
from pathlib import Path
from typing import Optional

from muse.core.config import MuseConfig, get_config
from muse.core.logging import setup_logger
from muse.core.models import AuthTokens

logger = setup_logger("muse.auth.tokens")


class TokenStore:
    """Manages persistent storage of abra access tokens with restricted 0600 permissions."""

    def __init__(self, config: Optional[MuseConfig] = None):
        self.config = config or get_config()
        self.cred_path = Path(self.config.credentials_path)

    def save(self, tokens: AuthTokens) -> None:
        """Saves authentication tokens to disk with owner-only (0600) permissions."""
        self.cred_path.parent.mkdir(parents=True, exist_ok=True)
        flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC
        mode = 0o600

        fd = os.open(self.cred_path, flags, mode)
        with open(fd, "w", encoding="utf-8") as f:
            json.dump(tokens.to_dict(), f, indent=2)

        # Enforce chmod 600 if file already existed previously with broader permissions
        try:
            os.chmod(self.cred_path, 0o600)
        except OSError:
            pass

        logger.info(f"Credentials successfully saved to {self.cred_path} (mode 0600)")

    def load(self) -> Optional[AuthTokens]:
        """Loads credentials from disk if present."""
        if not self.cred_path.exists():
            return None
        try:
            with open(self.cred_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return AuthTokens.from_dict(data)
        except Exception as e:
            logger.error(f"Failed to read credentials from {self.cred_path}: {e}")
            return None
