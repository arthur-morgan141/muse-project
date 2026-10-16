"""
Meta Password Cipher Engine based on ARM64 native library libbackgroundinit.so (CryptoPubNative)
and Android decompiler X.C9CS.A00 / AuraPasswordEncryptionHelper.
"""

import base64
import os
import struct
import time
from typing import Optional

from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from muse.core.exceptions import CryptographyError
from muse.crypto.keys import resolve_encryption_key


def encrypt_meta_password(
    password: str,
    server_key_id: Optional[int] = None,
    server_pubkey: Optional[str] = None,
    custom_timestamp: Optional[int] = None,
) -> str:
    """
    Encrypts password according to the specification in native library libbackgroundinit.so (CryptoPubNative)
    and Android class com.facebook.aura.auth.encryption.AuraPasswordEncryptionHelper.

    Binary encryption architecture:
    - Engine: OpenSSL EVP_SealInit with EVP_aes_256_gcm()
    - Symmetric key: 32-byte AES-256 key encrypted using RSA PKCS#1 v1.5
    - IV: 12 random bytes
    - AAD: Timestamp in seconds (UTF-8 string)
    - Ciphertext: Result of AES-256-GCM encryption on the password
    - Tag: 16-byte GCM authentication tag

    Binary envelope layout:
    - Byte 0: Version (0x01)
    - Byte 1: key_id (uint8)
    - Bytes 2-13: IV (12 bytes)
    - Bytes 14-15: Encrypted key length (uint16 little-endian, ekl)
    - Bytes 16 .. 16+ekl-1: Encrypted symmetric key (RSA)
    - Bytes 16+ekl .. 16+ekl+15: GCM Tag (16 bytes)
    - Bytes 16+ekl+16 ..: GCM Ciphertext

    Wire string format: #PWD_ENC:<mode>:<timestamp>:<base64_payload>
    """
    if not password:
        raise CryptographyError("Password to encrypt cannot be empty")

    ts_int = custom_timestamp if custom_timestamp is not None else int(time.time())
    timestamp_str = str(ts_int)

    pubkey, key_id, mode_str = resolve_encryption_key(server_pubkey, server_key_id)

    try:
        # 1. Generate 32-byte AES-256 key & 12-byte IV
        aes_key = os.urandom(32)
        iv = os.urandom(12)

        # 2. Encrypt symmetric key with RSA PKCS#1 v1.5 (EVP_SealInit)
        ek = pubkey.encrypt(aes_key, padding.PKCS1v15())
        ekl = len(ek)

        # 3. Encrypt password using AES-256-GCM with timestamp as AAD
        aesgcm = AESGCM(aes_key)
        encrypted_blob = aesgcm.encrypt(iv, password.encode("utf-8"), timestamp_str.encode("utf-8"))
        ciphertext = encrypted_blob[:-16]
        tag = encrypted_blob[-16:]

        # 4. Construct binary byte structure matching assembly offset 0x1bcf14 in libbackgroundinit.so
        payload = bytearray()
        payload.append(1)                        # Byte 0: version = 1
        payload.append(key_id & 0xFF)           # Byte 1: key_id
        payload.extend(iv)                      # Bytes 2-13: IV 12 bytes
        payload.extend(struct.pack("<H", ekl))  # Bytes 14-15: ekl (uint16 little-endian)
        payload.extend(ek)                      # Bytes 16..16+ekl-1: Encrypted AES key
        payload.extend(tag)                     # Tag 16 bytes
        payload.extend(ciphertext)              # Ciphertext

        b64_payload = base64.b64encode(payload).decode("utf-8")
        return f"#PWD_ENC:{mode_str}:{timestamp_str}:{b64_payload}"

    except Exception as e:
        raise CryptographyError(f"Failed to generate Meta password envelope: {e}") from e
