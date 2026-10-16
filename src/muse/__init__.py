"""
Meta Muse Client & Agentic Framework (com.facebook.aura)
Reverse-engineered architecture for Direct API communication and MCP integrations.
"""

from muse.__version__ import __version__
from muse.core.config import get_config
from muse.auth.client import MuseAuthClient
from muse.crypto.meta_cipher import encrypt_meta_password

__all__ = [
    "__version__",
    "get_config",
    "MuseAuthClient",
    "encrypt_meta_password",
]
