"""
Entry point — Version 4 (Advanced Settings & Administration).

Boot sequence
-------------
1. Load config from environment variables
2. Set up logging
3. Initialise the database (create/migrate tables)
4. Build Bot + Dispatcher
5. Register middleware, routers, commands (Arabic labels)
6. Start long-polling
"""

import asyncio
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from config import load_config
from database import init_db
from bot.middlewares.db_middleware import DbSessionMiddleware
from bot.handlers import (
    start,
    group_events,
    message_filter,
    admin_commands,
    callbacks,
)
from bot.handlers import v4_settings
from utils.logger import get_logger, setup_logging


async def main() -> None:
    # ------------------------------------------------------------------
    # Config & logging
    # ------------------------------------------------------------------
    config = load_config()
    setup_logging(config.log_level)
    log = get_logger("main")
    log.info("Starting Telegram Moderation Bot v4 (Advanced Settings & Administration)…")

    # ------------------------------------------------------------------
    # Database — create/migrate tables
    # ------------------------------------------------------------------
    await init_db()

    # ------------------------------------------------------------------
    # Bot & Dispatcher
    # ------------------------------------------------------------------
    bot = Bot(
        token=config.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    dp = Dispatcher(storage=MemoryStorage())

    # ------------------------------------------------------------------
    # Middleware — inject DB session into every handler
    # ------------------------------------------------------------------
    dp.update.middleware(DbSessionMiddleware())

    # ------------------------------------------------------------------
    # Routers — order matters:
    #   1. Lifecycle events (bot joins/leaves, member joins/leaves)
    #   2. Private-chat dashboard (/start)
    #   3. V4 Settings callbacks (before generic callbacks)
    #   4. Generic callback queries (inline buttons)
    #   5. Admin commands (in-group text commands)
    #   6. Message filter (last — catches everything else)
    # ------------------------------------------------------------------
    dp.include_router(group_events.router)
    dp.include_router(start.router)
    dp.include_router(v4_settings.router)   # V4 — registered before callbacks
    dp.include_router(callbacks.router)
    dp.include_router(admin_commands.router)
    dp.include_router(message_filter.router)

    # ------------------------------------------------------------------
    # Bot commands menu — Arabic labels shown in Telegram UI
    # ------------------------------------------------------------------
    from aiogram.types import BotCommand, BotCommandScopeAllGroupChats, BotCommandScopeAllPrivateChats

    private_commands = [
        BotCommand(command="start", description="فتح لوحة التحكم"),
    ]
    group_commands = [
        BotCommand(command="ban",        description="حظر مستخدم (بالرد)"),
        BotCommand(command="unban",      description="رفع الحظر"),
        BotCommand(command="mute",       description="كتم مستخدم (بالرد) [مدة]"),
        BotCommand(command="unmute",     description="رفع الكتم (بالرد)"),
        BotCommand(command="warn",       description="تحذير مستخدم (بالرد)"),
        BotCommand(command="resetwarns", description="إعادة تعيين التحذيرات"),
        BotCommand(command="del",        description="حذف رسالة (بالرد)"),
        BotCommand(command="pin",        description="تثبيت رسالة (بالرد)"),
        BotCommand(command="unpin",      description="إلغاء التثبيت"),
        BotCommand(command="info",       description="معلومات المستخدم (بالرد)"),
    ]

    try:
        await bot.set_my_commands(private_commands, scope=BotCommandScopeAllPrivateChats())
        await bot.set_my_commands(group_commands, scope=BotCommandScopeAllGroupChats())
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
