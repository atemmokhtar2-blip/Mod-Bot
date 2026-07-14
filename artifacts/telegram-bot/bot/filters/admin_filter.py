"""
Custom aiogram filters for permission checking.

IsGroupOwner  – passes only if the invoking user owns the group in the DB.
IsGroupAdmin  – passes if owner OR a registered admin in the DB.
IsBotAdmin    – passes if the bot itself is a Telegram admin in the chat.

Future: per-permission granular filters (can_ban, can_change_settings…).
"""

from __future__ import annotations

from aiogram.filters import BaseFilter
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from database import repository as repo
from utils.logger import get_logger

log = get_logger(__name__)


class IsGroupOwner(BaseFilter):
    """True if from_user is the owner of the group (stored in DB)."""

    async def __call__(self, event: Message | CallbackQuery, session: AsyncSession) -> bool:
        if isinstance(event, CallbackQuery):
            message = event.message
            user_id = event.from_user.id
            chat_id = message.chat.id if message else None
        else:
            user_id = event.from_user.id if event.from_user else None
            chat_id = event.chat.id

        if not user_id or not chat_id:
            return False

        group = await repo.get_group(session, chat_id)
        return group is not None and group.owner_id == user_id


class IsGroupAdmin(BaseFilter):
    """
    True if from_user is the group owner OR a Telegram admin/creator.
    Uses the live Telegram API (getChat) so it's always up-to-date.
    """

    async def __call__(self, event: Message | CallbackQuery, **data) -> bool:
        from aiogram import Bot

        if isinstance(event, CallbackQuery):
            message = event.message
            user_id = event.from_user.id
            chat_id = message.chat.id if message else None
        else:
            user_id = event.from_user.id if event.from_user else None
            chat_id = event.chat.id

        if not user_id or not chat_id or chat_id > 0:
            # Positive IDs are private chats — no concept of "admin" there
            return True

        bot: Bot = data["bot"]
        try:
            member = await bot.get_chat_member(chat_id, user_id)
            return member.status in ("administrator", "creator")
        except Exception as exc:
            log.warning("IsGroupAdmin check failed: %s", exc)
            return False


class IsBotAdmin(BaseFilter):
    """True if the bot has admin privileges in the chat."""

    async def __call__(self, event: Message, **data) -> bool:
        from aiogram import Bot

        bot: Bot = data["bot"]
        try:
            me = await bot.get_me()
            member = await bot.get_chat_member(event.chat.id, me.id)
            return member.status == "administrator"
        except Exception:
            return False


class IsBotOwner(BaseFilter):
    """
    V6: True if from_user.id is listed in BOT_OWNER_IDS (config.bot_owner_ids).

    This is a bot-wide (not per-group) permission, used to gate management of
    global resources such as the Gemini API key pool. Distinct from
    IsGroupOwner, which is scoped to a single group's owner_id in the DB.
    """

    async def __call__(self, event: Message | CallbackQuery, **data) -> bool:
        from config import load_config

        user = event.from_user
        if not user:
            return False
        config = load_config()
        return user.id in config.bot_owner_ids
