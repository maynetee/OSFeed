#!/usr/bin/env python3
"""CLI tool for initial Telegram authentication.

Usage:
    python -m app.cli.telegram_setup

This tool:
1. Prompts for phone number (if not in env)
2. Sends auth code via Telegram
3. Prompts for SMS code (interactive!)
4. Prompts for 2FA password (if enabled)
5. Creates a StringSession that can be used as an environment variable
6. Verifies session works

The StringSession output can be set as TELEGRAM_SESSION_STRING in Coolify
or any cloud deployment platform.

Deployment Workflow:
1. Get API credentials from my.telegram.org
2. Set environment variables locally:
   - TELEGRAM_API_ID
   - TELEGRAM_API_HASH
   - TELEGRAM_PHONE
3. Run this script
4. Enter SMS/Telegram code when prompted
5. Enter 2FA password if enabled
6. Copy the TELEGRAM_SESSION_STRING output to Coolify
"""
import asyncio
import sys
import os
from pathlib import Path

# Add parent to path for imports when running as script
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.errors import SessionPasswordNeededError, RPCError, FloodWaitError


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
    print("This tool will authenticate with Telegram and generate a")
    print("StringSession that you can use as an environment variable.")
    print()
    print("You will need:")
    print("  1. API ID and API Hash from my.telegram.org")
    print("  2. Phone number registered with Telegram")
    print("  3. Access to receive Telegram code (in app or SMS)")
    print()

    # Get credentials
    api_id_str = get_env_or_prompt("TELEGRAM_API_ID", "API ID")
    try:
        api_id = int(api_id_str)
    except ValueError:
        print("Error: API ID must be a number")
        sys.exit(1)

    api_hash = get_env_or_prompt("TELEGRAM_API_HASH", "API Hash")
    phone = get_env_or_prompt("TELEGRAM_PHONE", "Phone number (with country code, e.g., +33612345678)")

    print("\nConnecting to Telegram...")

    # Use StringSession for portable session
    client = TelegramClient(StringSession(), api_id, api_hash)

    try:
        await client.connect()

        if not await client.is_user_authorized():
            print(f"\nSending authentication code to {phone}...")
            await client.send_code_request(phone)

            print()
            print("=" * 60)
            print("CHECK YOUR TELEGRAM APP FOR THE CODE")
            print("(or SMS if Telegram app is not installed)")
            print("=" * 60)
            print()
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

        # Get the session string
        session_string = client.session.save()

        print()
        print("=" * 60)
        print("SUCCESS!")
        print("=" * 60)
        print(f"Authenticated as: {me.first_name} {me.last_name or ''}")
        print(f"Username: @{me.username}" if me.username else "Username: (none)")
        print(f"Phone: {me.phone}")
        print()
        print("=" * 60)
        print("COPY THIS TO COOLIFY AS TELEGRAM_SESSION_STRING:")
        print("=" * 60)
        print()
        print(session_string)
        print()
        print("=" * 60)
        print()
        print("In Coolify, add this environment variable to your backend:")
        print()
        print(f"  TELEGRAM_SESSION_STRING={session_string}")
        print()
        print("This single string contains your authenticated session.")
        print("Set the same value in both preview and production environments.")
        print()
        print("SECURITY WARNING:")
        print("  - This string grants FULL ACCESS to your Telegram account")
        print("  - Keep it secret like a password")
        print("  - Never commit it to git")

    except (RPCError, FloodWaitError) as e:
        print(f"\nTelegram error: {e}")
        sys.exit(1)
    except OSError as e:
        print(f"\nNetwork error: {e}")
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
