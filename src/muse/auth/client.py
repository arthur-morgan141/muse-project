"""
Authentication and registration workflow client for Meta Muse.
"""

import uuid
from typing import Any, Dict, Optional, cast

from muse.api.client import MuseApiClient
from muse.api.endpoints import HatchEndpoints
from muse.auth.session import SessionStore
from muse.auth.token_store import TokenStore
from muse.core.config import MuseConfig, get_config
from muse.core.exceptions import MuseApiError, OtpVerificationError
from muse.core.logging import setup_logger
from muse.core.models import ActivationStatus, AuthTokens, SessionState, UserProfile
from muse.crypto.meta_cipher import encrypt_meta_password

logger = setup_logger("muse.auth")


class MuseAuthClient:
    """High-level client orchestrating registration and authentication steps."""

    def __init__(
        self,
        config: Optional[MuseConfig] = None,
        api_client: Optional[MuseApiClient] = None,
        session_store: Optional[SessionStore] = None,
        token_store: Optional[TokenStore] = None,
    ):
        self.config = config or get_config()
        self.api = api_client or MuseApiClient(self.config)
        self.session_store = session_store or SessionStore(self.config)
        self.token_store = token_store or TokenStore(self.config)
        self.state: Optional[SessionState] = None

    def initialize_session(self, force_new: bool = False, resume: bool = False) -> SessionState:
        """Loads an existing in-flight session or creates a new one."""
        if force_new:
            self.session_store.clear()
            self.state = SessionState(
                device_id=str(uuid.uuid4()),
                waterfall_id=str(uuid.uuid4()),
                region=self.config.default_region,
            )
            return self.state

        if resume or self.config.auto_resume_session:
            existing = self.session_store.load()
            if existing:
                logger.info(f"Resuming existing session: Device {existing.device_id[:8]}...")
                self.state = existing
                if existing.temp_token:
                    self.api.set_auth_token(existing.temp_token)
                return self.state

        self.state = SessionState(
            device_id=str(uuid.uuid4()),
            waterfall_id=str(uuid.uuid4()),
            region=self.config.default_region,
        )
        return self.state

    def _get_active_state(self) -> SessionState:
        """Ensures an active session state exists."""
        if self.state is None:
            return self.initialize_session()
        return self.state

    def start_onboarding(self) -> Dict[str, Any]:
        """
        Step 1: Initiate onboarding flow (/hatch/auth/start).
        Retrieves temporary token, ToS content version, and server encryption public key.
        """
        state = self._get_active_state()

        payload = {
            "device_id": state.device_id,
            "waterfall_id": state.waterfall_id,
        }
        resp = self.api.post(HatchEndpoints.AUTH_START, json=payload)
        data = cast(Dict[str, Any], resp.json())

        state.temp_token = data.get("access_token")
        if state.temp_token:
            self.api.set_auth_token(state.temp_token)

        state.tos_ver = data.get("tos", {}).get("content_version")
        enc_info = data.get("password_encryption_key", {})
        state.key_id = enc_info.get("key_id", self.config.default_key_id)
        state.public_key = enc_info.get("public_key")

        self.session_store.save(state)
        logger.info("Onboarding initialized. Temporary token acquired.")
        return data

    def check_login_options(self, contact_point: str, region: Optional[str] = None) -> Dict[str, Any]:
        """
        Step 2: Evaluate login & registration options (/hatch/auth/login_options).
        """
        state = self._get_active_state()

        state.contact_point = contact_point
        state.region = region or state.region

        payload = {
            "contact_point": contact_point,
            "region": state.region,
            "device_id": state.device_id,
            "waterfall_id": state.waterfall_id,
        }
        resp = self.api.post(HatchEndpoints.AUTH_LOGIN_OPTIONS, json=payload)
        data = cast(Dict[str, Any], resp.json())

        state.auth_state = data.get("auth_state")
        self.session_store.save(state)
        return data

    def send_otp(self, contact_point: Optional[str] = None) -> Dict[str, Any]:
        """
        Step 3: Dispatch OTP code to email or phone (/hatch/auth/send_otp).
        """
        if self.state is None:
            raise MuseApiError(400, "Session Error", "Session not initialized")

        state = self.state
        target_contact = contact_point or state.contact_point
        if not target_contact:
            raise MuseApiError(400, "Validation Error", "Contact point required")

        payload: Dict[str, Any] = {
            "contact_point": target_contact,
            "channel": "EMAIL" if "@" in target_contact else "SMS",
            "region": state.region,
            "device_id": state.device_id,
            "waterfall_id": state.waterfall_id,
        }
        if state.auth_state:
            payload["auth_state"] = state.auth_state

        resp = self.api.post(HatchEndpoints.AUTH_SEND_OTP, json=payload)
        data = cast(Dict[str, Any], resp.json())

        state.auth_state = data.get("auth_state", state.auth_state)
        self.session_store.save(state)
        logger.info(f"OTP successfully dispatched to {target_contact}")
        return data

    def confirm_otp(self, otp_code: str) -> str:
        """
        Step 4: Confirm OTP verification code (/hatch/auth/confirm_otp).
        Returns: completion_handle (one-time authorization token for registration).
        """
        if self.state is None:
            raise MuseApiError(400, "Session Error", "Session not initialized")

        state = self.state
        payload: Dict[str, Any] = {
            "otp_code": otp_code,
            "supports_account_selection": True,
            "device_id": state.device_id,
            "waterfall_id": state.waterfall_id,
        }
        if state.auth_state:
            payload["auth_state"] = state.auth_state

        try:
            resp = self.api.post(HatchEndpoints.AUTH_CONFIRM_OTP, json=payload)
            data = cast(Dict[str, Any], resp.json())
        except MuseApiError as e:
            raise OtpVerificationError(e.status_code, e.title, e.detail, e.error_type, e.error_code) from e

        handle = cast(Optional[str], data.get("completion_handle"))
        if not handle:
            raise OtpVerificationError(resp.status_code, "Invalid Response", "No completion_handle in response")

        state.completion_handle = handle
        state.tos_ver = data.get("tos", {}).get("content_version", state.tos_ver)
        self.session_store.save(state)
        logger.info("OTP confirmed successfully. Completion handle acquired.")
        return handle

    def complete_registration(self, profile: UserProfile) -> AuthTokens:
        """
        Step 5: Finalize account registration (/hatch/auth/register_completion).
        Encrypts password natively using Meta EVP_SealInit and stores permanent tokens.
        """
        if not self.state or not self.state.completion_handle:
            raise MuseApiError(400, "Session Error", "No completion handle found; verify OTP first")

        state = self.state
        enc_password = encrypt_meta_password(
            password=profile.password,
            server_key_id=state.key_id,
            server_pubkey=state.public_key,
        )

        payload = {
            "completion_handle": state.completion_handle,
            "contact_point": state.contact_point,
            "first_name": profile.first_name,
            "last_name": profile.last_name,
            "password": enc_password,
            "date_of_birth": profile.date_of_birth,
            "region": profile.region or state.region,
            "tos_content_version": state.tos_ver,
            "device_id": state.device_id,
            "waterfall_id": state.waterfall_id,
        }

        resp = self.api.post(HatchEndpoints.AUTH_REGISTER_COMPLETION, json=payload)
        data = cast(Dict[str, Any], resp.json())

        tokens = AuthTokens.from_dict(data)
        self.token_store.save(tokens)
        self.api.set_auth_token(tokens.abra_access_token)

        # Clear session cache once account is created
        self.session_store.clear()
        logger.info(f"Account successfully registered! User ID: {tokens.abra_user_id}")
        return tokens

    def check_activation_status(self) -> ActivationStatus:
        """
        Step 6: Check gatekeeper / waitlist status (/hatch/activation_statuses).
        """
        resp = self.api.get(HatchEndpoints.ACTIVATION_STATUSES)
        data = cast(Dict[str, Any], resp.json())
        return ActivationStatus(
            waitlist_status=data.get("waitlist_status", "UNKNOWN"),
            has_hatch_access=data.get("has_hatch_access", False),
            has_redeemed_invite_code=data.get("has_redeemed_invite_code", False),
            raw_response=data,
        )

    def redeem_invite_code(self, invite_code: str) -> Dict[str, Any]:
        """
        Step 7: Redeem invite code (/hatch/invite_code/redeem).
        """
        resp = self.api.post(
            HatchEndpoints.INVITE_CODE_REDEEM,
            headers={"Content-Type": "application/json; charset=utf-8"},
            json={"code": invite_code},
        )
        data = cast(Dict[str, Any], resp.json())
        logger.info(f"Invite code redeemed! New status: {data.get('waitlist_status')}")
        return data
