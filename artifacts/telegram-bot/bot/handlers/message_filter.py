"""
Automatic moderation filter — runs on every group message.

Detection logic is cheap and deterministic (no external calls).
For each triggered filter, applies the configured action via the
moderation / warning services.

In-memory rate tracking for flood and duplicate detection resets on
bot restart; this is intentional for V1 simplicity.
Future: move flood state to Redis for multi-worker setups, add AI pass.
"""

from __future__ import annotations

import asyncio
import re
import time
from collections import defaultdict, deque

from aiogram import Bot, Router, F
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.services import moderation_service as mod
from bot.services.warning_service import warn_user
from database import repository as repo
from database.models import Filter
from utils.helpers import (
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
# In-memory state for flood / duplicate detection
# key: (chat_id, user_id) → deque of timestamps
# ---------------------------------------------------------------------------
_flood_state: dict[tuple[int, int], deque[float]] = defaultdict(lambda: deque(maxlen=20))
_last_message: dict[tuple[int, int], tuple[str, float]] = {}  # (chat_id,uid) → (text, ts)


# ---------------------------------------------------------------------------
# Helper: apply an action
# ---------------------------------------------------------------------------

async def _apply_action(
    action: str,
    bot: Bot,
    session: AsyncSession,
    message: Message,
    reason: str,
    mute_duration: int = 3600,
) -> None:
    chat_id = message.chat.id
    user_id = message.from_user.id  # type: ignore[union-attr]
    msg_id = message.message_id

    if action == "ignore":
        return

    if action in ("delete", "warn", "mute", "kick", "ban"):
        # Always delete the offending message first (silently)
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
                await bot.send_message(
                    chat_id,
                    f"⚠️ User reached {limit} warnings and has been automatically punished.",
                    parse_mode="HTML",
                )
            else:
                await bot.send_message(
                    chat_id,
                    f"⚠️ Warning <b>{count}/{limit}</b> — {reason}",
                    parse_mode="HTML",
                )
        except Exception:
            pass

    elif action == "mute":
        await mod.mute_user(
            bot, session, chat_id=chat_id, user_id=user_id,
            duration_seconds=mute_duration, actor_id=None, reason=reason,
        )
        try:
            await bot.send_message(chat_id, f"🔇 User muted: {reason}")
        except Exception:
            pass

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


# ---------------------------------------------------------------------------
# Detection functions
# ---------------------------------------------------------------------------

def _check_flood(chat_id: int, user_id: int, flood_count: int, flood_window: int) -> bool:
    key = (chat_id, user_id)
    now = time.monotonic()
    q = _flood_state[key]
    q.append(now)
    # Count messages in the last flood_window seconds
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
# Main message handler
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
            # Still count messages for stats
            await repo.increment_stat(session, chat_id, "messages_today")
            return
    except Exception:
        pass

    # Count all user messages
    await repo.increment_stat(session, chat_id, "messages_today")

    text = message.text or message.caption or ""

    filters = await repo.get_filters(session, chat_id)
    fmap = _build_filter_map(filters)
    settings = await repo.get_settings(session, chat_id)
    mute_duration = settings.mute_duration if settings else 3600

    async def act(filter_type: str, reason: str) -> bool:
        """Apply action for a filter; return True if message was acted on."""
        f = fmap.get(filter_type)
        if not f or not f.enabled:
            return False
        if f.action == "ignore":
            return False
        await _apply_action(f.action, bot, session, message, reason, mute_duration)
        await repo.add_log(
            session,
            group_id=chat_id,
            event_type="filter_triggered",
            target_id=user.id,
            details=f"filter={filter_type} action={f.action}",
        )
        return True

    # ------------------------------------------------------------------
    # Run checks in priority order; stop on first match that deletes msg
    # ------------------------------------------------------------------

    # 1. Flood
    f_flood = fmap.get("flood")
    if f_flood and f_flood.enabled and text:
        flood_count, flood_window = 5, 10  # defaults; future: make configurable
        if _check_flood(chat_id, user.id, flood_count, flood_window):
            if await act("flood", "Flood detected"):
                return

    # 2. Duplicate messages
    f_dup = fmap.get("duplicate_messages")
    if f_dup and f_dup.enabled and text:
        dup_window = 30
        if _check_duplicate(chat_id, user.id, text, dup_window):
            if await act("duplicate_messages", "Duplicate message"):
                return

    # 3. Telegram invite links
    if text and has_telegram_link(text):
        if await act("telegram_links", "Telegram link detected"):
            return

    # 4. External links
    if text and has_external_link(text):
        if await act("external_links", "External link detected"):
            return

    # 5. Advertisement (@ mentions that look promotional)
    if text and has_advertisement(text):
        if await act("advertisement", "Advertisement detected"):
            return

    # 6. Excessive emojis
    if text:
        emoji_count = count_emojis(text)
        f_emoji = fmap.get("excessive_emojis")
        if f_emoji and f_emoji.enabled and emoji_count > 10:
            if await act("excessive_emojis", f"Too many emojis ({emoji_count})"):
                return

    # 7. Repeated characters
    if text and has_repeated_chars(text):
        if await act("repeated_chars", "Repeated characters detected"):
            return

    # 8. Long messages
    if text:
        f_long = fmap.get("long_messages")
        if f_long and f_long.enabled and len(text) > 2000:
            if await act("long_messages", f"Message too long ({len(text)} chars)"):
                return

    # 9. Bad words (checks against extra field word list)
    if text:
        f_bw = fmap.get("bad_words")
        if f_bw and f_bw.enabled and f_bw.extra:
            bad_words = [w.strip().lower() for w in f_bw.extra.split(",") if w.strip()]
            lower_text = text.lower()
            for word in bad_words:
                if word and re.search(rf"\b{re.escape(word)}\b", lower_text):
                    if await act("bad_words", f"Prohibited word: {word}"):
                        return
                    break

    # 10. Spam / insults  (future: plug in AI classifier here)
    # Placeholder: these filters exist in DB but detection is left for AI pass
