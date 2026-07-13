"""
Admin command handlers.
Commands work via reply (reply to target user's message) or
username/user_id argument.

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

Future: /kick, /promote, /demote, /slow_mode.
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
from database import repository as repo
from utils.helpers import escape_html, format_duration, mention_html, parse_duration
from utils.logger import get_logger

log = get_logger(__name__)
router = Router(name="admin_commands")

# All command handlers require the user to be a Telegram admin/creator
router.message.filter(IsGroupAdmin())


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _resolve_target(message: Message, bot: Bot) -> tuple[int, str] | None:
    """
    Return (user_id, display_name) of the target user.
    Priority: replied-to message > first command argument (user_id or @username).
    """
    if message.reply_to_message and message.reply_to_message.from_user:
        u = message.reply_to_message.from_user
        return u.id, u.first_name

    args = (message.text or "").split()
    if len(args) < 2:
        return None

    arg = args[1]
    # Numeric user ID
    if arg.lstrip("-").isdigit():
        uid = int(arg)
        return uid, str(uid)

    # @username
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
        await message.reply("❌ Reply to a message or provide a user ID/username.")
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
        r = f" — {escape_html(reason)}" if reason else ""
        await message.reply(f"🚫 {mention} has been banned{r}.", parse_mode="HTML")
    else:
        await message.reply("❌ Could not ban this user. Check my permissions.")


# ---------------------------------------------------------------------------
# /unban
# ---------------------------------------------------------------------------

@router.message(Command("unban"))
async def cmd_unban(message: Message, bot: Bot, session: AsyncSession) -> None:
    target = await _resolve_target(message, bot)
    if not target:
        await message.reply("❌ Reply to a message or provide a user ID.")
        return

    user_id, name = target
    success = await mod.unban_user(
        bot, session,
        chat_id=message.chat.id,
        user_id=user_id,
        actor_id=message.from_user.id,  # type: ignore[union-attr]
    )
    if success:
        await message.reply(f"✅ User <b>{escape_html(name)}</b> has been unbanned.", parse_mode="HTML")
    else:
        await message.reply("❌ Could not unban this user.")


# ---------------------------------------------------------------------------
# /mute
# ---------------------------------------------------------------------------

@router.message(Command("mute"))
async def cmd_mute(message: Message, bot: Bot, session: AsyncSession) -> None:
    target = await _resolve_target(message, bot)
    if not target:
        await message.reply("❌ Reply to a message or provide a user ID.")
        return

    user_id, name = target
    args = (message.text or "").split()

    # Try to parse duration from args[2]
    duration = 3600  # default 1 hour
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
        r = f" — {escape_html(reason)}" if reason else ""
        await message.reply(
            f"🔇 {mention} muted for <b>{format_duration(duration)}</b>{r}.",
            parse_mode="HTML",
        )
    else:
        await message.reply("❌ Could not mute this user. Check my permissions.")


# ---------------------------------------------------------------------------
# /unmute
# ---------------------------------------------------------------------------

@router.message(Command("unmute"))
async def cmd_unmute(message: Message, bot: Bot, session: AsyncSession) -> None:
    target = await _resolve_target(message, bot)
    if not target:
        await message.reply("❌ Reply to a message or provide a user ID.")
        return

    user_id, name = target
    success = await mod.unmute_user(
        bot, session,
        chat_id=message.chat.id,
        user_id=user_id,
        actor_id=message.from_user.id,  # type: ignore[union-attr]
    )
    if success:
        await message.reply(f"🔊 <b>{escape_html(name)}</b> has been unmuted.", parse_mode="HTML")
    else:
        await message.reply("❌ Could not unmute this user.")


# ---------------------------------------------------------------------------
# /warn
# ---------------------------------------------------------------------------

@router.message(Command("warn"))
async def cmd_warn(message: Message, bot: Bot, session: AsyncSession) -> None:
    target = await _resolve_target(message, bot)
    if not target:
        await message.reply("❌ Reply to a message or provide a user ID.")
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
    r = f"\n📝 Reason: {escape_html(reason)}" if reason else ""

    if punished:
        await message.reply(
            f"⚠️ {mention} received warning <b>{limit}/{limit}</b> and was automatically punished.{r}",
            parse_mode="HTML",
        )
    else:
        await message.reply(
            f"⚠️ {mention} warned — <b>{count}/{limit}</b>.{r}",
            parse_mode="HTML",
        )


# ---------------------------------------------------------------------------
# /resetwarns
# ---------------------------------------------------------------------------

@router.message(Command("resetwarns"))
async def cmd_resetwarns(message: Message, bot: Bot, session: AsyncSession) -> None:
    target = await _resolve_target(message, bot)
    if not target:
        await message.reply("❌ Reply to a message or provide a user ID.")
        return

    user_id, name = target
    await repo.reset_warnings(session, message.chat.id, user_id)
    await message.reply(
        f"🔄 Warnings reset for <b>{escape_html(name)}</b>.",
        parse_mode="HTML",
    )


# ---------------------------------------------------------------------------
# /del  — delete replied message
# ---------------------------------------------------------------------------

@router.message(Command("del"))
async def cmd_del(message: Message, bot: Bot, session: AsyncSession) -> None:
    if not message.reply_to_message:
        await message.reply("❌ Reply to the message you want to delete.")
        return

    target_msg = message.reply_to_message
    # Delete both the target and the command message
    success = await mod.delete_message_safe(
        bot, session,
        chat_id=message.chat.id,
        message_id=target_msg.message_id,
        actor_id=message.from_user.id,  # type: ignore[union-attr]
        reason="/del command",
    )
    if success:
        await mod.delete_message_safe(
            bot, session,
            chat_id=message.chat.id,
            message_id=message.message_id,
        )
    else:
        await message.reply("❌ Could not delete that message.")


# ---------------------------------------------------------------------------
# /pin
# ---------------------------------------------------------------------------

@router.message(Command("pin"))
async def cmd_pin(message: Message, bot: Bot, session: AsyncSession) -> None:
    if not message.reply_to_message:
        await message.reply("❌ Reply to the message you want to pin.")
        return

    success = await mod.pin_message(
        bot, session,
        chat_id=message.chat.id,
        message_id=message.reply_to_message.message_id,
        actor_id=message.from_user.id,  # type: ignore[union-attr]
    )
    if not success:
        await message.reply("❌ Could not pin that message.")


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
        await message.reply("❌ Reply to the message you want to unpin.")
        return

    success = await mod.unpin_message(
        bot, session,
        chat_id=message.chat.id,
        message_id=target_id,
        actor_id=message.from_user.id,  # type: ignore[union-attr]
    )
    if not success:
        await message.reply("❌ Could not unpin that message.")


# ---------------------------------------------------------------------------
# /info — display user information
# ---------------------------------------------------------------------------

@router.message(Command("info"))
async def cmd_info(message: Message, bot: Bot, session: AsyncSession) -> None:
    target = await _resolve_target(message, bot)
    if not target:
        # Default to self
        u = message.from_user
        if u:
            target = (u.id, u.first_name)
        else:
            await message.reply("❌ Could not resolve target user.")
            return

    user_id, _ = target
    db_user = await repo.get_user(session, user_id)
    warnings = await repo.get_warnings(session, message.chat.id, user_id)
    warn_count = warnings.count if warnings else 0

    try:
        member = await bot.get_chat_member(message.chat.id, user_id)
        status = member.status
        tg_user = member.user
        name = f"{tg_user.first_name}" + (f" {tg_user.last_name}" if tg_user.last_name else "")
        username = f"@{tg_user.username}" if tg_user.username else "—"
    except Exception:
        name = db_user.display_name() if db_user else str(user_id)
        username = f"@{db_user.username}" if db_user and db_user.username else "—"
        status = "unknown"

    text = (
        f"👤 <b>User Info</b>\n\n"
        f"🆔 ID: <code>{user_id}</code>\n"
        f"📛 Name: {escape_html(name)}\n"
        f"🔗 Username: {username}\n"
        f"🏷 Status: {status}\n"
        f"⚠️ Warnings: {warn_count}"
    )
    await message.reply(text, parse_mode="HTML")
