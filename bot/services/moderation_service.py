"""
Core moderation actions: ban, unban, mute, unmute, kick, delete, pin.

All actions:
  1. Execute the Telegram API call.
  2. Write an audit log entry.
  3. Increment the relevant statistic.

Future: timed-ban expiry via scheduler, appeal system, AI-assisted review.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.types import ChatPermissions
from sqlalchemy.ext.asyncio import AsyncSession

from database import repository as repo
from utils.helpers import mention_html
from utils.logger import get_logger

log = get_logger(__name__)

# Fully restricted permissions (muted)
_MUTED_PERMISSIONS = ChatPermissions(
    can_send_messages=False,
    can_send_media_messages=False,
    can_send_polls=False,
    can_send_other_messages=False,
    can_add_web_page_previews=False,
)

# Full permissions (unmuted)
_FULL_PERMISSIONS = ChatPermissions(
    can_send_messages=True,
    can_send_media_messages=True,
    can_send_polls=True,
    can_send_other_messages=True,
    can_add_web_page_previews=True,
)


async def ban_user(
    bot: Bot,
    session: AsyncSession,
    *,
    chat_id: int,
    user_id: int,
    actor_id: int | None = None,
    reason: str | None = None,
    revoke_messages: bool = False,
) -> bool:
    """Permanently ban a user from the group. Returns True on success."""
    try:
        await bot.ban_chat_member(
            chat_id,
            user_id,
            revoke_messages=revoke_messages,
        )
        await repo.add_log(
            session,
            group_id=chat_id,
            event_type="user_banned",
            actor_id=actor_id,
            target_id=user_id,
            details=reason,
        )
        await repo.increment_stat(session, chat_id, "banned_members")
        log.info("Banned user %s in chat %s (actor=%s)", user_id, chat_id, actor_id)
        return True
    except (TelegramBadRequest, TelegramForbiddenError) as exc:
        log.warning("Ban failed: %s", exc)
        return False


async def unban_user(
    bot: Bot,
    session: AsyncSession,
    *,
    chat_id: int,
    user_id: int,
    actor_id: int | None = None,
) -> bool:
    try:
        await bot.unban_chat_member(chat_id, user_id, only_if_banned=True)
        await repo.add_log(
            session,
            group_id=chat_id,
            event_type="user_unbanned",
            actor_id=actor_id,
            target_id=user_id,
        )
        return True
    except (TelegramBadRequest, TelegramForbiddenError) as exc:
        log.warning("Unban failed: %s", exc)
        return False


async def mute_user(
    bot: Bot,
    session: AsyncSession,
    *,
    chat_id: int,
    user_id: int,
    duration_seconds: int,
    actor_id: int | None = None,
    reason: str | None = None,
) -> bool:
    """Restrict a user so they cannot send messages for *duration_seconds*."""
    until = datetime.now(timezone.utc) + timedelta(seconds=duration_seconds)
    try:
        await bot.restrict_chat_member(
            chat_id,
            user_id,
            permissions=_MUTED_PERMISSIONS,
            until_date=until,
        )
        await repo.add_log(
            session,
            group_id=chat_id,
            event_type="user_muted",
            actor_id=actor_id,
            target_id=user_id,
            details=f"duration={duration_seconds}s reason={reason}",
        )
        await repo.increment_stat(session, chat_id, "muted_members")
        log.info("Muted user %s in chat %s for %ss", user_id, chat_id, duration_seconds)
        return True
    except (TelegramBadRequest, TelegramForbiddenError) as exc:
        log.warning("Mute failed: %s", exc)
        return False


async def unmute_user(
    bot: Bot,
    session: AsyncSession,
    *,
    chat_id: int,
    user_id: int,
    actor_id: int | None = None,
) -> bool:
    try:
        await bot.restrict_chat_member(
            chat_id,
            user_id,
            permissions=_FULL_PERMISSIONS,
        )
        await repo.add_log(
            session,
            group_id=chat_id,
            event_type="user_unmuted",
            actor_id=actor_id,
            target_id=user_id,
        )
        return True
    except (TelegramBadRequest, TelegramForbiddenError) as exc:
        log.warning("Unmute failed: %s", exc)
        return False


async def kick_user(
    bot: Bot,
    session: AsyncSession,
    *,
    chat_id: int,
    user_id: int,
    actor_id: int | None = None,
    reason: str | None = None,
) -> bool:
    """Kick (ban then immediately unban) so the user can rejoin."""
    try:
        await bot.ban_chat_member(chat_id, user_id)
        await bot.unban_chat_member(chat_id, user_id)
        await repo.add_log(
            session,
            group_id=chat_id,
            event_type="user_banned",  # kick is a temporary ban
            actor_id=actor_id,
            target_id=user_id,
            details=f"kick reason={reason}",
        )
        return True
    except (TelegramBadRequest, TelegramForbiddenError) as exc:
        log.warning("Kick failed: %s", exc)
        return False


async def delete_message_safe(
    bot: Bot,
    session: AsyncSession,
    *,
    chat_id: int,
    message_id: int,
    actor_id: int | None = None,
    reason: str | None = None,
) -> bool:
    try:
        await bot.delete_message(chat_id, message_id)
        await repo.add_log(
            session,
            group_id=chat_id,
            event_type="message_deleted",
            actor_id=actor_id,
            details=f"msg_id={message_id} reason={reason}",
        )
        await repo.increment_stat(session, chat_id, "deleted_messages")
        return True
    except (TelegramBadRequest, TelegramForbiddenError) as exc:
        log.warning("Delete message failed: %s", exc)
        return False


async def pin_message(
    bot: Bot,
    session: AsyncSession,
    *,
    chat_id: int,
    message_id: int,
    actor_id: int | None = None,
    disable_notification: bool = False,
) -> bool:
    try:
        await bot.pin_chat_message(
            chat_id,
            message_id,
            disable_notification=disable_notification,
        )
        await repo.add_log(
            session,
            group_id=chat_id,
            event_type="message_pinned",
            actor_id=actor_id,
            details=f"msg_id={message_id}",
        )
        return True
    except (TelegramBadRequest, TelegramForbiddenError) as exc:
        log.warning("Pin failed: %s", exc)
        return False


async def unpin_message(
    bot: Bot,
    session: AsyncSession,
    *,
    chat_id: int,
    message_id: int,
    actor_id: int | None = None,
) -> bool:
    try:
        await bot.unpin_chat_message(chat_id, message_id)
        await repo.add_log(
            session,
            group_id=chat_id,
            event_type="message_unpinned",
            actor_id=actor_id,
            details=f"msg_id={message_id}",
        )
        return True
    except (TelegramBadRequest, TelegramForbiddenError) as exc:
        log.warning("Unpin failed: %s", exc)
        return False
