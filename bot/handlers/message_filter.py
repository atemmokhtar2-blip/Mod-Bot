"""
Automatic moderation filter — Version 7 (AI Multi-Action + Link Analysis).

V4.1 changes
------------
- bad_words filter runs FIRST — before flood, duplicate, or any other check.
- Detection backed by the new ProfanityEngine (built-in dictionary + per-group
  custom words), compiled regex, TTL-cached per group.
- In-process word-list cache eliminates repeated DB queries on hot paths.
- wordlist_cache_invalidate() exported for wordlist.py to call on mutations.

Filter execution order (V4.1)
------------------------------
 1. bad_words      ← FIRST (profanity — highest priority)
 2. forwarded      (V4)
 3. flood
 4. duplicate_messages
 5. telegram_links
 6. external_links
 7. advertisement
 8. excessive_emojis
 9. repeated_chars
10. long_messages
11. mass_mention   (V4)
12. hashtag        (V4)
13. AI text analysis (V6) — handles insults, spam, harassment, threats, scams
Media locks are checked separately before all text filters.
"""

from __future__ import annotations

import re
import time
from collections import defaultdict, deque
from typing import Optional

from aiogram import Bot, Router, F
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.ai.manager import ai_manager
from bot.services import moderation_service as mod
from bot.services.warning_service import warn_user
from bot.strings.ar import S
from database import repository as repo
from database.models import AI_SENSITIVITY_THRESHOLDS, Filter
from utils.helpers import (
    count_emojis,
    has_advertisement,
    has_external_link,
    has_repeated_chars,
    has_telegram_link,
)
from utils.logger import get_logger
from utils.profanity.engine import engine as profanity_engine

log = get_logger(__name__)
router = Router(name="message_filter")


# ---------------------------------------------------------------------------
# In-memory state  (chat_id, user_id) → deque / last-message tuple
# ---------------------------------------------------------------------------
_flood_state: dict[tuple[int, int], deque[float]] = defaultdict(lambda: deque(maxlen=30))
_last_message: dict[tuple[int, int], tuple[str, float]] = {}


# ---------------------------------------------------------------------------
# Custom word-list in-process cache
# TTL: 120 s — matches engine pattern cache TTL.
# Invalidated on add/remove/clear via wordlist_cache_invalidate().
# ---------------------------------------------------------------------------
_WORD_LIST_TTL: float = 120.0
_word_list_cache: dict[int, tuple[float, list[str]]] = {}
# (group_id) → (expiry_monotonic, [word1, word2, ...])


def wordlist_cache_invalidate(group_id: int) -> None:
    """
    Drop the cached word list for *group_id*.
    Call this after any add/remove/clear operation so the next message
    scan reloads from the database.
    """
    _word_list_cache.pop(group_id, None)


