# Termux Android Setup & Usage Guide

This guide covers running the **Meta Muse Registration & 1-Billion Token Redemption Client** directly on Android using Termux.

---

## 1. Prerequisites

1. **Termux App:**  
   Install Termux from **[F-Droid](https://f-droid.org/packages/com.termux/)** or the official **[Termux GitHub Releases](https://github.com/termux/termux-app/releases)**.  
   *(Do NOT use the outdated Google Play Store release, as its package mirrors are deprecated).*

2. **Termux:API App (Recommended):**  
   Install the **[Termux:API Addon](https://f-droid.org/packages/com.termux.api/)** from F-Droid to enable hardware integrations:
   - Automatic 6-digit OTP detection from the Android clipboard.
   - Status bar push notifications upon OTP dispatch and registration completion.
   - Haptic vibration feedback on successful invite code redemption.

---

## 2. Automated Setup (Recommended)

Run the included zero-compile bootstrap script:

```bash
cd ~/muse-project
bash scripts/install_termux.sh
```

### What This Script Does:
1. Updates Termux package repositories (`pkg update -y`).
2. Installs pre-compiled Bionic libc packages: `python`, `python-cryptography`, `openssl`, `libffi`, `git`, and `termux-api`.
3. Creates a virtual environment using `--system-site-packages` so Python directly accesses the pre-compiled native ARM64 cryptography library (avoiding heavy Rust/C compilation on device).
4. Installs pure-Python dependencies (`httpx`, `pyyaml`).
5. Installs the `muse` CLI package in editable mode (`pip install -e . --no-deps`).

---

## 3. Manual Installation (Alternative)

If you prefer to configure the environment step-by-step:

```bash
# 1. Update packages
pkg update -y

# 2. Install native system dependencies
pkg install -y python python-cryptography openssl libffi git termux-api

# 3. Create virtual environment with system site-packages
python3 -m venv --system-site-packages .venv
source .venv/bin/activate

# 4. Install pure-Python dependencies
pip install --upgrade pip
pip install -r requirements-termux.txt

# 5. Install the package
pip install -e . --no-deps
```

---

## 4. Usage on Android

Activate the virtual environment:
```bash
source .venv/bin/activate
```

### A. Full Interactive Registration (Recommended)
```bash
muse register
```
- **Automatic Wake-Lock:** Automatically holds `termux-wake-lock` during registration to prevent Android Doze from suspending the process when switching between apps.
- **Auto-Clipboard Detection:** When the 6-digit OTP arrives via email or SMS, simply copy it. The CLI detects it in your clipboard and prompts:  
  `[Termux Clipboard] Found 6-digit OTP in clipboard: 123456. Use code '123456'? [Y/n]`

### B. Two-Stage Registration (Send OTP First, Confirm Later)
Useful if you want to dispatch the OTP and close or background the terminal:

1. **Dispatch OTP:**
   ```bash
   muse register --email user@example.com --send-only
   ```
2. **Resume and finalize once OTP is received:**
   ```bash
   muse register --otp 123456
   ```

### C. Check Gatekeeper & Activation Status
Check if your account is active or still on the waitlist:
```bash
muse status
```

### D. Redeem Invite Code (Unlock 1-Billion Token Quota)
Redeem an invite code using your saved credentials:
```bash
muse redeem YOUR-INVITE-CODE
```
Upon success, the terminal will confirm:
```text
[SUCCESS] Invite code redeemed successfully!
  New Status: FULLY_ACTIVATED
  [ACCESS UNLOCKED] 1 Billion Token access quota activated!
```

---

## 5. Termux Optimization Details

- **Responsive Mobile Layout:** Banners and status blocks automatically adjust their width to match your phone's terminal columns (`shutil.get_terminal_size()`), eliminating awkward text wrapping in portrait mode.
- **POSIX 0600 Permissions:** Generated account tokens and session caches (`data/sessions/credentials.json`) are written with owner-only `0600` permissions.
- **Graceful Fallback:** If `termux-api` is not installed or permissions are denied, the client falls back to standard keyboard prompts without raising errors.

---

## 6. Troubleshooting

- **Clipboard not detected:**  
  Ensure both the `termux-api` package (`pkg install termux-api`) and the Termux:API Android application from F-Droid are installed, and grant clipboard permissions when prompted.
- **Process killed in background (Android 12+):**  
  Disable battery optimization for Termux in Android Settings (`Settings -> Apps -> Termux -> Battery -> Unrestricted`).
