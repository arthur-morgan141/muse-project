"""
Endpoint taxonomy for Meta Muse (Hatch API & GraphQL Pando).
Extracted from StefiHatchPath and decompiled networking classes.
"""


class HatchEndpoints:
    # Authentication & Onboarding
    AUTH_START = "/hatch/auth/start"
    AUTH_LOGIN_OPTIONS = "/hatch/auth/login_options"
    AUTH_SEND_OTP = "/hatch/auth/send_otp"
    AUTH_CONFIRM_OTP = "/hatch/auth/confirm_otp"
    AUTH_REGISTER_COMPLETION = "/hatch/auth/register_completion"

    # Gatekeeper & Waitlist
    ACTIVATION_STATUSES = "/hatch/activation_statuses"
    INVITE_CODE_REDEEM = "/hatch/invite_code/redeem"

    # Confidential VM (CVM) & Browser Takeover
    CVM_ALLOCATE = "/hatch/cvm/allocate"
    CVM_RELEASE = "/hatch/cvm/release"
    CVM_HEARTBEAT = "/hatch/cvm/heartbeat"

    # Agentic Runtime & Interactions
    AGENT_PROMPT = "/hatch/agent/prompt"
    AGENT_CANCEL = "/hatch/agent/cancel"

    # Device & Node Sync
    DEVICE_REGISTER = "/hatch/device/register"
    DEVICE_STATE_SYNC = "/hatch/device/state_sync"

    # Meta Pando GraphQL
    GRAPHQL = "/graphql"
