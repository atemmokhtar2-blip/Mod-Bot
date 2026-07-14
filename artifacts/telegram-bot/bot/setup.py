"""
Bot + Dispatcher factory.

Single source of truth for how the bot is assembled.
Used by:
  - main.py           (long-polling mode — Replit / any VPS)
  - api/webhook.py    (serverless webhook mode — Vercel)
"""

from __future__ import annotations

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from config import Config
from bot.middlewares.db_middleware import DbSessionMiddleware
from bot.handlers import (
    start,
    group_events,
    message_filter,
    admin_commands,
    callbacks,
)
from bot.handlers import v4_settings
from bot.handlers import wordlist
from bot.handlers import donations
from bot.handlers import ai_admin


def create_bot(cfg: Config) -> Bot:
    """Instantiate a Bot with the project's default properties."""
    return Bot(
        token=cfg.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )


def create_dispatcher() -> Dispatcher:
    """
    Build a fully-wired Dispatcher.

    Router registration order matters:
      1. Lifecycle events (bot/member joins + leaves)
      2. /start — private dashboard
      3. V4 settings callbacks (must precede generic callbacks)
      4. Generic inline-button callbacks
      5. V5 donations (Telegram Stars) — pre_checkout_query / successful_payment
      6. Admin text commands (/ban, /mute, …)
      7. V4.1 word-list commands (/addword, …)
      8. V6: global Gemini key-manager commands (bot-owner only)
      9. Message filter — catches everything else (last)
    """
    dp = Dispatcher(storage=MemoryStorage())
    dp.update.middleware(DbSessionMiddleware())

    dp.include_router(group_events.router)
    dp.include_router(start.router)
    dp.include_router(v4_settings.router)
    dp.include_router(callbacks.router)
    dp.include_router(donations.router)
    dp.include_router(admin_commands.router)
    dp.include_router(wordlist.router)
    dp.include_router(ai_admin.router)
    dp.include_router(message_filter.router)

    return dp
