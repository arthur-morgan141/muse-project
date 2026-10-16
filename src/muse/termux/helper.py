"""
Termux Android hardware & system integration helper.
Supports Termux:API features (clipboard OTP detection, notifications, wake lock, haptics)
with graceful degradation on non-Termux systems.
"""

import os
import re
import shutil
import subprocess
from typing import Optional

from muse.core.logging import setup_logger

logger = setup_logger("muse.termux")


def is_termux() -> bool:
    """Detects whether running inside Termux on Android."""
    prefix = os.environ.get("PREFIX", "")
    if "com.termux" in prefix:
        return True
    return os.path.exists("/data/data/com.termux")


def has_termux_api() -> bool:
    """Checks if termux-api CLI commands are installed in PATH."""
    return is_termux() and shutil.which("termux-notification") is not None


def acquire_wake_lock() -> bool:
    """Acquires Termux wake lock to prevent process suspension by Android Doze."""
    if not is_termux() or not shutil.which("termux-wake-lock"):
        return False
    try:
        subprocess.run(["termux-wake-lock"], check=True, capture_output=True)
        logger.debug("Termux wake-lock acquired")
        return True
    except Exception as e:
        logger.debug(f"Failed to acquire wake-lock: {e}")
        return False


def release_wake_lock() -> bool:
    """Releases Termux wake lock."""
    if not is_termux() or not shutil.which("termux-wake-unlock"):
        return False
    try:
        subprocess.run(["termux-wake-unlock"], check=True, capture_output=True)
        logger.debug("Termux wake-lock released")
        return True
    except Exception as e:
        logger.debug(f"Failed to release wake-lock: {e}")
        return False


def get_clipboard_otp() -> Optional[str]:
    """
    Extracts a 6-digit verification code from Android clipboard via termux-clipboard-get.
    Returns the 6-digit string or None.
    """
    if not is_termux() or not shutil.which("termux-clipboard-get"):
        return None
    try:
        res = subprocess.run(
            ["termux-clipboard-get"],
            capture_output=True,
            text=True,
            timeout=2.0,
            check=True,
        )
        content = res.stdout.strip()
        match = re.search(r"\b\d{6}\b", content)
        if match:
            return match.group(0)
    except Exception as e:
        logger.debug(f"Failed to read clipboard OTP: {e}")
    return None


def send_notification(title: str, content: str) -> bool:
    """Displays an Android status bar notification via termux-notification."""
    if not is_termux() or not shutil.which("termux-notification"):
        return False
    try:
        subprocess.run(
            [
                "termux-notification",
                "--title",
                title,
                "--content",
                content,
                "--priority",
                "high",
            ],
            capture_output=True,
            timeout=2.0,
            check=True,
        )
        return True
    except Exception as e:
        logger.debug(f"Failed to send Termux notification: {e}")
        return False


def vibrate(duration_ms: int = 150) -> bool:
    """Triggers Android haptic feedback vibration via termux-vibrate."""
    if not is_termux() or not shutil.which("termux-vibrate"):
        return False
    try:
        subprocess.run(
            ["termux-vibrate", "-d", str(duration_ms)],
            capture_output=True,
            timeout=2.0,
            check=True,
        )
        return True
    except Exception as e:
        logger.debug(f"Failed to trigger vibration: {e}")
        return False
