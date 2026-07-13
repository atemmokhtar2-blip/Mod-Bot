"""
Entry point for the Telegram Moderation Bot.

Boot sequence
-------------
1. Load config from environment variables
2. Set up logging
3. Initialise the database (create tables if not existing)
4. Build Bot + Dispatcher
5. Register middleware, routers, commands
6. Start long-polling

Future: swap long-polling for webhook when deploying to production server.
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
from utils.logger import get_logger, setup_logging


async def main() -> None:
    # ------------------------------------------------------------------
    # Config & logging
    # ------------------------------------------------------------------
    config = load_config()
    setup_logging(config.log_level)
    log = get_logger("main")
    log.info("Starting Telegram Moderation Bot…")

    # ------------------------------------------------------------------
    # Database
    # ------------------------------------------------------------------
    await init_db()

    # ------------------------------------------------------------------
    # Bot & Dispatcher
    # ------------------------------------------------------------------
    bot = Bot(
        token=config.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    # MemoryStorage is fine for V1 (FSM states survive until restart).
    # Future: replace with RedisStorage for multi-worker / persistent FSM.
    dp = Dispatcher(storage=MemoryStorage())

    # ------------------------------------------------------------------
    # Middleware — inject DB session into every handler
    # ------------------------------------------------------------------
    dp.update.middleware(DbSessionMiddleware())

    # ------------------------------------------------------------------
    # Routers — order matters:
    #   1. Lifecycle events (bot joins/leaves, member joins/leaves)
    #   2. Private-chat dashboard (start command)
    #   3. Callback queries (inline buttons)
    #   4. Admin commands (in-group text commands)
    #   5. Message filter (last — catches everything else)
    # ------------------------------------------------------------------
    dp.include_router(group_events.router)
    dp.include_router(start.router)
    dp.include_router(callbacks.router)
    dp.include_router(admin_commands.router)
    dp.include_router(message_filter.router)

    # ------------------------------------------------------------------
    # Bot commands menu (shown in Telegram UI)
    # ------------------------------------------------------------------
    from aiogram.types import BotCommand, BotCommandScopeAllGroupChats, BotCommandScopeAllPrivateChats

    private_commands = [
        BotCommand(command="start", description="Open the control panel"),
    ]
    group_commands = [
        BotCommand(command="ban",        description="Ban a user (reply)"),
        BotCommand(command="unban",      description="Unban a user"),
        BotCommand(command="mute",       description="Mute a user (reply) [duration]"),
        BotCommand(command="unmute",     description="Unmute a user (reply)"),
        BotCommand(command="warn",       description="Warn a user (reply)"),
        BotCommand(command="resetwarns", description="Reset user warnings (reply)"),
        BotCommand(command="del",        description="Delete a message (reply)"),
        BotCommand(command="pin",        description="Pin a message (reply)"),
        BotCommand(command="unpin",      description="Unpin a message (reply)"),
        BotCommand(command="info",       description="Show user info (reply)"),
    ]

    try:
        await bot.set_my_commands(private_commands, scope=BotCommandScopeAllPrivateChats())
        await bot.set_my_commands(group_commands, scope=BotCommandScopeAllGroupChats())
        log.info("Bot commands registered.")
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
            drop_pending_updates=True,   # ignore updates that arrived while bot was offline
        )
    finally:
        await bot.session.close()
        log.info("Bot stopped.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(0)
