"""
Termux Android integration module.
"""

from muse.termux.helper import (
    acquire_wake_lock,
    get_clipboard_otp,
    has_termux_api,
    is_termux,
    release_wake_lock,
    send_notification,
    vibrate,
)

__all__ = [
    "is_termux",
    "has_termux_api",
    "acquire_wake_lock",
    "release_wake_lock",
    "get_clipboard_otp",
    "send_notification",
    "vibrate",
]
