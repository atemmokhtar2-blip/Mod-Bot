"""
/start command handler — Arabic dashboard.
Future: onboarding wizard for first-time users, language selection.
"""

from __future__ import annotations

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.builder import main_menu_kb
from bot.strings.ar import S
from database import repository as repo
from utils.helpers import escape_html
from utils.logger import get_logger

log = get_logger(__name__)
router = Router(name="start")


@router.message(CommandStart())
async def cmd_start(message: Message, session: AsyncSession) -> None:
    """Entry point — always works in private chat."""
    user = message.from_user
    if not user:
        return

    await repo.upsert_user(
        session,
        user_id=user.id,
        first_name=user.first_name,
        last_name=user.last_name,
        username=user.username,
    )

    groups = await repo.get_groups_for_user(session, user.id)
    name = escape_html(user.first_name)

    if groups:
        status = S.start_has_groups.format(count=len(groups))
    else:
        status = S.start_no_groups

    text = S.start_greeting.format(name=name, status=status)

    await message.answer(
        text,
        reply_markup=main_menu_kb(groups),
        parse_mode="HTML",
    )
    log.info("User %s opened the Arabic dashboard", user.id)
