"""
Domain data models and schemas for Meta Muse.
"""

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, Optional


@dataclass
class SessionState:
    device_id: str
    waterfall_id: str
    temp_token: Optional[str] = None
    key_id: Optional[int] = None
    public_key: Optional[str] = None
    tos_ver: Optional[str] = None
    contact_point: Optional[str] = None
    region: str = "US"
    auth_state: Optional[str] = None
    completion_handle: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SessionState":
        return cls(
            device_id=data.get("device_id", ""),
            waterfall_id=data.get("waterfall_id", ""),
            temp_token=data.get("temp_token"),
            key_id=data.get("key_id"),
            public_key=data.get("public_key"),
            tos_ver=data.get("tos_ver"),
            contact_point=data.get("contact_point"),
            region=data.get("region", "US"),
            auth_state=data.get("auth_state"),
            completion_handle=data.get("completion_handle"),
            metadata=data.get("metadata", {}),
        )


@dataclass
class UserProfile:
    first_name: str
    last_name: str
    date_of_birth: str  # YYYY-MM-DD
    password: str
    region: str = "US"


@dataclass
class AuthTokens:
    abra_access_token: str
    abra_user_id: Optional[str] = None
    frl_account_id: Optional[str] = None
    token_type: str = "Bearer"
    raw_response: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AuthTokens":
        return cls(
            abra_access_token=data.get("abra_access_token", ""),
            abra_user_id=data.get("abra_user_id"),
            frl_account_id=data.get("frl_account_id"),
            token_type=data.get("token_type", "Bearer"),
            raw_response=data.get("raw_response", data),
        )


@dataclass
class ActivationStatus:
    waitlist_status: str
    has_hatch_access: bool
    has_redeemed_invite_code: bool
    raw_response: Dict[str, Any] = field(default_factory=dict)
