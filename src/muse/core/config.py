"""
Hierarchical configuration loader supporting YAML files and environment variable overrides.
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml


def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively merges override dictionary into base dictionary."""
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


class MuseConfig:
    """Application configuration holder for registration & invite redemption."""

    def __init__(self, raw_data: Dict[str, Any]):
        self._data = raw_data

        # Top level sections
        self.env = raw_data.get("environment", os.getenv("MUSE_ENV", "development"))

        api_section = raw_data.get("api", {})
        self.api_base_url = os.getenv("MUSE_API_BASE_URL", api_section.get("base_url", "https://hatch-api.meta.ai"))
        self.api_timeout = float(os.getenv("MUSE_API_TIMEOUT", api_section.get("timeout", 30.0)))
        self.api_version = os.getenv("MUSE_API_VERSION", api_section.get("version", "1.0.0"))
        self.user_agent = api_section.get(
            "user_agent", "com.facebook.aura/11.0.0.18.164 (Android 14; Mobile; en_US)"
        )
        self.headers = api_section.get("headers", {})

        auth_section = raw_data.get("auth", {})
        self.default_region = os.getenv("MUSE_DEFAULT_REGION", auth_section.get("default_region", "US"))
        self.default_key_id = int(auth_section.get("default_key_id", 41))
        self.auto_resume_session = os.getenv(
            "MUSE_AUTO_RESUME_SESSION", str(auth_section.get("auto_resume_session", False))
        ).lower() in ("true", "1", "yes")

        storage_section = raw_data.get("storage", {})
        self.session_cache_path = Path(
            os.getenv("MUSE_SESSION_CACHE_FILE", storage_section.get("session_cache_path", "data/sessions/session_cache.json"))
        )
        self.credentials_path = Path(
            os.getenv("MUSE_CREDENTIALS_FILE", storage_section.get("credentials_path", "data/sessions/credentials.json"))
        )

        log_section = raw_data.get("logging", {})
        self.log_level = os.getenv("MUSE_LOG_LEVEL", log_section.get("level", "INFO"))
        self.log_format = log_section.get("format")

    def as_dict(self) -> Dict[str, Any]:
        return self._data


_GLOBAL_CONFIG: Optional[MuseConfig] = None


def load_config(
    env: Optional[str] = None,
    config_dir: Optional[Path] = None,
) -> MuseConfig:
    """Loads and merges configuration based on current environment."""
    target_env = env or os.getenv("MUSE_ENV", "development").lower()

    if config_dir is None:
        # Default relative to package or root
        candidates = [
            Path.cwd() / "config",
            Path(__file__).resolve().parent.parent.parent.parent / "config",
        ]
        for c in candidates:
            if c.is_dir():
                config_dir = c
                break

    base_config: Dict[str, Any] = {}
    env_config: Dict[str, Any] = {}

    if config_dir and config_dir.is_dir():
        base_path = config_dir / "config.base.yaml"
        if base_path.exists():
            with open(base_path, "r", encoding="utf-8") as f:
                base_config = yaml.safe_load(f) or {}

        env_path = config_dir / f"config.{target_env}.yaml"
        if env_path.exists():
            with open(env_path, "r", encoding="utf-8") as f:
                env_config = yaml.safe_load(f) or {}

    merged = _deep_merge(base_config, env_config)
    merged["environment"] = target_env

    return MuseConfig(merged)


def get_config(force_reload: bool = False) -> MuseConfig:
    """Singleton getter for application configuration."""
    global _GLOBAL_CONFIG
    if _GLOBAL_CONFIG is None or force_reload:
        _GLOBAL_CONFIG = load_config()
    return _GLOBAL_CONFIG
