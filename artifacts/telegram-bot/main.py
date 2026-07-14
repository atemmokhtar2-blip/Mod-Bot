"""
Entry point — Version 4.1 (Advanced Profanity Filter).

Boot sequence
-------------
1. Load config from environment variables
2. Set up logging
3. Initialise the database (create / migrate tables)
4. Build Bot + Dispatcher  ← via bot/setup.py (shared with api/webhook.py)
5. Register bot commands (Arabic labels shown in Telegram UI)
6. Start long-polling

Run modes
---------
  Long-polling (default / Replit):
    python main.py

  To switch to webhook mode (Vercel):
    Delete the webhook → run scripts/setup_webhook.py --delete
    Then deploy to Vercel and run scripts/setup_webhook.py --url <url>
"""

import asyncio
import sys

from aiogram.types import BotCommand, BotCommandScopeAllGroupChats, BotCommandScopeAllPrivateChats

from config import load_config
from database import init_db
from bot.setup import create_bot, create_dispatcher
from utils.logger import get_logger, setup_logging


async def main() -> None:
    # ------------------------------------------------------------------
    # Config & logging
    # ------------------------------------------------------------------
    config = load_config()
    setup_logging(config.log_level)
    log = get_logger("main")
    log.info("Starting Telegram Moderation Bot v4.1 (Advanced Profanity Filter)…")

    # ------------------------------------------------------------------
    # Database — create / migrate tables
    # ------------------------------------------------------------------
    await init_db()

    # ------------------------------------------------------------------
    # Bot & Dispatcher  (shared factory — same setup used by webhook)
    # ------------------------------------------------------------------
    bot = create_bot(config)
    dp  = create_dispatcher()

    # ------------------------------------------------------------------
    # Bot commands menu — Arabic labels shown in Telegram UI
    # ------------------------------------------------------------------
    private_commands = [
        BotCommand(command="start", description="فتح لوحة التحكم"),
    ]
    group_commands = [
        BotCommand(command="ban",         description="حظر مستخدم (بالرد)"),
        BotCommand(command="unban",       description="رفع الحظر"),
        BotCommand(command="mute",        description="كتم مستخدم (بالرد) [مدة]"),
        BotCommand(command="unmute",      description="رفع الكتم (بالرد)"),
        BotCommand(command="warn",        description="تحذير مستخدم (بالرد)"),
        BotCommand(command="resetwarns",  description="إعادة تعيين التحذيرات"),
        BotCommand(command="del",         description="حذف رسالة (بالرد)"),
        BotCommand(command="pin",         description="تثبيت رسالة (بالرد)"),
        BotCommand(command="unpin",       description="إلغاء التثبيت"),
        BotCommand(command="info",        description="معلومات المستخدم (بالرد)"),
        BotCommand(command="addword",     description="إضافة كلمة محظورة [كلمة]"),
        BotCommand(command="removeword",  description="إزالة كلمة محظورة [كلمة]"),
        BotCommand(command="listwords",   description="عرض الكلمات المحظورة المخصصة"),
        BotCommand(command="clearwords",  description="مسح جميع الكلمات المخصصة (المالك فقط)"),
    ]

    # V6: Gemini key-manager commands are bot-owner-only and deliberately NOT
    # advertised in the public group/private command menus — they manage a
    # global, sensitive resource (API keys) and are only meant to be typed by
    # whoever is listed in BOT_OWNER_IDS. They still work when typed manually.

    try:
        await bot.set_my_commands(private_commands, scope=BotCommandScopeAllPrivateChats())
        await bot.set_my_commands(group_commands,   scope=BotCommandScopeAllGroupChats())
        log.info("Arabic bot commands registered.")
    except Exception as exc:
        log.warning("Could not set bot commands: %s", exc)

    # ------------------------------------------------------------------
    # Start polling
    # ------------------------------------------------------------------
    me = await bot.get_me()
    log.info("Bot @%s (id=%s) is running. Listening for updates…", me.username, me.id)

    try:
        await dp.start_polling(
            bot,
            allowed_updates=dp.resolve_used_update_types(),
            drop_pending_updates=True,
        )
    finally:
        await bot.session.close()
        log.info("Bot stopped.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(0)
