"""
Persistent credential and token storage for registered Muse accounts.
"""

import json
from pathlib import Path
from typing import Optional

from muse.core.config import MuseConfig, get_config
from muse.core.logging import setup_logger
from muse.core.models import AuthTokens

logger = setup_logger("muse.auth.tokens")


class TokenStore:
    """Manages persistent storage of abra access tokens."""

    def __init__(self, config: Optional[MuseConfig] = None):
        self.config = config or get_config()
        self.cred_path = Path(self.config.credentials_path)

    def save(self, tokens: AuthTokens) -> None:
        """Saves authentication tokens to disk."""
        self.cred_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.cred_path, "w", encoding="utf-8") as f:
            json.dump(tokens.to_dict(), f, indent=2)
        logger.info(f"Credentials successfully saved to {self.cred_path}")

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
