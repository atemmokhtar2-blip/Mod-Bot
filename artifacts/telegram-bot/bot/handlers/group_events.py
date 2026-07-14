"""
Lifecycle event handlers — Version 4 (Goodbye message support).

Events:
  - Bot added to / removed from a group or channel
  - Bot receives admin permissions → beautiful activation message with deep link
  - New member joins a group (welcome message)
  - Member leaves a group (goodbye message + log)  ← V4
"""

from __future__ import annotations

from aiogram import Bot, Router
from aiogram.filters import ChatMemberUpdatedFilter, IS_MEMBER, IS_NOT_MEMBER
from aiogram.types import ChatMemberUpdated
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.builder import manage_group_url_kb
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
    chat = event.chat
    chat_type = chat.type
    inviter_id = event.from_user.id if event.from_user else None

    log.info("bot_added: chat_id=%s chat_type=%s inviter=%s", chat.id, chat_type, inviter_id)

    if chat_type in ("group", "supergroup"):
        await register_group(session, bot, chat.id, added_by_user_id=inviter_id)
        try:
            me = await bot.get_me()
            await bot.send_message(
                chat.id,
                S.bot_activation_msg,
                parse_mode="HTML",
                reply_markup=manage_group_url_kb(chat.id, me.username),
            )
        except Exception as exc:
            log.warning("Could not send activation message to group %s: %s", chat.id, exc)

    elif chat_type == "channel":
        await register_channel(session, bot, chat.id)
        log.info("Bot joined channel %s", chat.id)


@router.my_chat_member()
async def bot_member_status_changed(event: ChatMemberUpdated, bot: Bot, session: AsyncSession) -> None:
    chat = event.chat
    if chat.type not in ("group", "supergroup"):
        return

    old_status = event.old_chat_member.status
    new_status = event.new_chat_member.status
    actor_id = event.from_user.id if event.from_user else None

    if old_status in ("member", "restricted") and new_status == "administrator":
        log.info(
            "bot_added: chat_id=%s promoted to administrator by=%s — re-registering to sync owner/admins",
            chat.id, actor_id,
        )
        # V8 fix: re-run registration on promotion too. Being added as a plain
        # member doesn't expose the admin list reliably; once the bot becomes
        # an admin we can see the real admin list and must (re)save it so the
        # private panel finds the group immediately — never re-ask to add it.
        await register_group(session, bot, chat.id, added_by_user_id=actor_id)
        try:
            me = await bot.get_me()
            await bot.send_message(
                chat.id,
                S.bot_activation_msg,
                parse_mode="HTML",
                reply_markup=manage_group_url_kb(chat.id, me.username),
            )
        except Exception as exc:
            log.warning("Could not send admin-promotion message in group %s: %s", chat.id, exc)


@router.my_chat_member(ChatMemberUpdatedFilter(IS_MEMBER >> IS_NOT_MEMBER))
async def bot_left_chat(event: ChatMemberUpdated, session: AsyncSession) -> None:
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
# Member leaves  — V4: goodbye message
# ---------------------------------------------------------------------------

@router.chat_member(ChatMemberUpdatedFilter(IS_MEMBER >> IS_NOT_MEMBER))
async def member_left(event: ChatMemberUpdated, bot: Bot, session: AsyncSession) -> None:
    user = event.old_chat_member.user
    chat_id = event.chat.id

    if user.is_bot:
        return

    await repo.add_log(
        session,
        group_id=chat_id,
        event_type="user_left",
        target_id=user.id,
        details=f"غادر {user.first_name}",
    )

    # V4: send goodbye message if enabled
    settings = await repo.get_settings(session, chat_id)
    if settings and settings.goodbye_enabled:
        try:
            chat = await bot.get_chat(chat_id)
            text = format_welcome(
                settings.goodbye_text,
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
            log.warning("Goodbye message failed in %s: %s", chat_id, exc)
