"""
Admin command handlers — Version 2 (Arabic responses).

Commands
--------
/ban [reason]
/unban [user_id]
/mute [duration] [reason]   e.g. /mute 2h spamming
/unmute
/warn [reason]
/resetwarns
/del   – delete replied message
/pin   – pin replied message
/unpin – unpin replied message
/info  – show member info

Future: /kick, /promote, /demote, /slow_mode, /warn_history.
"""

from __future__ import annotations

import re

from aiogram import Bot, Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.filters.admin_filter import IsGroupAdmin
from bot.services import moderation_service as mod
from bot.services.warning_service import warn_user
from bot.strings.ar import S
from database import repository as repo
from utils.helpers import (
    escape_html,
    format_datetime_ar,
    format_duration,
    mention_html,
    parse_duration,
)
from utils.logger import get_logger

log = get_logger(__name__)
router = Router(name="admin_commands")

router.message.filter(IsGroupAdmin())


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _resolve_target(message: Message, bot: Bot) -> tuple[int, str] | None:
    """Return (user_id, display_name) of the target user."""
    if message.reply_to_message and message.reply_to_message.from_user:
        u = message.reply_to_message.from_user
        return u.id, u.first_name

    args = (message.text or "").split()
    if len(args) < 2:
        return None

    arg = args[1]
    if arg.lstrip("-").isdigit():
        uid = int(arg)
        return uid, str(uid)

    if arg.startswith("@"):
        username = arg[1:]
        try:
            chat = await bot.get_chat(f"@{username}")
            return chat.id, chat.first_name or chat.title or username
        except Exception:
            return None

    return None


def _extract_reason(message: Message, offset: int = 2) -> str | None:
    parts = (message.text or "").split(maxsplit=offset)
    return parts[-1] if len(parts) > offset - 1 else None


# ---------------------------------------------------------------------------
# /ban
# ---------------------------------------------------------------------------

@router.message(Command("ban"))
async def cmd_ban(message: Message, bot: Bot, session: AsyncSession) -> None:
    target = await _resolve_target(message, bot)
    if not target:
        await message.reply(S.cmd_need_target)
        return

    user_id, name = target
    reason = _extract_reason(message)

    success = await mod.ban_user(
        bot, session,
        chat_id=message.chat.id,
        user_id=user_id,
        actor_id=message.from_user.id,  # type: ignore[union-attr]
        reason=reason,
    )
    if success:
        mention = mention_html(user_id, name)
        r = S.cmd_reason_prefix.format(reason=escape_html(reason)) if reason else ""
        await message.reply(S.cmd_ban_ok.format(mention=mention, reason=r), parse_mode="HTML")
    else:
        await message.reply(S.cmd_ban_fail)


# ---------------------------------------------------------------------------
# /unban
# ---------------------------------------------------------------------------

@router.message(Command("unban"))
async def cmd_unban(message: Message, bot: Bot, session: AsyncSession) -> None:
    target = await _resolve_target(message, bot)
    if not target:
        await message.reply(S.cmd_need_target)
        return

    user_id, name = target
    success = await mod.unban_user(
        bot, session,
        chat_id=message.chat.id,
        user_id=user_id,
        actor_id=message.from_user.id,  # type: ignore[union-attr]
    )
    if success:
        await message.reply(S.cmd_unban_ok.format(name=escape_html(name)), parse_mode="HTML")
    else:
        await message.reply(S.cmd_unban_fail)


# ---------------------------------------------------------------------------
# /mute
# ---------------------------------------------------------------------------

@router.message(Command("mute"))
async def cmd_mute(message: Message, bot: Bot, session: AsyncSession) -> None:
    target = await _resolve_target(message, bot)
    if not target:
        await message.reply(S.cmd_need_target)
        return

    user_id, name = target
    args = (message.text or "").split()

    duration = 3600
    reason_start = 2
    if len(args) > 2:
        parsed = parse_duration(args[2])
        if parsed:
            duration = parsed
            reason_start = 3

    reason_parts = args[reason_start:]
    reason = " ".join(reason_parts) if reason_parts else None

    success = await mod.mute_user(
        bot, session,
        chat_id=message.chat.id,
        user_id=user_id,
        duration_seconds=duration,
        actor_id=message.from_user.id,  # type: ignore[union-attr]
        reason=reason,
    )
    if success:
        mention = mention_html(user_id, name)
        r = S.cmd_reason_prefix.format(reason=escape_html(reason)) if reason else ""
        await message.reply(
            S.cmd_mute_ok.format(mention=mention, duration=format_duration(duration), reason=r),
            parse_mode="HTML",
        )
    else:
        await message.reply(S.cmd_mute_fail)


# ---------------------------------------------------------------------------
# /unmute
# ---------------------------------------------------------------------------

@router.message(Command("unmute"))
async def cmd_unmute(message: Message, bot: Bot, session: AsyncSession) -> None:
    target = await _resolve_target(message, bot)
    if not target:
        await message.reply(S.cmd_need_target)
        return

    user_id, name = target
    success = await mod.unmute_user(
        bot, session,
        chat_id=message.chat.id,
        user_id=user_id,
        actor_id=message.from_user.id,  # type: ignore[union-attr]
    )
    if success:
        await message.reply(S.cmd_unmute_ok.format(name=escape_html(name)), parse_mode="HTML")
    else:
        await message.reply(S.cmd_unmute_fail)


