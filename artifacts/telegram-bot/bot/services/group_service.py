"""
Group & channel registration service.
Called when the bot is added to / removed from a chat.
Future: add onboarding wizard, group-tier system.
"""

from __future__ import annotations

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest
from sqlalchemy.ext.asyncio import AsyncSession

from database import repository as repo
from utils.logger import get_logger

log = get_logger(__name__)


async def register_group(session: AsyncSession, bot: Bot, chat_id: int) -> None:
    """Fetch live chat info and upsert the group row with all defaults."""
    try:
        chat = await bot.get_chat(chat_id)
    except TelegramBadRequest as exc:
        log.error("Could not fetch chat %s: %s", chat_id, exc)
        return

    # Try to find the owner via chat.get_administrators()
    owner_id: int | None = None
    try:
        admins = await bot.get_chat_administrators(chat_id)
        for a in admins:
            if a.status == "creator":
                owner_id = a.user.id
                # Upsert the owner into users table
                await repo.upsert_user(
                    session,
                    user_id=a.user.id,
                    first_name=a.user.first_name,
                    last_name=a.user.last_name,
                    username=a.user.username,
                )
                break
        # Also upsert all admins
        for a in admins:
            if a.status == "administrator":
                await repo.upsert_user(
                    session,
                    user_id=a.user.id,
                    first_name=a.user.first_name,
                    last_name=a.user.last_name,
                    username=a.user.username,
                )
    except TelegramBadRequest as exc:
        log.warning("Could not fetch admins for %s: %s", chat_id, exc)

    await repo.upsert_group(
        session,
        group_id=chat_id,
        title=chat.title or str(chat_id),
        owner_id=owner_id,
        username=chat.username,
    )

    # Log the event
    await repo.add_log(
        session,
        group_id=chat_id,
        event_type="bot_added",
        details=f"Bot added to group '{chat.title}'",
    )

    log.info("Group registered: %s (%s), owner=%s", chat.title, chat_id, owner_id)


async def deregister_group(session: AsyncSession, chat_id: int) -> None:
    """Mark the group inactive when the bot is removed."""
    await repo.deactivate_group(session, chat_id)
    log.info("Group deactivated: %s", chat_id)


async def register_channel(session: AsyncSession, bot: Bot, channel_id: int) -> None:
    """Upsert a channel record when the bot gains admin access."""
    try:
        chat = await bot.get_chat(channel_id)
    except TelegramBadRequest as exc:
        log.error("Could not fetch channel %s: %s", channel_id, exc)
        return

    owner_id: int | None = None
    try:
        admins = await bot.get_chat_administrators(channel_id)
        for a in admins:
            if a.status == "creator":
                owner_id = a.user.id
                break
    except TelegramBadRequest:
        pass

    await repo.upsert_channel(
        session,
        channel_id=channel_id,
        title=chat.title or str(channel_id),
        username=chat.username,
        owner_id=owner_id,
    )
    log.info("Channel registered: %s (%s)", chat.title, channel_id)
