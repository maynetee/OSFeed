#!/usr/bin/env python3
"""CLI tool for initial Telegram authentication.

Usage:
    python -m app.cli.telegram_setup

This tool:
1. Prompts for phone number (if not in env)
2. Sends auth code via Telegram
3. Prompts for SMS code (interactive!)
4. Prompts for 2FA password (if enabled)
5. Creates session file at telegram_session_path
6. Verifies session works

Run this ONCE locally before deploying to production.
The session file must then be copied to the production server
or mounted via Docker volume.

Deployment Workflow:
1. Get API credentials from my.telegram.org
2. Set environment variables:
   - TELEGRAM_API_ID
   - TELEGRAM_API_HASH
   - TELEGRAM_PHONE
3. Run this script
4. Enter SMS code when prompted
5. Enter 2FA password if enabled
6. Session file created at TELEGRAM_SESSION_PATH
7. Copy session file to server OR configure Docker volume
"""
import asyncio
import sys
import os
from pathlib import Path

# Add parent to path for imports when running as script
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError


def get_env_or_prompt(var_name: str, prompt_text: str, is_secret: bool = False) -> str:
    """Get value from env or prompt user."""
    value = os.environ.get(var_name, "").strip()
    if value:
        if is_secret:
            print(f"{prompt_text}: [from environment]")
        else:
            print(f"{prompt_text}: {value} [from environment]")
        return value

    if is_secret:
        import getpass
        return getpass.getpass(f"{prompt_text}: ")
    else:
        return input(f"{prompt_text}: ").strip()


async def setup_telegram_session():
    """Interactive setup for Telegram session."""
    print("=" * 60)
    print("OSFeed Telegram Setup")
    print("=" * 60)
    print()
    print("This tool will authenticate with Telegram and create a session file.")
    print("You will need:")
    print("  1. API ID and API Hash from my.telegram.org")
    print("  2. Phone number registered with Telegram")
    print("  3. Access to receive SMS or Telegram code")
    print()

    # Get credentials
    api_id_str = get_env_or_prompt("TELEGRAM_API_ID", "API ID")
    try:
        api_id = int(api_id_str)
    except ValueError:
        print("Error: API ID must be a number")
        sys.exit(1)

    api_hash = get_env_or_prompt("TELEGRAM_API_HASH", "API Hash")
    phone = get_env_or_prompt("TELEGRAM_PHONE", "Phone number (with country code, e.g., +1234567890)")

    session_path = os.environ.get("TELEGRAM_SESSION_PATH", "./telegram.session")
    print(f"\nSession will be saved to: {session_path}")

    # Ensure directory exists
    session_dir = Path(session_path).parent
    session_dir.mkdir(parents=True, exist_ok=True)

    # Remove .session extension if present (Telethon adds it)
    if session_path.endswith(".session"):
        session_path = session_path[:-8]

    print("\nConnecting to Telegram...")

    client = TelegramClient(session_path, api_id, api_hash)

    try:
        await client.connect()

        if not await client.is_user_authorized():
            print(f"\nSending authentication code to {phone}...")
            await client.send_code_request(phone)

            print("\nCheck your Telegram app or SMS for the code.")
            code = input("Enter the code you received: ").strip()

            try:
                await client.sign_in(phone, code)
            except SessionPasswordNeededError:
                print("\n2FA is enabled on this account.")
                password = get_env_or_prompt(
                    "TELEGRAM_2FA_PASSWORD",
                    "Enter your 2FA password",
                    is_secret=True
                )
                await client.sign_in(password=password)

        # Verify it works
        me = await client.get_me()
        print()
        print("=" * 60)
        print("SUCCESS!")
        print("=" * 60)
        print(f"Authenticated as: {me.first_name} {me.last_name or ''}")
        print(f"Username: @{me.username}" if me.username else "Username: (none)")
        print(f"Phone: {me.phone}")
        print()
        print(f"Session file created at: {session_path}.session")
        print()
        print("Next steps:")
        print("  1. Copy the session file to your production server")
        print("     OR mount it via Docker volume at /app/data/")
        print("  2. Set TELEGRAM_SESSION_PATH=/app/data/telegram.session")
        print("  3. The production app will use this session automatically")
        print()
        print("IMPORTANT: Keep your session file secure!")
        print("           It grants full access to this Telegram account.")

    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)
    finally:
        await client.disconnect()


def main():
    """Entry point for CLI."""
    try:
        asyncio.run(setup_telegram_session())
    except KeyboardInterrupt:
        print("\n\nSetup cancelled.")
        sys.exit(1)


if __name__ == "__main__":
    main()
