"""
Automatic moderation filter — Version 4 (Media locks + 3 new filter types).

V4 additions
------------
- Media locks: delete photos/video/audio/documents/stickers/gifs/polls/locations/voice
  when the corresponding lock_* flag is set in GroupSettings.
- New filter types: forwarded, mass_mention, hashtag
- Detection helpers for the 3 new filters.

Existing logic preserved verbatim; new checks appended at the end.
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
    user = message.from_user
    user_id = user.id
    name = user.first_name or str(user_id)
    msg_id = message.message_id

    if action == "ignore":
        return

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
        await _notify(bot, chat_id, notify_template, user_id, name)


# ---------------------------------------------------------------------------
# Detection functions — existing
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
# Detection functions — V4 new
# ---------------------------------------------------------------------------

def _has_forwarded(message: Message) -> bool:
    """True if the message is a forward from any source."""
    return bool(
        message.forward_date
        or message.forward_from
        or message.forward_from_chat
        or message.forward_sender_name
    )


_MENTION_RE = re.compile(r"@\w+")


def _has_mass_mention(text: str, threshold: int = 5) -> bool:
    """True if the text contains 5+ @username mentions."""
    return len(_MENTION_RE.findall(text)) >= threshold


_HASHTAG_RE = re.compile(r"#\w+")


def _has_hashtag(text: str) -> bool:
    """True if the text contains at least one #hashtag."""
    return bool(_HASHTAG_RE.search(text))


# ---------------------------------------------------------------------------
# Media lock checker — V4
# ---------------------------------------------------------------------------

async def _check_media_locks(
    bot: Bot,
    session: AsyncSession,
    message: Message,
) -> bool:
    """
    Delete the message if its media type is locked in group settings.
    Returns True if the message was deleted (caller should return early).
    """
    settings = await repo.get_settings(session, message.chat.id)
    if not settings:
        return False

    user = message.from_user
    user_id = user.id
    name = user.first_name or str(user_id)
    chat_id = message.chat.id

    lock_map = [
        (settings.lock_photos,    message.photo,    S.media_photos),
        (settings.lock_video,     message.video,    S.media_video),
        (settings.lock_audio,     message.audio,    S.media_audio),
        (settings.lock_documents, message.document, S.media_documents),
        (settings.lock_stickers,  message.sticker,  S.media_stickers),
        (settings.lock_gifs,      message.animation, S.media_gifs),
        (settings.lock_polls,     message.poll,     S.media_polls),
        (settings.lock_locations, message.location, S.media_locations),
        (settings.lock_voice,     message.voice,    S.media_voice),
    ]

    for locked, media_obj, label in lock_map:
        if locked and media_obj:
            try:
                await bot.delete_message(chat_id, message.message_id)
            except Exception:
                pass
            try:
                await bot.send_message(
                    chat_id,
                    S.v4_media_blocked.format(uid=user_id, name=name),
                    parse_mode="HTML",
                )
            except Exception:
                pass
            await repo.add_log(
                session, group_id=chat_id, event_type="message_deleted",
                target_id=user_id, details=f"media_lock:{label}",
            )
            return True

    return False


# ---------------------------------------------------------------------------
# Main handler
# ---------------------------------------------------------------------------

@router.message(F.chat.type.in_({"group", "supergroup"}))
async def filter_message(message: Message, bot: Bot, session: AsyncSession) -> None:
    """Intercept all group messages and apply enabled filters."""
    if message.sender_chat:
        return

    user = message.from_user
    if not user or user.is_bot:
        return

    chat_id = message.chat.id

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

    # ── V4: Media locks — checked before text filters ───────────────────────
    if await _check_media_locks(bot, session, message):
        return

    text = message.text or message.caption or ""

    filters = await repo.get_filters(session, chat_id)
    fmap = _build_filter_map(filters)
    settings = await repo.get_settings(session, chat_id)
    mute_duration = settings.mute_duration if settings else 3600

    async def act(filter_type: str, reason: str, notify_tpl: str | None = None) -> bool:
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

    # ── V4: Forwarded messages ───────────────────────────────────────────────
    if _has_forwarded(message):
        if await act("forwarded", "forwarded", S.auto_forwarded):
            return

    # ── 1. Flood ─────────────────────────────────────────────────────────────
    f_flood = fmap.get("flood")
    if f_flood and f_flood.enabled and text:
        if _check_flood(chat_id, user.id, 5, 10):
            if await act("flood", "flood", S.auto_flood):
                return

    # ── 2. Duplicate messages ────────────────────────────────────────────────
    f_dup = fmap.get("duplicate_messages")
    if f_dup and f_dup.enabled and text:
        if _check_duplicate(chat_id, user.id, text, 30):
            if await act("duplicate_messages", "duplicate", S.auto_duplicate):
                return

    # ── 3. Telegram invite links ─────────────────────────────────────────────
    if text and has_telegram_link(text):
        if await act("telegram_links", "telegram_link", S.auto_telegram_link):
            return

    # ── 4. External links ────────────────────────────────────────────────────
    if text and has_external_link(text):
        if await act("external_links", "external_link", S.auto_external_link):
            return

    # ── 5. Advertisement ─────────────────────────────────────────────────────
    if text and has_advertisement(text):
        if await act("advertisement", "advertisement", S.auto_advertisement):
            return

    # ── 6. Excessive emojis ──────────────────────────────────────────────────
    if text:
        emoji_count = count_emojis(text)
        f_emoji = fmap.get("excessive_emojis")
        if f_emoji and f_emoji.enabled and emoji_count > 10:
            if await act("excessive_emojis", "excessive_emojis", S.auto_emoji):
                return

    # ── 7. Repeated characters ───────────────────────────────────────────────
    if text and has_repeated_chars(text):
        if await act("repeated_chars", "repeated_chars", S.auto_repeated):
            return

    # ── 8. Long messages ─────────────────────────────────────────────────────
    if text:
        f_long = fmap.get("long_messages")
        if f_long and f_long.enabled and len(text) > 2000:
            if await act("long_messages", "long_message", S.auto_long_msg):
                return

    # ── 9. Bad words ─────────────────────────────────────────────────────────
    if text:
        f_bw = fmap.get("bad_words")
        if f_bw and f_bw.enabled and f_bw.extra:
            bad_words = [w.strip() for w in f_bw.extra.split(",") if w.strip()]
            matched = contains_bad_word(text, bad_words)
            if matched:
                if await act("bad_words", f"bad_word:{matched}", S.auto_bad_word):
                    return

    # ── 10. Spam / Insults — placeholder; AI classifier hook ─────────────────
    # f_spam = fmap.get("spam") ...
    # f_insults = fmap.get("insults") ...

    # ── V4: Mass mention ─────────────────────────────────────────────────────
    if text and _has_mass_mention(text):
        if await act("mass_mention", "mass_mention", S.auto_mass_mention):
            return

    # ── V4: Hashtag ──────────────────────────────────────────────────────────
    if text and _has_hashtag(text):
        if await act("hashtag", "hashtag", S.auto_hashtag):
            return