async def _get_custom_words(session: AsyncSession, group_id: int) -> list[str]:
    """Return the custom word list, using the in-memory cache when valid."""
    now = time.monotonic()
    entry = _word_list_cache.get(group_id)
    if entry and entry[0] > now:
        return entry[1]

    words = await repo.get_custom_word_strings(session, group_id)
    _word_list_cache[group_id] = (now + _WORD_LIST_TTL, words)
    return words


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
    notify_template: Optional[str] = None,
    mute_duration: int = 3600,
) -> None:
    chat_id = message.chat.id
    user = message.from_user
    user_id = user.id
    name = user.first_name or str(user_id)

    if action == "ignore":
        return

    if action in ("delete", "warn", "mute", "kick", "ban"):
        await mod.delete_message_safe(
            bot, session, chat_id=chat_id, message_id=message.message_id,
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


# V4 detection helpers
_MENTION_RE = re.compile(r"@\w+")
_HASHTAG_RE = re.compile(r"#\w+")

# V7 — URL extraction for AI link analysis
_URL_RE = re.compile(
    r"(?:https?://|www\.)\S+|t\.me/\S+",
    re.IGNORECASE,
)


def _extract_urls(text: str) -> list[str]:
    """Extract all URLs from *text* for AI link analysis."""
    return _URL_RE.findall(text)


def _has_forwarded(message: Message) -> bool:
    return bool(
        message.forward_date
        or message.forward_from
        or message.forward_from_chat
        or message.forward_sender_name
    )


def _has_mass_mention(text: str, threshold: int = 5) -> bool:
    return len(_MENTION_RE.findall(text)) >= threshold


def _has_hashtag(text: str) -> bool:
    return bool(_HASHTAG_RE.search(text))


# ---------------------------------------------------------------------------
# Media lock checker — V4
# ---------------------------------------------------------------------------

async def _check_media_locks(
    bot: Bot,
    session: AsyncSession,
    message: Message,
    settings,
) -> bool:
    if not settings:
        return False

    user    = message.from_user
    user_id = user.id
    name    = user.first_name or str(user_id)
    chat_id = message.chat.id

    lock_map = [
        (settings.lock_photos,    message.photo,     S.media_photos),
        (settings.lock_video,     message.video,     S.media_video),
        (settings.lock_audio,     message.audio,     S.media_audio),
        (settings.lock_documents, message.document,  S.media_documents),
        (settings.lock_stickers,  message.sticker,   S.media_stickers),
        (settings.lock_gifs,      message.animation, S.media_gifs),
        (settings.lock_polls,     message.poll,      S.media_polls),
        (settings.lock_locations, message.location,  S.media_locations),
        (settings.lock_voice,     message.voice,     S.media_voice),
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
# V6/V7 — AI Protection (Gemini) — never raises; silently skips on any failure.
# ---------------------------------------------------------------------------

async def _apply_ai_multi_actions(
    bot: Bot,
    session: AsyncSession,
    message: Message,
    settings,
    reason: str,
    filter_type: str,
) -> bool:
    """
    V7: Apply all enabled AI actions in order: delete → warn → mute → ban.
    Message is always deleted first (minimum action for any AI violation).
    Returns True unconditionally on entry — caller can rely on it as a
    "message was handled" sentinel.
    """
    chat_id  = message.chat.id
    user     = message.from_user
    user_id  = user.id
    name     = user.first_name or str(user_id)
    mute_dur = getattr(settings, "mute_duration", 3600)

    # 1. Delete the offending message (always — regardless of action config)
    try:
        await mod.delete_message_safe(
            bot, session, chat_id=chat_id,
            message_id=message.message_id,
            actor_id=None, reason=reason,
        )
    except Exception as exc:
        log.debug("AI delete failed (already gone?): %s", exc)

    # 2. Extra punishment actions (independent of delete)
    if getattr(settings, "ai_action_warn", False):
        try:
            count, limit, punished = await warn_user(
                bot, session, chat_id=chat_id,
                user_id=user_id, actor_id=None, reason=reason,
            )
            if punished:
                await _notify(bot, chat_id, S.auto_punished, user_id, name)
            else:
                try:
                    await bot.send_message(
                        chat_id,
                        S.auto_warn_notice.format(count=count, limit=limit, reason=reason),
                        parse_mode="HTML",
                    )
                except Exception:
                    pass
        except Exception as exc:
            log.debug("AI warn failed: %s", exc)

    if getattr(settings, "ai_action_mute", False):
        try:
            await mod.mute_user(
                bot, session, chat_id=chat_id, user_id=user_id,
                duration_seconds=mute_dur, actor_id=None, reason=reason,
            )
        except Exception as exc:
            log.debug("AI mute failed: %s", exc)

    if getattr(settings, "ai_action_ban", False):
        try:
            await mod.ban_user(
                bot, session, chat_id=chat_id, user_id=user_id,
                actor_id=None, reason=reason,
            )
        except Exception as exc:
            log.debug("AI ban failed: %s", exc)

    # 3. Audit log
    await repo.add_log(
        session,
        group_id=chat_id,
        event_type="filter_triggered",
        target_id=user_id,
        details=f"filter={filter_type} reason={reason}",
    )
    return True


async def _handle_ai_verdict(
    session: AsyncSession,
    chat_id: int,
    user_id: int,
    filter_type: str,
    verdict,
    threshold: int,
    act_fn,
) -> bool:
    """Route VIOLATION to act_fn (multi-action closure); log SUSPICIOUS only."""
    if verdict is None:
        return False

    if verdict.is_violation and verdict.confidence >= threshold:
        reason = f"ai:{verdict.reason[:120]}" if verdict.reason else "ai_violation"
        return await act_fn(filter_type, reason)

    if verdict.is_suspicious:
        await repo.add_log(
            session,
            group_id=chat_id,
            event_type="filter_triggered",
            target_id=user_id,
            details=(
                f"ai_suspicious filter={filter_type} confidence={verdict.confidence} "
                f"reason={verdict.reason} recommended={verdict.recommended_action}"
            ),
        )
    return False


async def _run_ai_image_check(
    bot: Bot,
    session: AsyncSession,
    message: Message,
    settings,
    fmap: dict[str, Filter],
    act_fn,
) -> bool:
    # Gate: AI must be enabled and image analysis must be on.
    # We intentionally do NOT gate on the ai_image filter row — the filter-row
    # enabled flag was designed for deterministic filters. AI moderation is
    # controlled entirely via GroupSettings (ai_enabled, ai_analyze_images) and
    # the multi-action flags (ai_action_*). Requiring the filter row to be
    # enabled too creates a hidden second gate that users never know to set.
    if not (settings and settings.ai_enabled and settings.ai_analyze_images):
        return False
    if not message.photo:
        return False

    try:
        from io import BytesIO
        buf = BytesIO()
        await bot.download(message.photo[-1], destination=buf)
        image_bytes = buf.getvalue()
    except Exception as exc:
        log.warning("AI image download failed: %s", exc)
        return False

    verdict   = await ai_manager.analyze_image(session, image_bytes, mime_type="image/jpeg")
    threshold = AI_SENSITIVITY_THRESHOLDS.get(settings.ai_sensitivity, 65)
    return await _handle_ai_verdict(
        session, message.chat.id, message.from_user.id, "ai_image", verdict, threshold, act_fn,
    )


async def _run_ai_text_check(
    session: AsyncSession,
    message: Message,
    text: str,
    settings,
    fmap: dict[str, Filter],
    act_fn,
) -> bool:
    # Gate: AI must be enabled and message analysis must be on.
    # We intentionally do NOT gate on the ai_text filter row — see the comment
    # in _run_ai_image_check for the full rationale. ai_enabled +
    # ai_analyze_messages are the correct and sufficient controls.
    if not (settings and settings.ai_enabled and settings.ai_analyze_messages):
        return False
    if not text or not text.strip():
        return False

    verdict   = await ai_manager.analyze_text(session, text)
    threshold = AI_SENSITIVITY_THRESHOLDS.get(settings.ai_sensitivity, 65)
    return await _handle_ai_verdict(
        session, message.chat.id, message.from_user.id, "ai_text", verdict, threshold, act_fn,
    )


async def _run_ai_links_check(
    session: AsyncSession,
    message: Message,
    text: str,
    settings,
    fmap: dict[str, Filter],
    act_fn,
) -> bool:
    """
    V7: Dedicated URL-safety analysis.
    Extracts up to 5 URLs from the message text and classifies them with the
    LINK_SYSTEM_PROMPT. Only fires when ai_analyze_links is enabled.

    We intentionally do NOT gate on the ai_text filter row — see the comment
    in _run_ai_image_check for the full rationale.
    """
    if not (settings and settings.ai_enabled and getattr(settings, "ai_analyze_links", False)):
        return False
    if not text or not text.strip():
        return False

    urls = _extract_urls(text)
    if not urls:
        return False

    url_sample = " ".join(urls[:5])   # cap at 5 URLs to avoid huge prompts
    verdict    = await ai_manager.analyze_links(session, url_sample)
    threshold  = AI_SENSITIVITY_THRESHOLDS.get(settings.ai_sensitivity, 65)
    return await _handle_ai_verdict(
        session, message.chat.id, message.from_user.id, "ai_links", verdict, threshold, act_fn,
    )


# ---------------------------------------------------------------------------
# Main handler
# ---------------------------------------------------------------------------

@router.edited_message(F.chat.type.in_({"group", "supergroup"}))
async def filter_edited_message(message: Message, bot: Bot, session: AsyncSession) -> None:
    """
    V7.2: Re-run the exact same filter pipeline against edited messages.
    Covers the classic bypass of posting something innocuous, letting it pass,
    then editing it into a violation afterwards.
    """
    await filter_message(message, bot, session)


@router.message(F.chat.type.in_({"group", "supergroup"}))
async def filter_message(message: Message, bot: Bot, session: AsyncSession) -> None:
    """Intercept all group messages and apply enabled filters in priority order."""
    if message.sender_chat:
        return

    user = message.from_user
    if not user or user.is_bot:
        return

    chat_id = message.chat.id

    group = await repo.get_group(session, chat_id)
    if not group or not group.is_active:
        return

    # ─── V8: Quick Admin Commands (Reply-based) ──────────────────────────────
    # If an admin replies with "طرد", "حظر", or "كتم", execute the action immediately.
    if message.reply_to_message and text:
        # Check if the sender is an admin
        is_admin = False
        try:
            member = await bot.get_chat_member(chat_id, user.id)
            if member.status in ("administrator", "creator"):
                is_admin = True
        except Exception:
            pass

        if is_admin:
            target = message.reply_to_message.from_user
            if target and not target.is_bot:
                clean_text = text.strip().lower()
                
                # 1. Ban/Kick (طرد or حظر)
                if clean_text in ("طرد", "حظر"):
                    try:
                        await bot.ban_chat_member(chat_id, target.id)
                        await message.reply(f"🚫 تم {clean_text} المستخدم <b>{target.full_name}</b> بنجاح.")
                        await repo.add_log(session, chat_id, "user_banned", target.id, f"Quick command: {clean_text} by {user.id}")
                        return
                    except Exception as e:
                        await message.reply(f"❌ فشل الـ {clean_text}: {str(e)}")
                        return

                # 2. Mute (كتم)
                elif clean_text == "كتم":
                    try:
                        # Default mute for 24 hours if no duration specified
                        until = int(time.time() + 86400)
                        await bot.restrict_chat_member(
                            chat_id, target.id,
                            permissions={"can_send_messages": False},
                            until_date=until
                        )
                        await message.reply(f"🔇 تم كتم المستخدم <b>{target.full_name}</b> لمدة 24 ساعة.")
                        await repo.add_log(session, chat_id, "user_muted", target.id, f"Quick command: كتم by {user.id}")
                        return
                    except Exception as e:
                        await message.reply(f"❌ فشل الكتم: {str(e)}")
                        return

                # 3. Unban/Unmute (إلغاء or فك)
                elif clean_text in ("إلغاء", "فك"):
                    try:
                        await bot.unban_chat_member(chat_id, target.id, grow_confused=True)
                        await message.reply(f"✅ تم فك القيود عن <b>{target.full_name}</b>.")
                        return
                    except Exception:
                        pass

    # Do not moderate Telegram admins / owners for standard filters
    try:
        member = await bot.get_chat_member(chat_id, user.id)
        if member.status in ("administrator", "creator"):
            await repo.increment_stat(session, chat_id, "messages_today")
            return
    except Exception:
        pass

    await repo.increment_stat(session, chat_id, "messages_today")

    filters  = await repo.get_filters(session, chat_id)
    fmap     = _build_filter_map(filters)
    settings = await repo.get_settings(session, chat_id)
    mute_duration = settings.mute_duration if settings else 3600

    # ── V4: Media locks ─────────────────────────────────────────────────────
    if await _check_media_locks(bot, session, message, settings):
        return

    text = message.text or message.caption or ""

    async def act(filter_type: str, reason: str, notify_tpl: Optional[str] = None) -> bool:
        """Apply the configured action for a filter; return True if message was acted on."""
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
            details=f"filter={filter_type} action={f.action} reason={reason}",
        )
        return True

    # ════════════════════════════════════════════════════════════════════════
    # V7: AI action closure — uses multi-action settings instead of the
    #     single filter action. Shared by image, text, and link AI checks.
    # ════════════════════════════════════════════════════════════════════════
    async def ai_act(filter_type: str, reason: str) -> bool:
        return await _apply_ai_multi_actions(bot, session, message, settings, reason, filter_type)

    # ════════════════════════════════════════════════════════════════════════
    # V6: AI IMAGE ANALYSIS — runs early, right after media locks, before any
    #     text filter. Never raises — failures are silently skipped.
    # ════════════════════════════════════════════════════════════════════════
    if await _run_ai_image_check(bot, session, message, settings, fmap, ai_act):
        return

    # ════════════════════════════════════════════════════════════════════════
    # 1. BAD WORDS — runs FIRST, highest priority
    #    V4.1: uses ProfanityEngine (built-in dict + custom words, cached).
    # ════════════════════════════════════════════════════════════════════════
    f_bw = fmap.get("bad_words")
    if f_bw and f_bw.enabled and text:
        # Load custom words from cache (DB query only on cache miss)
        custom_words = await _get_custom_words(session, chat_id)
        matched = profanity_engine.check(text, custom_words=custom_words, group_id=chat_id)
        if matched:
            acted = await act("bad_words", f"bad_word:{matched}", S.auto_bad_word)
            if acted:
                return

    # ════════════════════════════════════════════════════════════════════════
    # 2. FORWARDED MESSAGES  (V4)
    # ════════════════════════════════════════════════════════════════════════
    if _has_forwarded(message):
        if await act("forwarded", "forwarded", S.auto_forwarded):
            return

    # ════════════════════════════════════════════════════════════════════════
    # 3. FLOOD
    # ════════════════════════════════════════════════════════════════════════
    f_flood = fmap.get("flood")
    if f_flood and f_flood.enabled:
        if _check_flood(chat_id, user.id, 5, 10):
            if await act("flood", "flood", S.auto_flood):
                return

    # ════════════════════════════════════════════════════════════════════════
    # 4. DUPLICATE MESSAGES
    # ════════════════════════════════════════════════════════════════════════
    if text:
        f_dup = fmap.get("duplicate_messages")
        if f_dup and f_dup.enabled:
            if _check_duplicate(chat_id, user.id, text, 30):
                if await act("duplicate_messages", "duplicate", S.auto_duplicate):
                    return

    # ════════════════════════════════════════════════════════════════════════
    # 5. TELEGRAM INVITE LINKS
    # ════════════════════════════════════════════════════════════════════════
    if text and has_telegram_link(text):
        if await act("telegram_links", "telegram_link", S.auto_telegram_link):
            return

    # ════════════════════════════════════════════════════════════════════════
    # 6. EXTERNAL LINKS
    # ════════════════════════════════════════════════════════════════════════
    if text and has_external_link(text):
        if await act("external_links", "external_link", S.auto_external_link):
            return

    # ════════════════════════════════════════════════════════════════════════
    # 7. ADVERTISEMENT
    # ════════════════════════════════════════════════════════════════════════
    if text and has_advertisement(text):
        if await act("advertisement", "advertisement", S.auto_advertisement):
            return

    # ════════════════════════════════════════════════════════════════════════
    # 8. EXCESSIVE EMOJIS
    # ════════════════════════════════════════════════════════════════════════
    if text:
        f_emoji = fmap.get("excessive_emojis")
        if f_emoji and f_emoji.enabled and count_emojis(text) > 10:
            if await act("excessive_emojis", "excessive_emojis", S.auto_emoji):
                return

    # ════════════════════════════════════════════════════════════════════════
    # 9. REPEATED CHARACTERS
    # ════════════════════════════════════════════════════════════════════════
    if text and has_repeated_chars(text):
        if await act("repeated_chars", "repeated_chars", S.auto_repeated):
            return

    # ════════════════════════════════════════════════════════════════════════
    # 10. LONG MESSAGES
    # ════════════════════════════════════════════════════════════════════════
    if text:
        f_long = fmap.get("long_messages")
        if f_long and f_long.enabled and len(text) > 2000:
            if await act("long_messages", "long_message", S.auto_long_msg):
                return

    # ════════════════════════════════════════════════════════════════════════
    # 11. MASS MENTION  (V4)
    # ════════════════════════════════════════════════════════════════════════
    if text and _has_mass_mention(text):
        if await act("mass_mention", "mass_mention", S.auto_mass_mention):
            return

    # ════════════════════════════════════════════════════════════════════════
    # 12. HASHTAG  (V4)
    # ════════════════════════════════════════════════════════════════════════
    if text and _has_hashtag(text):
        if await act("hashtag", "hashtag", S.auto_hashtag):
            return

    # ════════════════════════════════════════════════════════════════════════
    # 13. AI TEXT ANALYSIS (V6) — runs after all deterministic filters.
    #     Detects profanity, insults, harassment, hate speech, threats, scams,
    #     spam, ads, suspicious links, filter-bypass attempts, and toxicity.
    #     Never raises — failures are silently skipped so the bot keeps working.
    # ════════════════════════════════════════════════════════════════════════
    if text:
        if await _run_ai_text_check(session, message, text, settings, fmap, ai_act):
            return

    # ════════════════════════════════════════════════════════════════════════
    # 14. AI LINK ANALYSIS (V7) — dedicated URL-safety check.
    #     Only fires when ai_analyze_links is enabled AND the message text
    #     contains at least one URL that slipped past the deterministic link
    #     filters above. Uses the LINK_SYSTEM_PROMPT for targeted verdict.
    #     Never raises — failures are silently skipped.
    # ════════════════════════════════════════════════════════════════════════
    if text:
        if await _run_ai_links_check(session, message, text, settings, fmap, ai_act):
            return
