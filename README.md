# Meta Muse Registration & 1-Billion Token Redemption Client (Project Aura / Hatch)

This lightweight, modular API client is specifically dedicated to automating the Meta Muse (`com.facebook.aura`) registration flow, OTP verification, native password envelope encryption, and redeeming invite codes to claim the **1 Billion Token** compute quota.

---

## 1. Directory Structure

The repository follows standard modern **`src`-layout** practices with clear separation between configuration, domain logic, automation scripts, test suites, and production container artifacts:

```text
muse-project/
├── .env.example                    # Template for environment variable overrides
├── .gitignore                      # Git exclusion rules for credentials, venv, and caches
├── pyproject.toml                  # PEP 517/518 packaging configuration & tool settings
├── requirements.txt                # Production runtime dependencies
├── requirements-dev.txt            # Development & testing dependencies (pytest, ruff, mypy)
├── register_client.py              # Backward-compatible wrapper for legacy invocations
├── README.md                       # Comprehensive architecture and operational documentation
│
├── config/                         # Hierarchical configuration layers
│   ├── config.base.yaml            # Shared defaults (timeouts, headers, user-agent)
│   ├── config.development.yaml     # Development profile (debug logging, auto-resume, local cache)
│   └── config.production.yaml      # Production profile (hardened timeouts, secure paths)
│
├── docker/                         # Containerization artifacts
│   ├── Dockerfile                  # Multi-stage production container (minimal & non-root user)
│   ├── Dockerfile.dev              # Development container with hot-reloading & volume mounts
│   └── docker-compose.yml          # Compose orchestration for dev and prod environments
│
├── src/                            # Core application source code (src-layout)
│   └── muse/
│       ├── __init__.py             # Public API re-exports
│       ├── __version__.py          # Package semantic versioning (1.0.0)
│       │
│       ├── api/                    # Network transport layer (HTTPX Client)
│       │   ├── __init__.py
│       │   ├── client.py           # HTTP client with RFC-7807 (HatchProblemJson) error parsing
│       │   └── endpoints.py        # StefiHatchPath endpoint taxonomy (/hatch/*)
│       │
│       ├── auth/                   # Authentication & registration workflows
│       │   ├── __init__.py
│       │   ├── client.py           # 7-step onboarding and invite code redemption coordinator
│       │   ├── session.py          # State persistence and auto-resumption for multi-step OTP
│       │   └── token_store.py      # Secure storage for permanent tokens (abra_access_token)
│       │
│       ├── cli/                    # Command Line Interface subcommands
│       │   ├── __init__.py
│       │   ├── __main__.py         # python -m muse.cli entrypoint
│       │   └── main.py             # CLI parser: `muse register|status|redeem|config`
│       │
│       ├── core/                   # System core foundation
│       │   ├── __init__.py
│       │   ├── config.py           # Configuration loader (YAML + ENV deep merge)
│       │   ├── exceptions.py       # Domain-specific exception hierarchy
│       │   ├── logging.py          # Structured logging setup
│       │   └── models.py           # Dataclass schemas (SessionState, AuthTokens, UserProfile)
│       │
│       │
│       ├── termux/                 # Termux Android hardware & system integration
│       │   ├── __init__.py
│       │   └── helper.py           # Clipboard OTP detection, notifications, wake-lock
│       │
│       └── crypto/                 # Meta binary cryptographic engines
│           ├── __init__.py
│           ├── keys.py             # RSA 2048 fallback resolution & public key management
│           └── meta_cipher.py      # #PWD_ENC envelope (EVP_SealInit + AES-256-GCM)
│
├── scripts/                        # Automation & execution launchers
│   ├── run_dev.sh                  # Development environment runner (MUSE_ENV=development)
│   └── run_prod.sh                 # Production environment runner (MUSE_ENV=production)
│
├── tests/                          # Automated test suite
│   ├── __init__.py
│   ├── conftest.py                 # Pytest shared fixtures
│   └── unit/
│       ├── test_config.py          # Tests for configuration parsing and ENV overrides
│       ├── test_crypto.py          # Tests for binary envelope encryption and byte layout
│       └── test_models.py          # Tests for dataclass serialization
│
└── data/                           # Runtime working directory (git-ignored)
    └── sessions/                   # In-flight session caches and stored credentials
```

---

## 2. Development Workflow

