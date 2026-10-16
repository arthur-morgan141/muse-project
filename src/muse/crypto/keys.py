"""
Cryptographic key management and fallback keys for Meta Muse.
"""

from typing import Optional, Tuple

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicKey

# Default Meta RSA public key (extracted from disassembly of X.C9CS.A00 in base.apk)
# Used as official fallback when the server does not provide a compatible PEM RSA key
DEFAULT_META_RSA_PUBLIC_KEY: str = """-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAvcu1KMDR1vzuBr9iYKW8
KWmhT8CVUBRkchiO8861H7zIOYRwkQrkeHA+0mkBo3Ly1PiLXDkbKQZyeqZbspke
4e7WgFNwT23jHfRMV/cNPxjPEy4kxNEbzLET6GlWepGdXFhzHfnS1PinGQzj0ZOU
ZM3pQjgGRL9fAf8brt1ewhQ5XtpvKFdPyQq5BkeFEDKoInDsC/yKDWRAx2twgPFr
CYUzAB8/yXuL30ErTHT79bt3yTnv1fRtE19tROIlBuqruwSBk9gGq/LuvSECgsl5
z4VcpHXhgZt6MhrAj6y9vAAxO2RVrt0Mq4OY4HgyYz9Wlr1vAxXXGAAYIvrhAYLP
7QIDAQAB
-----END PUBLIC KEY-----"""


def resolve_encryption_key(
    server_pubkey: Optional[str] = None,
    server_key_id: Optional[int] = None,
) -> Tuple[RSAPublicKey, int, str]:
    """
    Resolves the password encryption key:
    - If the server provides a valid PEM RSA key: use mode '2' with server key_id.
    - Otherwise (e.g. hex X25519 or None): fall back to default hardcoded Meta RSA (key_id 41, mode '1').

    Returns: (rsa_public_key, effective_key_id, mode_string)
    """
    if server_pubkey and "BEGIN PUBLIC KEY" in server_pubkey:
        try:
            pubkey = serialization.load_pem_public_key(server_pubkey.encode("utf-8"))
            if isinstance(pubkey, RSAPublicKey):
                return pubkey, (server_key_id or 1), "2"
        except Exception:
            pass

    # Meta default hardcoded RSA fallback
    default_pubkey = serialization.load_pem_public_key(DEFAULT_META_RSA_PUBLIC_KEY.encode("utf-8"))
    assert isinstance(default_pubkey, RSAPublicKey)
    return default_pubkey, 41, "1"
