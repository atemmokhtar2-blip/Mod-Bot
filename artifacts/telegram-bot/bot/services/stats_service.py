"""
Statistics helpers.
Future: weekly/monthly roll-ups, export to CSV, webhook push.
"""

from __future__ import annotations

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest
from sqlalchemy.ext.asyncio import AsyncSession

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
        return f"📊 <b>{group_title}</b>\n\nNo statistics recorded yet."

    today = stats_rows[0]
    lines = [
        f"📊 <b>Statistics — {group_title}</b>",
        "",
        f"👥 Total Members:     <b>{today.total_members}</b>",
        f"💬 Messages Today:    <b>{today.messages_today}</b>",
        f"🗑 Deleted Messages:  <b>{today.deleted_messages}</b>",
        f"🔇 Muted (today):     <b>{today.muted_members}</b>",
        f"🚫 Banned (today):    <b>{today.banned_members}</b>",
    ]
    if len(stats_rows) > 1:
        lines.append("")
        lines.append("📅 <b>Last 7 days:</b>")
        for row in stats_rows:
            lines.append(
                f"  {row.date}: 💬 {row.messages_today} | 🗑 {row.deleted_messages} | 🚫 {row.banned_members}"
            )
    return "\n".join(lines)
