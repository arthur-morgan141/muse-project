"""
Shared test fixtures for Meta Muse tests.
"""

import sys
from pathlib import Path
import pytest

# Ensure src is on Python path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


@pytest.fixture
def mock_crypto_key():
    from muse.crypto.keys import DEFAULT_META_RSA_PUBLIC_KEY
    return DEFAULT_META_RSA_PUBLIC_KEY
