"""
Unit tests for Termux Android integration and fallback behaviors.
"""

from muse.termux.helper import (
    acquire_wake_lock,
    get_clipboard_otp,
    is_termux,
    release_wake_lock,
    send_notification,
    vibrate,
)


def test_is_termux_environment(monkeypatch):
    # Standard desktop / linux container without Termux
    monkeypatch.delenv("PREFIX", raising=False)
    # Check that it returns boolean without error
    val = is_termux()
    assert isinstance(val, bool)

    # Simulated Termux environment
    monkeypatch.setenv("PREFIX", "/data/data/com.termux/files/usr")
    assert is_termux() is True


def test_termux_graceful_fallbacks_on_desktop(monkeypatch):
    # Ensure commands that are not in PATH return False and do not crash
    monkeypatch.delenv("PREFIX", raising=False)
    assert acquire_wake_lock() is False
    assert release_wake_lock() is False
    assert send_notification("Test", "Body") is False
    assert vibrate(100) is False
    assert get_clipboard_otp() is None
