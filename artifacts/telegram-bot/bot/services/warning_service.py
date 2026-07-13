"""
Warning system service.
Handles warn/reset and triggers auto-punishment when limit is reached.
Future: warning decay over time, per-filter warning weights.
"""

from __future__ import annotations

from aiogram import Bot
from sqlalchemy.ext.asyncio import AsyncSession

from database import repository as repo
from bot.services import moderation_service as mod
from utils.logger import get_logger

log = get_logger(__name__)


async def warn_user(
    bot: Bot,
    session: AsyncSession,
    *,
    chat_id: int,
    user_id: int,
    actor_id: int | None = None,
    reason: str | None = None,
) -> tuple[int, int, bool]:
    """
    Add a warning.
    Returns (new_count, warning_limit, punishment_applied).
    """
    settings = await repo.get_settings(session, chat_id)
    warning_limit = settings.warning_limit if settings else 3
    auto_punishment = settings.auto_punishment if settings else "mute"
    mute_duration = settings.mute_duration if settings else 3600

    new_count = await repo.add_warning(session, chat_id, user_id, reason)
    await repo.add_log(
        session,
        group_id=chat_id,
        event_type="user_warned",
        actor_id=actor_id,
        target_id=user_id,
        details=f"count={new_count}/{warning_limit} reason={reason}",
    )

    punishment_applied = False
    if new_count >= warning_limit:
        # Reset warnings before punishment so the counter is clean
        await repo.reset_warnings(session, chat_id, user_id)

        if auto_punishment == "ban":
            punishment_applied = await mod.ban_user(
                bot, session, chat_id=chat_id, user_id=user_id,
                actor_id=actor_id, reason=f"Auto-ban: reached {warning_limit} warnings",
            )
        elif auto_punishment == "kick":
            punishment_applied = await mod.kick_user(
                bot, session, chat_id=chat_id, user_id=user_id,
                actor_id=actor_id, reason=f"Auto-kick: reached {warning_limit} warnings",
            )
        else:  # default: mute
            punishment_applied = await mod.mute_user(
                bot, session, chat_id=chat_id, user_id=user_id,
                duration_seconds=mute_duration, actor_id=actor_id,
                reason=f"Auto-mute: reached {warning_limit} warnings",
            )

    return new_count, warning_limit, punishment_applied
