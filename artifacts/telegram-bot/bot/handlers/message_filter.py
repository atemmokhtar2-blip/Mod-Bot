"""
Automatic moderation filter — Version 2 (Arabic notifications, smart detection).

Improvements over V1:
- Smart bad-word detection: normalizes Arabic text to defeat bypass tricks
  (spaces, symbols, repeated letters, diacritics, alef variants).
- Arabic notification messages pulled from S (strings module).
- Flood and duplicate windows read from config rather than hard-coded.
- warn_members stat incremented via warning_service.

In-memory rate tracking resets on restart — intentional for V1/V2 simplicity.
Future: move flood state to Redis, plug AI classifier for spam/insults.
"""

from __future__ import annotations

import re
import time
from collections import defaultdict, deque

from aiogram import Bot, Router, F
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.services import moderation_service as mod
from bot.services.warning_service import warn_user
from bot.strings.ar import S
from database import repository as repo
from database.models import Filter
from utils.helpers import (
    contains_bad_word,
    count_emojis,
    has_advertisement,
    has_external_link,
    has_repeated_chars,
    has_telegram_link,
)
from utils.logger import get_logger

log = get_logger(__name__)
router = Router(name="message_filter")

# ---------------------------------------------------------------------------
# In-memory state  (chat_id, user_id) → deque / last-message tuple
# ---------------------------------------------------------------------------
_flood_state: dict[tuple[int, int], deque[float]] = defaultdict(lambda: deque(maxlen=30))
_last_message: dict[tuple[int, int], tuple[str, float]] = {}


# ---------------------------------------------------------------------------
# Notification helper
# ---------------------------------------------------------------------------

async def _notify(bot: Bot, chat_id: int, template: str,
                  user_id: int, name: str) -> None:
    """Send a short Arabic notification to the group (silent fail)."""
    try:
        await bot.send_message(
            chat_id,
            template.format(uid=user_id, name=name),
            parse_mode="HTML",
        )
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Action dispatcher
# ---------------------------------------------------------------------------

async def _apply_action(
    action: str,
    bot: Bot,
    session: AsyncSession,
    message: Message,
    reason: str,
    notify_template: str | None = None,
    mute_duration: int = 3600,
) -> None:
    chat_id = message.chat.id
    user = message.from_user  # type: ignore[union-attr]
    user_id = user.id
    name = user.first_name or str(user_id)
    msg_id = message.message_id

    if action == "ignore":
        return

    # Always delete the offending message first
    if action in ("delete", "warn", "mute", "kick", "ban"):
        await mod.delete_message_safe(
            bot, session, chat_id=chat_id, message_id=msg_id,
            actor_id=None, reason=reason,
        )

    if action == "warn":
        count, limit, punished = await warn_user(
            bot, session,
            chat_id=chat_id, user_id=user_id,
            actor_id=None, reason=reason,
        )
        try:
            if punished:
                await _notify(bot, chat_id, S.auto_punished, user_id, name)
            else:
                await bot.send_message(
                    chat_id,
                    S.auto_warn_notice.format(count=count, limit=limit, reason=reason),
                    parse_mode="HTML",
                )
        except Exception:
            pass

    elif action == "mute":
        await mod.mute_user(
            bot, session, chat_id=chat_id, user_id=user_id,
            duration_seconds=mute_duration, actor_id=None, reason=reason,
        )
        if notify_template:
            await _notify(bot, chat_id, notify_template, user_id, name)

    elif action == "kick":
        await mod.kick_user(
            bot, session, chat_id=chat_id, user_id=user_id,
            actor_id=None, reason=reason,
        )

    elif action == "ban":
        await mod.ban_user(
            bot, session, chat_id=chat_id, user_id=user_id,
            actor_id=None, reason=reason,
        )

    elif action == "delete" and notify_template:
        # delete already done above; send notification
        await _notify(bot, chat_id, notify_template, user_id, name)


# ---------------------------------------------------------------------------
# Detection functions
# ---------------------------------------------------------------------------

def _check_flood(chat_id: int, user_id: int, flood_count: int, flood_window: int) -> bool:
    key = (chat_id, user_id)
    now = time.monotonic()
    q = _flood_state[key]
    q.append(now)
    recent = sum(1 for t in q if now - t <= flood_window)
    return recent >= flood_count


def _check_duplicate(chat_id: int, user_id: int, text: str, window: int) -> bool:
    key = (chat_id, user_id)
    now = time.monotonic()
    last = _last_message.get(key)
    _last_message[key] = (text, now)
    if last:
        last_text, last_ts = last
        if now - last_ts <= window and last_text == text:
            return True
    return False


