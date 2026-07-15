"""
Switch the bot between long-polling (Replit / `python main.py`) and the
Vercel serverless webhook (`api/webhook.py`).

Usage
-----
  # After deploying to Vercel, point Telegram at the serverless endpoint:
  python scripts/setup_webhook.py --url https://your-app.vercel.app/api/webhook

  # To move back to long-polling (e.g. back on Replit):
  python scripts/setup_webhook.py --delete
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aiogram import Bot  # noqa: E402

from bot.setup import create_dispatcher  # noqa: E402
from config import load_config  # noqa: E402


async def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", help="Full webhook URL, e.g. https://app.vercel.app/api/webhook")
    parser.add_argument("--delete", action="store_true", help="Delete the webhook and return to long-polling")
    args = parser.parse_args()

    config = load_config()
    bot = Bot(token=config.bot_token)

    try:
        if args.delete:
            await bot.delete_webhook(drop_pending_updates=True)
            print("✅ Webhook deleted. You can now run `python main.py` for long-polling.")
            return

        if not args.url:
            parser.error("--url is required unless --delete is passed")

        secret = os.environ.get("WEBHOOK_SECRET")
        if not secret:
            print(
                "⚠️  WEBHOOK_SECRET is not set. The endpoint will accept requests without "
                "verifying they came from Telegram. Set WEBHOOK_SECRET (any random string, "
                "shared between this env and your Vercel project's env vars) before going live."
            )

        # Derive the exact update types this build actually listens for, the
        # same way main.py does for long-polling, so nothing is silently missed.
        dp = create_dispatcher()
        allowed_updates = dp.resolve_used_update_types()

        await bot.set_webhook(
            url=args.url,
            secret_token=secret,
            drop_pending_updates=True,
            allowed_updates=allowed_updates,
        )
        info = await bot.get_webhook_info()
        print(f"✅ Webhook set: {info.url}")
        print(f"   Allowed updates: {allowed_updates}")
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
