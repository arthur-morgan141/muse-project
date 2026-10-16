"""
Exception taxonomy for Meta Muse API and Runtime.
"""

from typing import Any, Dict, Optional


class MuseError(Exception):
    """Base exception for all Muse client errors."""
    pass


class ConfigurationError(MuseError):
    """Raised when configuration is invalid or missing."""
    pass


class CryptographyError(MuseError):
    """Raised when password encryption or key derivation fails."""
    pass


class NetworkError(MuseError):
    """Raised on connection timeout or transport failures."""
    pass


class MuseApiError(MuseError):
    """
    Standard RFC-7807 Problem Details representation for Hatch API errors.
    """
    def __init__(
        self,
        status_code: int,
        title: str = "API Error",
        detail: str = "",
        error_type: str = "about:blank",
        error_code: str = "",
        raw_data: Optional[Dict[str, Any]] = None,
    ):
        self.status_code = status_code
        self.title = title
        self.detail = detail
        self.error_type = error_type
        self.error_code = error_code
        self.raw_data = raw_data or {}
        super().__init__(self.__str__())

    def __str__(self) -> str:
        code_str = f" [{self.error_code}]" if self.error_code else ""
        return f"{self.title}{code_str} (HTTP {self.status_code}): {self.detail}"


class OtpVerificationError(MuseApiError):
    """Raised when OTP code verification fails."""
    pass


class WaitlistBlockedError(MuseApiError):
    """Raised when account is locked behind waitlist gate."""
    pass


class InvalidInviteCodeError(MuseApiError):
    """Raised when invite code is rejected."""
    pass