# ---------------------------------------------------------------------------
# /warn
# ---------------------------------------------------------------------------

@router.message(Command("warn"))
async def cmd_warn(message: Message, bot: Bot, session: AsyncSession) -> None:
    target = await _resolve_target(message, bot)
    if not target:
        await message.reply(S.cmd_need_target)
        return

    user_id, name = target
    reason = _extract_reason(message)

    count, limit, punished = await warn_user(
        bot, session,
        chat_id=message.chat.id,
        user_id=user_id,
        actor_id=message.from_user.id,  # type: ignore[union-attr]
        reason=reason,
    )
    mention = mention_html(user_id, name)
    r = S.cmd_reason_prefix.format(reason=escape_html(reason)) if reason else ""

    if punished:
        await message.reply(
            S.cmd_warn_punished.format(mention=mention, limit=limit, reason=r),
            parse_mode="HTML",
        )
    else:
        await message.reply(
            S.cmd_warn_ok.format(mention=mention, count=count, limit=limit, reason=r),
            parse_mode="HTML",
        )


# ---------------------------------------------------------------------------
# /resetwarns
# ---------------------------------------------------------------------------

@router.message(Command("resetwarns"))
async def cmd_resetwarns(message: Message, bot: Bot, session: AsyncSession) -> None:
    target = await _resolve_target(message, bot)
    if not target:
        await message.reply(S.cmd_need_target)
        return

    user_id, name = target
    await repo.reset_warnings(session, message.chat.id, user_id)
    await message.reply(S.cmd_resetwarns_ok.format(name=escape_html(name)), parse_mode="HTML")


# ---------------------------------------------------------------------------
# /del  — delete replied message
# ---------------------------------------------------------------------------

@router.message(Command("del"))
async def cmd_del(message: Message, bot: Bot, session: AsyncSession) -> None:
    if not message.reply_to_message:
        await message.reply(S.cmd_del_need_reply)
        return

    target_msg = message.reply_to_message
    success = await mod.delete_message_safe(
        bot, session,
        chat_id=message.chat.id,
        message_id=target_msg.message_id,
        actor_id=message.from_user.id,  # type: ignore[union-attr]
        reason="أمر /del",
    )
    if success:
        await mod.delete_message_safe(
            bot, session,
            chat_id=message.chat.id,
            message_id=message.message_id,
        )
    else:
        await message.reply(S.cmd_del_fail)


# ---------------------------------------------------------------------------
# /pin
# ---------------------------------------------------------------------------

@router.message(Command("pin"))
async def cmd_pin(message: Message, bot: Bot, session: AsyncSession) -> None:
    if not message.reply_to_message:
        await message.reply(S.cmd_pin_need_reply)
        return

    success = await mod.pin_message(
        bot, session,
        chat_id=message.chat.id,
        message_id=message.reply_to_message.message_id,
        actor_id=message.from_user.id,  # type: ignore[union-attr]
    )
    if not success:
        await message.reply(S.cmd_pin_fail)


# ---------------------------------------------------------------------------
# /unpin
# ---------------------------------------------------------------------------

@router.message(Command("unpin"))
async def cmd_unpin(message: Message, bot: Bot, session: AsyncSession) -> None:
    target_id = (
        message.reply_to_message.message_id
        if message.reply_to_message
        else None
    )
    if not target_id:
        await message.reply(S.cmd_unpin_need_reply)
        return

    success = await mod.unpin_message(
        bot, session,
        chat_id=message.chat.id,
        message_id=target_id,
        actor_id=message.from_user.id,  # type: ignore[union-attr]
    )
    if not success:
        await message.reply(S.cmd_unpin_fail)


# ---------------------------------------------------------------------------
# /info — display user information
# ---------------------------------------------------------------------------

@router.message(Command("info"))
async def cmd_info(message: Message, bot: Bot, session: AsyncSession) -> None:
    target = await _resolve_target(message, bot)
    if not target:
        u = message.from_user
        if u:
            target = (u.id, u.first_name)
        else:
            await message.reply(S.cmd_info_fail)
            return

    user_id, _ = target
    db_user = await repo.get_user(session, user_id)
    warnings = await repo.get_warnings(session, message.chat.id, user_id)
    warn_count = warnings.count if warnings else 0
    last_warn_dt = (
        format_datetime_ar(warnings.last_warned_at)
        if warnings and warnings.last_warned_at else "—"
    )

    # Status map → Arabic labels
    status_map = {
        "creator": "مالك المجموعة 👑",
        "administrator": "مشرف 👮",
        "member": "عضو",
        "restricted": "مقيّد 🔇",
        "left": "غادر",
        "kicked": "محظور 🚫",
        "unknown": S.unknown,
    }

    try:
        member = await bot.get_chat_member(message.chat.id, user_id)
        tg_user = member.user
        status_ar = status_map.get(member.status, member.status)
        name = tg_user.first_name + (f" {tg_user.last_name}" if tg_user.last_name else "")
        username = f"@{tg_user.username}" if tg_user.username else "—"
    except Exception:
        name = db_user.display_name() if db_user else str(user_id)
        username = f"@{db_user.username}" if db_user and db_user.username else "—"
        status_ar = S.unknown

    text = S.cmd_info_text.format(
        uid=user_id,
        name=escape_html(name),
        username=username,
        status=status_ar,
        warns=warn_count,
        last_warn=last_warn_dt,
    )
    await message.reply(text, parse_mode="HTML")
