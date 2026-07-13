"""
Lifecycle event handlers — Arabic UI (V2).

Events:
  - Bot added to / removed from a group or channel
  - New member joins a group (welcome message)
  - Member leaves a group (log)

Future: anti-raid join throttling, CAPTCHA verification.
"""

from __future__ import annotations

from aiogram import Bot, Router
from aiogram.filters import ChatMemberUpdatedFilter, IS_MEMBER, IS_NOT_MEMBER
from aiogram.types import ChatMemberUpdated
from sqlalchemy.ext.asyncio import AsyncSession

from bot.services.group_service import (
    deregister_group,
    register_channel,
    register_group,
)
from bot.strings.ar import S
from database import repository as repo
from utils.helpers import format_welcome, mention_html
from utils.logger import get_logger

log = get_logger(__name__)
router = Router(name="group_events")


# ---------------------------------------------------------------------------
# Bot added to / removed from a group
# ---------------------------------------------------------------------------

@router.my_chat_member(ChatMemberUpdatedFilter(IS_NOT_MEMBER >> IS_MEMBER))
async def bot_joined_chat(event: ChatMemberUpdated, bot: Bot, session: AsyncSession) -> None:
    """Fired when the bot itself joins a group or channel."""
    chat = event.chat
    chat_type = chat.type

    if chat_type in ("group", "supergroup"):
        await register_group(session, bot, chat.id)
        try:
            await bot.send_message(
                chat.id,
                S.bot_joined_msg,
                parse_mode="HTML",
            )
        except Exception as exc:
            log.warning("Could not send welcome to group %s: %s", chat.id, exc)

    elif chat_type == "channel":
        await register_channel(session, bot, chat.id)
        log.info("Bot joined channel %s", chat.id)


@router.my_chat_member(ChatMemberUpdatedFilter(IS_MEMBER >> IS_NOT_MEMBER))
async def bot_left_chat(event: ChatMemberUpdated, session: AsyncSession) -> None:
    """Fired when the bot is removed from a group."""
    chat = event.chat
    if chat.type in ("group", "supergroup"):
        await deregister_group(session, chat.id)
    log.info("Bot removed from chat %s", chat.id)


# ---------------------------------------------------------------------------
# New member joins
# ---------------------------------------------------------------------------

@router.chat_member(ChatMemberUpdatedFilter(IS_NOT_MEMBER >> IS_MEMBER))
async def new_member_joined(event: ChatMemberUpdated, bot: Bot, session: AsyncSession) -> None:
    """Send a welcome message if enabled; log the join event."""
    chat_id = event.chat.id
    user = event.new_chat_member.user

    if user.is_bot:
        return

    await repo.upsert_user(
        session,
        user_id=user.id,
        first_name=user.first_name,
        last_name=user.last_name,
        username=user.username,
    )

    await repo.add_log(
        session,
        group_id=chat_id,
        event_type="user_joined",
        target_id=user.id,
        details=f"انضم {user.first_name}",
    )

    settings = await repo.get_settings(session, chat_id)
    if settings and settings.welcome_enabled:
        try:
            chat = await bot.get_chat(chat_id)
            text = format_welcome(
                settings.welcome_text,
                first_name=user.first_name,
                username=user.username,
                group_name=chat.title or "",
            )
            mention = mention_html(user.id, user.first_name)
            await bot.send_message(
                chat_id,
                f"{mention}، {text}",
                parse_mode="HTML",
            )
        except Exception as exc:
            log.warning("Welcome message failed in %s: %s", chat_id, exc)


# ---------------------------------------------------------------------------
# Member leaves
# ---------------------------------------------------------------------------

@router.chat_member(ChatMemberUpdatedFilter(IS_MEMBER >> IS_NOT_MEMBER))
async def member_left(event: ChatMemberUpdated, session: AsyncSession) -> None:
    user = event.old_chat_member.user
    if user.is_bot:
        return

    await repo.add_log(
        session,
        group_id=event.chat.id,
        event_type="user_left",
        target_id=user.id,
        details=f"غادر {user.first_name}",
    )
