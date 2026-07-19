"""
Security module — shared authorization helpers.

Every management callback and the /start home-dashboard MUST go through
these functions.  The principle is: NEVER trust the database alone.

Gates applied on every management action
-----------------------------------------
1. Keyboard expiry  — reject keyboards older than KEYBOARD_TTL_SECONDS.
2. DB pre-check     — fast reject if user is not registered at all.
3. Live Telegram API — getChatMember() must confirm creator/administrator.

No exceptions.  No cached results.  No previous session trust.
"""

from __future__ import annotations

import time
from datetime import datetime, timezone

from aiogram import Bot
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from bot.strings.ar import S
from database import repository as repo
from utils.logger import get_logger

log = get_logger(__name__)

# Inline keyboards expire after 3 hours.
KEYBOARD_TTL_SECONDS = 10_800


# ---------------------------------------------------------------------------
# Low-level live permission check
# ---------------------------------------------------------------------------

async def verify_live_tg_permission(bot: Bot, group_id: int, user_id: int) -> bool:
    """
    Calls Telegram's getChatMember API.
    Returns True ONLY if the user is currently a creator or administrator.

    Returns False (never raises) on any API error — callers must deny access
    on False.
    """
    try:
        member = await bot.get_chat_member(group_id, user_id)
        allowed = member.status in ("creator", "administrator")
        log.info(
            "live_perm: user=%s group=%s tg_status=%s allowed=%s",
            user_id, group_id, member.status, allowed,
        )
        return allowed
    except Exception as exc:
        log.warning(
            "live_perm: get_chat_member FAILED user=%s group=%s — %s",
            user_id, group_id, exc,
        )
        return False


# ---------------------------------------------------------------------------
# Full authorization guard — use this in EVERY management callback
# ---------------------------------------------------------------------------

async def ensure_authorized(
    cb: CallbackQuery,
    bot: Bot,
    session: AsyncSession,
    group_id: int,
    *,
    check_keyboard_expiry: bool = True,
) -> bool:
    """
    Three-gate authorization check.

    Returns True only when ALL gates pass.  Shows an alert and returns False
    for any failure — callers should immediately return without further action.

    Gates
    -----
    1. Keyboard TTL  — message older than KEYBOARD_TTL_SECONDS is rejected.
    2. DB pre-check  — user must be owner or registered admin in the DB.
    3. Live Telegram — getChatMember() must return creator/administrator.
       Stale DB admin records are pruned automatically when gate 3 fails.
    """
    user_id = cb.from_user.id

    # ── Gate 1: Keyboard expiry ──────────────────────────────────────────────
    if check_keyboard_expiry and cb.message and cb.message.date:
        msg_date = cb.message.date
        if isinstance(msg_date, datetime):
            age = (datetime.now(timezone.utc) - msg_date).total_seconds()
        else:
            # Fallback: aiogram may expose date as a plain Unix int
            age = time.time() - float(msg_date)

        if age > KEYBOARD_TTL_SECONDS:
            log.info(
                "keyboard_expired: user=%s group=%s age=%.0fs (limit=%ds)",
                user_id, group_id, age, KEYBOARD_TTL_SECONDS,
            )
            try:
                await cb.answer(S.keyboard_expired, show_alert=True)
            except Exception:
                pass
            return False

    # ── Gate 2: DB pre-check ─────────────────────────────────────────────────
    db_ok = await repo.is_authorized(session, group_id, user_id)
    if not db_ok:
        log.info(
            "auth_denied: user=%s group=%s reason=not_in_db",
            user_id, group_id,
        )
        try:
            await cb.answer(S.no_permission_cb, show_alert=True)
        except Exception:
            pass
        return False

    # ── Gate 3: Live Telegram API ────────────────────────────────────────────
    live_ok = await verify_live_tg_permission(bot, group_id, user_id)
    if not live_ok:
        log.info(
            "auth_denied: user=%s group=%s reason=not_tg_admin (demoted or left)",
            user_id, group_id,
        )
        # Prune the stale DB admin record so future plain /start won't show
        # this group in the user's dashboard.
        try:
            await repo.remove_admin(session, group_id, user_id)
            log.info("stale_admin_pruned: user=%s group=%s", user_id, group_id)
        except Exception as exc:
            log.warning(
                "stale_admin_prune_failed: user=%s group=%s — %s",
                user_id, group_id, exc,
            )
        try:
            await cb.answer(S.no_permission_cb, show_alert=True)
        except Exception:
            pass
        return False

    return True


# ---------------------------------------------------------------------------
# Owner-only guard
# ---------------------------------------------------------------------------

async def ensure_owner(
    cb: CallbackQuery,
    bot: Bot,
    session: AsyncSession,
    group_id: int,
) -> bool:
    """
    Owner-only check: DB ownership + live Telegram API confirmation.
    """
    user_id = cb.from_user.id

    db_ok = await repo.is_owner(session, group_id, user_id)
    if not db_ok:
        log.info(
            "owner_denied: user=%s group=%s reason=not_db_owner",
            user_id, group_id,
        )
        try:
            await cb.answer(S.owner_only_cb, show_alert=True)
        except Exception:
            pass
        return False

    live_ok = await verify_live_tg_permission(bot, group_id, user_id)
    if not live_ok:
        log.info(
            "owner_denied: user=%s group=%s reason=not_tg_admin (live check)",
            user_id, group_id,
        )
        try:
            await cb.answer(S.owner_only_cb, show_alert=True)
        except Exception:
            pass
        return False

    return True
