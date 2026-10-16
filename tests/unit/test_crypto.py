"""
Unit tests for Meta password envelope encryption and RSA key resolution.
"""

import base64
import struct
import pytest

from muse.crypto.keys import resolve_encryption_key, DEFAULT_META_RSA_PUBLIC_KEY
from muse.crypto.meta_cipher import encrypt_meta_password
from muse.core.exceptions import CryptographyError


def test_resolve_encryption_key_fallback():
    # Pass non-PEM / dummy string -> should fall back to default RSA key_id 41, mode 1
    pubkey, key_id, mode = resolve_encryption_key("dummy_hex_curve25519", 233)
    assert key_id == 41
    assert mode == "1"
    assert pubkey is not None


def test_encrypt_meta_password_format():
    password = "SuperSecretPassword123!"
    result = encrypt_meta_password(password, server_key_id=41)

    assert result.startswith("#PWD_ENC:1:")
    parts = result.split(":")
    assert len(parts) == 4
    assert parts[0] == "#PWD_ENC"
    assert parts[1] == "1"
    assert parts[2].isdigit()  # Timestamp

    # Decode base64 payload and verify binary envelope layout
    payload = base64.b64decode(parts[3])
    assert len(payload) > 288  # 1(ver) + 1(id) + 12(iv) + 2(ekl) + 256(ek) + 16(tag) + cipher
    assert payload[0] == 1     # Version 1
    assert payload[1] == 41    # Key ID 41

    ekl = struct.unpack("<H", payload[14:16])[0]
    assert ekl == 256          # 2048-bit RSA encrypted key length


def test_encrypt_meta_password_empty_fails():
    with pytest.raises(CryptographyError):
        encrypt_meta_password("")
