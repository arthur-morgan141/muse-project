"""
Unit tests for configuration loading and environment overrides.
"""

import os
from muse.core.config import load_config


def test_load_config_defaults():
    cfg = load_config(env="development")
    assert cfg.env == "development"
    assert cfg.api_base_url == "https://hatch-api.meta.ai"
    assert cfg.default_region == "US"
    assert cfg.api_timeout > 0


def test_load_config_env_override(monkeypatch):
    monkeypatch.setenv("MUSE_API_BASE_URL", "https://custom.endpoint.internal")
    monkeypatch.setenv("MUSE_DEFAULT_REGION", "ID")

    cfg = load_config(env="development")
    assert cfg.api_base_url == "https://custom.endpoint.internal"
    assert cfg.default_region == "ID"
