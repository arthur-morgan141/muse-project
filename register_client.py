#!/usr/bin/env python3
"""
Meta Muse (com.facebook.aura) Direct API Registration & Invite Redemption Client.
Backward-compatible wrapper delegating to the modular src/muse package.
"""

import sys
from pathlib import Path

# Add src to sys.path if not installed in site-packages
ROOT_DIR = Path(__file__).resolve().parent
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

# Re-exports for backward compatibility with legacy scripts
from muse.crypto.keys import DEFAULT_META_RSA_PUBLIC_KEY, resolve_encryption_key
from muse.crypto.meta_cipher import encrypt_meta_password
from muse.auth.client import MuseAuthClient
from muse.cli.main import main

if __name__ == "__main__":
    # If invoked directly without subcommand (e.g. register_client.py --email ...),
    # automatically route to the 'register' subcommand
    if len(sys.argv) == 1 or sys.argv[1] not in ("register", "status", "redeem", "config", "-h", "--help"):
        sys.argv.insert(1, "register")
    main()