### 2.1. Virtual Environment Setup
```bash
cd /workspace/muse-project

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install development dependencies and install package in editable mode
pip install --upgrade pip
pip install -r requirements-dev.txt
pip install -e .
```

### 2.2. Running Automated Tests
```bash
# Run test suite with pytest
pytest
```

### 2.3. Running Development Scripts
Use the development launcher script, which automatically sets `MUSE_ENV=development` and debug logging:
```bash
./scripts/run_dev.sh register --help
./scripts/run_dev.sh config
```

### 2.4. Termux Android Installation
For Termux on Android, run the automated zero-compile installer which uses Termux pre-built `python-cryptography` (preventing Rust/C compilation against Android Bionic libc) and integrates with Termux:API:
```bash
bash scripts/install_termux.sh
```
Key Termux features supported:
- **Auto-Clipboard OTP Detection:** Automatically reads 6-digit codes copied to Android clipboard.
- **Background Wake-Lock:** Automatically acquires `termux-wake-lock` during registration to prevent Android Doze termination.
- **Native Android Notifications & Haptics:** Push notifications on OTP dispatch and vibration on successful account creation.

---

## 3. Production Deployment

### 3.1. Environment Configuration (.env)
Copy `.env.example` to `.env` and configure parameters:
```bash
cp .env.example .env
```

### 3.2. Running Native Production Mode
```bash
./scripts/run_prod.sh register
```

### 3.3. Running with Docker
The project includes a hardened **multi-stage Dockerfile** that produces a minimal image running under an unprivileged user (`museuser`):

```bash
# Build production image via Docker Compose
cd docker
docker compose build muse-prod

# Run CLI inside isolated container
docker compose run --rm muse-prod register
```

---

## 4. CLI Usage Guide (`muse`)

The primary CLI provides structured subcommands:

### A. New Account Registration (`muse register`)
* **Interactive Mode (Recommended):**
  Prompts for confirmation if an in-flight session is found, or register clean:
  ```bash
  muse register
  ```
* **Force Brand New Account Registration (No Auto-Resume):**
  ```bash
  muse register --new
  ```
* **Explicit Resume of In-Flight Session:**
  ```bash
  muse register --resume
  ```
* **Two-Stage Mode (Dispatch OTP first, confirm later):**
  ```bash
  # Stage 1: Send OTP code
  muse register --email user@example.com --region US --send-only

  # Stage 2: Confirm OTP and finalize
  muse register --otp 123456
  ```
* **Full Argument Mode (One-liner):**
  ```bash
  muse register \
    --email user@example.com \
    --region US \
    --otp 123456 \
    --first-name "Alice" \
    --last-name "Doe" \
    --dob "1996-08-15" \
    --password "SecurePass123!" \
    --invite-code "INVITE-CODE-ABC"
  ```

### B. Inspect or Clear In-Flight Sessions (`muse session`)
Inspect active in-flight session progress or wipe the cache cleanly:
```bash
# View active in-flight session state
muse session show

# Discard/reset in-flight session cache
muse session clear
```

### C. Query Activation & Waitlist Status (`muse status`)
Check current account gatekeeper status using saved permanent credentials:
```bash
muse status
```

### D. Redeem Invite Code (`muse redeem`)
Redeem an invite code for an account that is on the waitlist:
```bash
muse redeem YOUR-INVITE-CODE
```

### E. Inspect Active Configuration (`muse config`)
Display currently merged configuration values from YAML and environment variables:
```bash
muse config
```

### F. Backward Compatibility (`register_client.py`)
Legacy scripts invoking `register_client.py` continue to work seamlessly:
```bash
.venv/bin/python3 register_client.py --email user@example.com
```

---

## 5. Security & Cryptographic Architecture
1. **Password Envelope (`#PWD_ENC`):** Conforms precisely to ARM64 native disassembly of `libbackgroundinit.so`. Uses **AES-256-GCM** with a 32-byte symmetric key encrypted using Meta's default RSA PKCS#1 v1.5 public key (key_id 41).
2. **RFC-7807 Standard Error Handling:** Server errors are translated into typed `MuseApiError` exceptions with HTTP status, title, and detailed diagnostic information.
3. **Isolated Credential Storage:** Permanent tokens and account identifiers are persisted to `data/sessions/credentials.json` with restricted permissions and excluded by `.gitignore`.
