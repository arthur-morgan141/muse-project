"""
Unit tests for data models and serialization.
"""

from muse.core.models import SessionState, AuthTokens, UserProfile


def test_session_state_serialization():
    state = SessionState(
        device_id="dev-1234",
        waterfall_id="wat-5678",
        temp_token="tok_abc",
        contact_point="user@example.com",
    )
    d = state.to_dict()
    assert d["device_id"] == "dev-1234"
    assert d["contact_point"] == "user@example.com"

    restored = SessionState.from_dict(d)
    assert restored.device_id == state.device_id
    assert restored.waterfall_id == state.waterfall_id
    assert restored.temp_token == state.temp_token


def test_auth_tokens_serialization():
    tokens = AuthTokens(
        abra_access_token="abra_token_secret_999",
        abra_user_id="user_12345",
        frl_account_id="frl_67890",
    )
    d = tokens.to_dict()
    restored = AuthTokens.from_dict(d)
    assert restored.abra_access_token == "abra_token_secret_999"
    assert restored.abra_user_id == "user_12345"
