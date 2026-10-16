"""
Unit tests for TokenStore and SessionStore file security.
"""

import os
import stat
import tempfile
from pathlib import Path

from muse.auth.session import SessionStore
from muse.auth.token_store import TokenStore
from muse.core.config import MuseConfig
from muse.core.models import AuthTokens, SessionState


def test_token_store_file_permissions():
    with tempfile.TemporaryDirectory() as tmpdir:
        cred_file = Path(tmpdir) / "credentials.json"
        cfg = MuseConfig({"storage": {"credentials_path": str(cred_file)}})

        store = TokenStore(cfg)
        tokens = AuthTokens(abra_access_token="test_token_123")
        store.save(tokens)

        assert cred_file.exists()
        file_mode = stat.S_IMODE(os.stat(cred_file).st_mode)
        # Verify 0o600 (owner read/write only)
        assert file_mode == 0o600

        loaded = store.load()
        assert loaded is not None
        assert loaded.abra_access_token == "test_token_123"


def test_session_store_file_permissions():
    with tempfile.TemporaryDirectory() as tmpdir:
        cache_file = Path(tmpdir) / "session_cache.json"
        cfg = MuseConfig({"storage": {"session_cache_path": str(cache_file)}})

        store = SessionStore(cfg)
        state = SessionState(device_id="dev-1", waterfall_id="wat-1")
        store.save(state)

        assert cache_file.exists()
        file_mode = stat.S_IMODE(os.stat(cache_file).st_mode)
        assert file_mode == 0o600

        loaded = store.load()
        assert loaded is not None
        assert loaded.device_id == "dev-1"
