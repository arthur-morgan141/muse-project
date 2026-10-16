#!/usr/bin/env bash
set -e

# ==============================================================================
# Meta Muse Termux Android Automated Bootstrap Installer
# Sets up Python environment with pre-built Bionic cryptography packages.
# ==============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

cd "${PROJECT_ROOT}"

echo "======================================================"
echo "    Meta Muse Client - Termux Android Installer       "
echo "======================================================"

# 1. Verify Termux environment
if [ -z "${PREFIX}" ] || [[ "${PREFIX}" != *"com.termux"* ]]; then
    echo "[WARNING] This script is optimized for Termux on Android."
    echo "Current PREFIX: ${PREFIX:-default system}"
fi

# 2. Update Termux package repositories
echo ""
echo "[Step 1/5] Updating Termux package lists..."
if command -v pkg >/dev/null 2>&1; then
    pkg update -y
else
    echo "[INFO] 'pkg' command not found. Assuming packages are already managed."
fi

# 3. Install precompiled Bionic C/OpenSSL packages
echo ""
echo "[Step 2/5] Installing native Termux packages (zero-compile mode)..."
if command -v pkg >/dev/null 2>&1; then
    # python-cryptography avoids building Rust/C on Android
    pkg install -y python python-cryptography openssl libffi git
    
    # Attempt to install termux-api if available
    echo "[INFO] Installing Termux:API tools..."
    pkg install -y termux-api || echo "[INFO] termux-api package skipped or already present."
fi

# 4. Create virtual environment with access to system-site-packages
echo ""
echo "[Step 3/5] Setting up virtual environment with system site-packages..."
if [ -d "${PROJECT_ROOT}/.venv" ]; then
    echo "[INFO] Existing .venv detected. Re-using..."
else
    python3 -m venv --system-site-packages "${PROJECT_ROOT}/.venv"
fi

source "${PROJECT_ROOT}/.venv/bin/activate"

# 5. Install pure-Python dependencies
echo ""
echo "[Step 4/5] Installing pure-Python requirements..."
pip install --upgrade pip
pip install -r requirements-termux.txt

# 6. Install muse package in editable mode
echo ""
echo "[Step 5/5] Registering muse CLI in virtual environment..."
pip install -e . --no-deps

echo ""
echo "======================================================"
echo "   [SUCCESS] Meta Muse successfully installed!        "
echo "======================================================"
echo "To activate and run:"
echo "  source .venv/bin/activate"
echo "  muse register"
echo "Or use the launcher:"
echo "  ./scripts/run_dev.sh register"
echo ""
