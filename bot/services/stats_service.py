"""
Statistics service — Arabic output (V2).
Future: weekly/monthly roll-ups, export to CSV, webhook push.
"""

from __future__ import annotations

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest
from sqlalchemy.ext.asyncio import AsyncSession

from bot.strings.ar import S
from database import repository as repo
from utils.logger import get_logger

log = get_logger(__name__)


async def refresh_member_count(bot: Bot, session: AsyncSession, group_id: int) -> int:
    """Fetch live member count and persist it in today's stats row."""
    try:
        count = await bot.get_chat_member_count(group_id)
        await repo.set_total_members(session, group_id, count)
        return count
    except TelegramBadRequest as exc:
        log.warning("Could not fetch member count for %s: %s", group_id, exc)
        return 0


def build_stats_text(stats_rows: list, group_title: str) -> str:
    if not stats_rows:
        return (
            S.stats_title.format(title=group_title) + "\n\n" +
            S.stats_no_data
        )

    today = stats_rows[0]
    lines = [
        S.stats_title.format(title=group_title),
        "",
        f"{S.stats_total_members}:   <b>{today.total_members}</b>",
        f"{S.stats_messages}:   <b>{today.messages_today}</b>",
        f"{S.stats_deleted}:   <b>{today.deleted_messages}</b>",
        f"{S.stats_muted}:   <b>{today.muted_members}</b>",
        f"{S.stats_banned}:   <b>{today.banned_members}</b>",
        f"{S.stats_warned}:   <b>{today.warned_members}</b>",
    ]

    if len(stats_rows) > 1:
        lines.append("")
        lines.append(S.stats_last_7)
        for row in stats_rows:
            lines.append(
                f"  📅 {row.date}: "
                f"💬 {row.messages_today} | "
                f"🗑️ {row.deleted_messages} | "
                f"⚠️ {row.warned_members} | "
                f"🚫 {row.banned_members}"
            )

    return "\n".join(lines)
