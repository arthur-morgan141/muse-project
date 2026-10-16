"""
Endpoint definitions for Meta Muse account registration and invite code redemption.
"""


class HatchEndpoints:
    # Authentication & Onboarding
    AUTH_START = "/hatch/auth/start"
    AUTH_LOGIN_OPTIONS = "/hatch/auth/login_options"
    AUTH_SEND_OTP = "/hatch/auth/send_otp"
    AUTH_CONFIRM_OTP = "/hatch/auth/confirm_otp"
    AUTH_REGISTER_COMPLETION = "/hatch/auth/register_completion"

    # Gatekeeper, Waitlist & Invite Code Redemption
    ACTIVATION_STATUSES = "/hatch/activation_statuses"
    INVITE_CODE_REDEEM = "/hatch/invite_code/redeem"
