"""
Unified CLI entrypoint for Meta Muse Client.
Commands:
  muse register      - Run onboarding and registration flow
  muse status        - Check gatekeeper / activation status using saved token
  muse redeem        - Redeem invite code using saved token
  muse config        - Inspect current environment configuration
"""

import argparse
import getpass
import json
import shutil
import sys

from muse.__version__ import __version__
from muse.auth.client import MuseAuthClient
from muse.core.config import get_config, load_config
from muse.core.logging import setup_logger
from muse.core.models import UserProfile
from muse.termux import (
    acquire_wake_lock,
    get_clipboard_otp,
    is_termux,
    release_wake_lock,
    send_notification,
    vibrate,
)

logger = setup_logger("muse.cli")


def print_banner(step: int, title: str) -> None:
    """Prints a responsive banner formatted cleanly on desktop and mobile screens."""
    terminal_width = shutil.get_terminal_size((80, 20)).columns
    max_width = min(terminal_width, 70)
    step_str = f"[{step}] {title}"
    if len(step_str) >= max_width:
        print(f"\n--- {step_str} ---")
        return

    side_padding = max((max_width - len(step_str) - 2) // 2, 2)
    bar = "=" * side_padding
    print(f"\n{bar} {step_str} {bar}")


def handle_register(args: argparse.Namespace) -> None:
    config = get_config()
    client = MuseAuthClient(config)

    wake_locked = False
    if is_termux() and not args.no_wake_lock:
        wake_locked = acquire_wake_lock()

    try:
        print(f"Meta Muse Registration Client (v{__version__}) - Environment: [{config.env}]")
        if is_termux():
            print("[Termux] Android environment detected. Termux:API integrations active.")

        # Determine session resumption strategy:
        has_cache = client.session_store.has_session()
        force_new = getattr(args, "new_session", False)
        force_resume = getattr(args, "resume", False)

        if has_cache and not force_new and not force_resume:
            summary = client.session_store.get_summary()
            if summary:
                print("\n[IN-FLIGHT SESSION DETECTED]")
                print(f"  Target Contact : {summary['contact_point']}")
                print(f"  Current Stage  : {summary['last_step']}")
                print(f"  Device UUID    : {summary['device_id'][:18]}...")
                choice = input("\nDo you want to RESUME this session? [Y/n] (type 'n' to register a new account): ").strip().lower()
                if choice in ("", "y", "yes"):
                    state = client.initialize_session(resume=True)
                else:
                    client.session_store.clear()
                    state = client.initialize_session(force_new=True)
                    print("[INFO] Previous session cleared. Starting fresh registration.")
            else:
                state = client.initialize_session(force_new=False)
        elif force_new:
            state = client.initialize_session(force_new=True)
            print("[INFO] Starting brand new registration (--new specified).")
        elif force_resume:
            state = client.initialize_session(resume=True)
            print("[INFO] Resuming in-flight registration (--resume specified).")
        else:
            state = client.initialize_session()

        # Step 1: Start onboarding
        if not state.temp_token:
            print_banner(1, "Initiate Onboarding (/hatch/auth/start)")
            try:
                client.start_onboarding()
                print("[OK] Anonymous session initialized and server encryption key obtained.")
            except Exception as e:
                print(f"[FAILED] Failed to initialize onboarding: {e}")
                sys.exit(1)
        else:
            print(f"\n[INFO] Resuming in-flight session: Device {state.device_id[:8]}...")

        # Steps 2 & 3: Contact point & Dispatch OTP
        if not state.completion_handle:
            print_banner(2, "Login & Registration Options (/hatch/auth/login_options)")
            contact_point = args.email or state.contact_point or input("Enter contact email address: ").strip()
            region = args.region or state.region

            if not contact_point:
                print("[ERROR] Contact email cannot be empty.")
                sys.exit(1)

            try:
                opts = client.check_login_options(contact_point, region)
                print(f"[OK] Detected authentication flow: {opts.get('flow', 'REGISTER')}")
            except Exception as e:
                print(f"[FAILED] Error in login_options: {e}")
                sys.exit(1)

            print_banner(3, "Dispatch OTP Code (/hatch/auth/send_otp)")
            try:
                client.send_otp()
                print(f"[OK] OTP verification code dispatched to {contact_point}.")
                send_notification("Meta Muse", f"OTP code dispatched to {contact_point}")
            except Exception as e:
                print(f"[FAILED] Error in send_otp: {e}")
                sys.exit(1)

            if args.send_only:
                print("\n[DISPATCH COMPLETED] Registration session state has been saved.")
                print(f"Check your inbox ({contact_point}) for the 6-digit OTP code.")
                print("To resume registration, run:")
                print("  muse register --otp <CODE>")
                return

            # Step 4: Confirm OTP
            print_banner(4, "Confirm OTP Code (/hatch/auth/confirm_otp)")
            otp_code = args.otp

            # Check Termux clipboard if no CLI argument passed
            if not otp_code and is_termux():
                clip_otp = get_clipboard_otp()
                if clip_otp:
                    print(f"[Termux Clipboard] Found 6-digit OTP in clipboard: {clip_otp}")
                    use_clip = input(f"Use code '{clip_otp}'? [Y/n]: ").strip().lower()
                    if use_clip in ("", "y", "yes"):
                        otp_code = clip_otp

            if not otp_code:
                otp_code = input("Enter the 6-digit OTP code received: ").strip()

            if not otp_code:
                print("[ERROR] OTP code cannot be empty.")
                sys.exit(1)

            try:
                handle = client.confirm_otp(otp_code)
                print("[OK] OTP successfully verified!")
                print(f"     Completion Handle: {handle[:25]}...")
            except Exception as e:
                print(f"[FAILED] Error confirming OTP: {e}")
                sys.exit(1)
        else:
            print("\n[INFO] Completion handle is already available from previous session.")

        # Step 5: Complete Registration
        print_banner(5, "Complete Account Registration (/hatch/auth/register_completion)")
        first_name = args.first_name or input("First Name: ").strip()
        last_name = args.last_name or input("Last Name: ").strip()
        dob = args.dob or input("Date of Birth (Format: YYYY-MM-DD): ").strip()
        password = args.password or getpass.getpass("New Account Password: ").strip()

        if not password:
            print("[ERROR] Password cannot be empty.")
            sys.exit(1)

        profile = UserProfile(
            first_name=first_name,
            last_name=last_name,
            date_of_birth=dob,
            password=password,
            region=args.region or state.region,
        )

        try:
            tokens = client.complete_registration(profile)
            print("\n[SUCCESS] Meta Muse Account Created Successfully!")
            print(f"  Abra User ID     : {tokens.abra_user_id}")
            print(f"  Abra Token       : {tokens.abra_access_token[:30]}...")
            print(f"  FRL Account ID   : {tokens.frl_account_id}")

            send_notification("Meta Muse", "Account successfully created!")
            vibrate(200)
        except Exception as e:
            print(f"[FAILED] Error in register_completion: {e}")
            sys.exit(1)

        # Step 6: Check Gatekeeper Status
        print_banner(6, "Check Gatekeeper Status (/hatch/activation_statuses)")
        try:
            status = client.check_activation_status()
            print(f"  Waitlist Status      : {status.waitlist_status}")
            print(f"  Hatch Access Active  : {status.has_hatch_access}")
            print(f"  Invite Code Redeemed : {status.has_redeemed_invite_code}")
        except Exception as e:
            print(f"[WARNING] Failed to query activation status: {e}")
            return

        # Step 7: Redeem Invite Code (optional)
        print_banner(7, "Redeem Invite Code (/hatch/invite_code/redeem)")
        invite_code = args.invite_code or input("Enter Invite Code [Press Enter to skip]: ").strip()
        if not invite_code:
            print("[INFO] Invite code redemption skipped. Base registration completed.")
            return

        try:
            redeem_res = client.redeem_invite_code(invite_code)
            print("\n[COMPLETED] Invite Code Redeemed Successfully!")
            print(f"  New Account Status : {redeem_res.get('waitlist_status')}")
            print("  [ACCESS UNLOCKED] 1 Billion Token access quota activated!")
            send_notification("Meta Muse", f"Invite redeemed! Status: {redeem_res.get('waitlist_status')}")
            vibrate(200)
        except Exception as e:
            print(f"[FAILED] Failed to redeem invite code: {e}")

    finally:
        if wake_locked:
            release_wake_lock()


def handle_status(args: argparse.Namespace) -> None:
    config = get_config()
    client = MuseAuthClient(config)
    tokens = client.token_store.load()
    if not tokens:
        print(f"[ERROR] No credentials found in {config.credentials_path}. Run 'muse register' first.")
        sys.exit(1)

    client.api.set_auth_token(tokens.abra_access_token)
    try:
        status = client.check_activation_status()
        print("\n=== Meta Muse Account Status ===")
        print(f"  User ID              : {tokens.abra_user_id}")
        print(f"  Waitlist Status      : {status.waitlist_status}")
        print(f"  Hatch Access Active  : {status.has_hatch_access}")
        print(f"  Invite Code Redeemed : {status.has_redeemed_invite_code}")
    except Exception as e:
        print(f"[FAILED] Error: {e}")
        sys.exit(1)


def handle_redeem(args: argparse.Namespace) -> None:
    config = get_config()
    client = MuseAuthClient(config)
    tokens = client.token_store.load()
    if not tokens:
        print(f"[ERROR] No credentials found in {config.credentials_path}. Run 'muse register' first.")
        sys.exit(1)

    client.api.set_auth_token(tokens.abra_access_token)
    code = args.code or input("Enter Invite Code: ").strip()
    if not code:
        print("[ERROR] Invite code cannot be empty.")
        sys.exit(1)

    try:
        res = client.redeem_invite_code(code)
        print("\n[SUCCESS] Invite code redeemed successfully!")
        print(f"  New Status: {res.get('waitlist_status')}")
        print("  [ACCESS UNLOCKED] 1 Billion Token access quota activated!")
        send_notification("Meta Muse", f"Invite redeemed! Status: {res.get('waitlist_status')}")
        vibrate(200)
    except Exception as e:
        print(f"[FAILED] Error: {e}")
        sys.exit(1)


def handle_session(args: argparse.Namespace) -> None:
    config = get_config()
    client = MuseAuthClient(config)
    action = args.action or "show"

    if action in ("show", "status"):
        summary = client.session_store.get_summary()
        if not summary:
            print("\n[INFO] No in-flight registration session found.")
            return
        print("\n=== In-Flight Registration Session ===")
        print(f"  Target Contact : {summary['contact_point']}")
        print(f"  Current Stage  : {summary['last_step']}")
        print(f"  Region         : {summary['region']}")
        print(f"  Device UUID    : {summary['device_id']}")
        print(f"  Temp Token     : {'Available' if summary['has_temp_token'] else 'None'}")
        print(f"  OTP Confirmed  : {'Yes (Handle Ready)' if summary['has_completion_handle'] else 'No'}")
        print(f"  Cache File     : {summary['cache_path']}")
    elif action in ("clear", "reset", "delete"):
        cleared = client.session_store.clear()
        if cleared:
            print("\n[OK] In-flight registration session cache has been deleted.")
        else:
            print("\n[INFO] No session cache was present.")


def handle_config(args: argparse.Namespace) -> None:
    config = get_config()
    print(f"\n=== Active Muse Configuration [{config.env}] ===")
    print(json.dumps(config.as_dict(), indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="muse",
        description="Meta Muse (com.facebook.aura) Direct API Client & Architecture Runtime",
    )
    parser.add_argument("--version", "-v", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("--env", help="Environment override (development, production, test)")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Subcommand: register
    reg_p = subparsers.add_parser("register", help="Execute account onboarding, OTP verification, and registration")
    reg_p.add_argument("--email", "-e", help="Contact email address")
    reg_p.add_argument("--region", "-r", default="US", help="ISO country / region code (default: US)")
    reg_p.add_argument("--otp", "-o", help="6-digit OTP code if already received")
    reg_p.add_argument("--first-name", help="User first name")
    reg_p.add_argument("--last-name", help="User last name")
    reg_p.add_argument("--dob", help="Date of birth YYYY-MM-DD")
    reg_p.add_argument("--password", "-p", help="New account password")
    reg_p.add_argument("--invite-code", "-i", help="Invite code")
    reg_p.add_argument("--send-only", action="store_true", help="Send OTP and persist session without proceeding")
    reg_p.add_argument("--new", "--fresh", "--new-session", dest="new_session", action="store_true",
                       help="Start a brand new registration without resuming existing session")
    reg_p.add_argument("--resume", action="store_true",
                       help="Force resume existing in-flight session without prompting")
    reg_p.add_argument("--no-wake-lock", action="store_true", help="Disable Termux wake-lock during registration")
    reg_p.set_defaults(func=handle_register)

    # Subcommand: session
    sess_p = subparsers.add_parser("session", help="Inspect or clear active in-flight registration session")
    sess_p.add_argument("action", nargs="?", choices=["show", "status", "clear", "reset"], default="show",
                        help="Session action: 'show' (default) or 'clear'")
    sess_p.set_defaults(func=handle_session)

    # Subcommand: status
    stat_p = subparsers.add_parser("status", help="Check account activation and waitlist status with saved token")
    stat_p.set_defaults(func=handle_status)

    # Subcommand: redeem
    red_p = subparsers.add_parser("redeem", help="Redeem invite code using stored token")
    red_p.add_argument("code", nargs="?", help="Invite code")
    red_p.set_defaults(func=handle_redeem)

    # Subcommand: config
    cfg_p = subparsers.add_parser("config", help="Inspect active application configuration")
    cfg_p.set_defaults(func=handle_config)

    args = parser.parse_args()

    if args.env:
        load_config(env=args.env)

    if hasattr(args, "func"):
        try:
            args.func(args)
        except KeyboardInterrupt:
            print("\n[CANCELLED] Operation aborted by user.")
            sys.exit(0)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
