"""
Oblivious HTTP (OHTTP / OHAI RFC 9292) relay transport abstraction.
"""

from typing import Optional
import httpx

from muse.core.config import MuseConfig, get_config
from muse.core.logging import setup_logger

logger = setup_logger("muse.privacy.ohttp")


class OHttpRelayTransport:
    """Manages encapsulated OHTTP requests forwarded to Fastly relay gateway."""

    def __init__(self, config: Optional[MuseConfig] = None):
        self.config = config or get_config()
        self.relay_url = self.config.ohttp_relay_url
        self.enabled = self.config.ohttp_enabled

    def encapsulate_and_send(self, target_url: str, payload: bytes) -> httpx.Response:
        """Stub for RFC-9292 encapsulated OHTTP transaction."""
        if not self.enabled:
            raise RuntimeError("OHTTP transport is disabled in configuration.")
        logger.debug(f"Forwarding encapsulated request for {target_url} to relay {self.relay_url}")
        # Placeholder for binary OHTTP envelope transmission
        raise NotImplementedError("Direct OHTTP encapsulation will be loaded via libtrafficnts.")