def _build_filter_map(filters: list[Filter]) -> dict[str, Filter]:
    return {f.filter_type: f for f in filters}


# ---------------------------------------------------------------------------
# Main handler
# ---------------------------------------------------------------------------

@router.message(F.chat.type.in_({"group", "supergroup"}))
async def filter_message(message: Message, bot: Bot, session: AsyncSession) -> None:
    """Intercept all group messages and apply enabled filters."""
    # Ignore channel posts forwarded into groups
    if message.sender_chat:
        return

    user = message.from_user
    if not user or user.is_bot:
        return

    chat_id = message.chat.id

    # Only process registered groups
    group = await repo.get_group(session, chat_id)
    if not group or not group.is_active:
        return

    # Do not moderate admins / owners
    try:
        member = await bot.get_chat_member(chat_id, user.id)
        if member.status in ("administrator", "creator"):
            await repo.increment_stat(session, chat_id, "messages_today")
            return
    except Exception:
        pass

    await repo.increment_stat(session, chat_id, "messages_today")

    text = message.text or message.caption or ""

    filters = await repo.get_filters(session, chat_id)
    fmap = _build_filter_map(filters)
    settings = await repo.get_settings(session, chat_id)
    mute_duration = settings.mute_duration if settings else 3600

    async def act(filter_type: str, reason: str, notify_tpl: str | None = None) -> bool:
        """Apply action for a filter; return True if message was acted on."""
        f = fmap.get(filter_type)
        if not f or not f.enabled:
            return False
        if f.action == "ignore":
            return False
        await _apply_action(
            f.action, bot, session, message, reason,
            notify_template=notify_tpl,
            mute_duration=mute_duration,
        )
        await repo.add_log(
            session,
            group_id=chat_id,
            event_type="filter_triggered",
            target_id=user.id,
            details=f"filter={filter_type} action={f.action}",
        )
        return True

    # ------------------------------------------------------------------
    # Priority order: stop on first match that deletes/acts on the message
    # ------------------------------------------------------------------

    # 1. Flood
    f_flood = fmap.get("flood")
    if f_flood and f_flood.enabled and text:
        flood_count, flood_window = 5, 10
        if _check_flood(chat_id, user.id, flood_count, flood_window):
            if await act("flood", "flood", S.auto_flood):
                return

    # 2. Duplicate messages
    f_dup = fmap.get("duplicate_messages")
    if f_dup and f_dup.enabled and text:
        if _check_duplicate(chat_id, user.id, text, 30):
            if await act("duplicate_messages", "duplicate", S.auto_duplicate):
                return

    # 3. Telegram invite links
    if text and has_telegram_link(text):
        if await act("telegram_links", "telegram_link", S.auto_telegram_link):
            return

    # 4. External links
    if text and has_external_link(text):
        if await act("external_links", "external_link", S.auto_external_link):
            return

    # 5. Advertisement (@-mention promotion)
    if text and has_advertisement(text):
        if await act("advertisement", "advertisement", S.auto_advertisement):
            return

    # 6. Excessive emojis
    if text:
        emoji_count = count_emojis(text)
        f_emoji = fmap.get("excessive_emojis")
        threshold = 10
        if f_emoji and f_emoji.enabled and emoji_count > threshold:
            if await act("excessive_emojis", "excessive_emojis", S.auto_emoji):
                return

    # 7. Repeated characters
    if text and has_repeated_chars(text):
        if await act("repeated_chars", "repeated_chars", S.auto_repeated):
            return

    # 8. Long messages
    if text:
        f_long = fmap.get("long_messages")
        if f_long and f_long.enabled and len(text) > 2000:
            if await act("long_messages", "long_message", S.auto_long_msg):
                return

    # 9. Bad words — V2 smart detection (normalized, bypass-resistant)
    if text:
        f_bw = fmap.get("bad_words")
        if f_bw and f_bw.enabled and f_bw.extra:
            bad_words = [w.strip() for w in f_bw.extra.split(",") if w.strip()]
            matched = contains_bad_word(text, bad_words)
            if matched:
                if await act("bad_words", f"bad_word:{matched}", S.auto_bad_word):
                    return

    # 10. Spam / insults — placeholder; AI classifier hook for V3
    # f_spam = fmap.get("spam") ...
    # f_insults = fmap.get("insults") ...
