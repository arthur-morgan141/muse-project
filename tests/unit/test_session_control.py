"""
Unit tests for SessionStore and session management controls.
"""

import tempfile
from pathlib import Path

from muse.auth.client import MuseAuthClient
from muse.auth.session import SessionStore
from muse.core.config import MuseConfig
from muse.core.models import SessionState


def test_session_summary_and_has_session():
    with tempfile.TemporaryDirectory() as tmpdir:
        cache_file = Path(tmpdir) / "session_cache.json"
        cfg = MuseConfig({"storage": {"session_cache_path": str(cache_file)}})
        store = SessionStore(cfg)

        assert store.has_session() is False
        assert store.get_summary() is None

        state = SessionState(
            device_id="dev-uuid-12345",
            waterfall_id="wat-uuid-67890",
            contact_point="user@example.com",
            temp_token="temp_tok_abc",
        )
        store.save(state)

        assert store.has_session() is True
        summary = store.get_summary()
        assert summary is not None
        assert summary["contact_point"] == "user@example.com"
        assert summary["device_id"] == "dev-uuid-12345"
        assert summary["has_temp_token"] is True

        cleared = store.clear()
        assert cleared is True
        assert store.has_session() is False


def test_initialize_session_force_new_vs_resume():
    with tempfile.TemporaryDirectory() as tmpdir:
        cache_file = Path(tmpdir) / "session_cache.json"
        cfg = MuseConfig({
            "storage": {"session_cache_path": str(cache_file)},
            "auth": {"auto_resume_session": False},
        })
        store = SessionStore(cfg)

        # Pre-seed session
        initial_state = SessionState(
            device_id="old-device-id",
            waterfall_id="old-waterfall-id",
            contact_point="old@example.com",
        )
        store.save(initial_state)

        client = MuseAuthClient(config=cfg, session_store=store)

        # 1. Default without auto_resume -> should create a new session
        new_state = client.initialize_session()
        assert new_state.device_id != "old-device-id"

        # 2. Explicit resume -> should load old session
        resumed_state = client.initialize_session(resume=True)
        assert resumed_state.device_id == "old-device-id"
        assert resumed_state.contact_point == "old@example.com"

        # 3. Explicit force_new -> should clear cache and create new session
        fresh_state = client.initialize_session(force_new=True)
        assert fresh_state.device_id != "old-device-id"
        assert store.has_session() is False
