"""
/start command handler — shows the main private-chat dashboard.
Future: onboarding wizard for first-time users, language selection.
"""

from __future__ import annotations

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from database import repository as repo
from bot.keyboards.builder import main_menu_kb
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

    # Persist the user
    await repo.upsert_user(
        session,
        user_id=user.id,
        first_name=user.first_name,
        last_name=user.last_name,
        username=user.username,
    )

    groups = await repo.get_groups_for_user(session, user.id)

    greeting = (
        f"👋 Hello, <b>{escape_html(user.first_name)}</b>!\n\n"
        "I'm your <b>Telegram Moderation Bot</b>.\n\n"
    )

    if groups:
        greeting += f"You manage <b>{len(groups)}</b> group(s). Select one below:"
    else:
        greeting += (
            "You don't manage any groups yet.\n"
            "Add me to a group and grant me <b>Administrator</b> privileges to get started."
        )

    await message.answer(
        greeting,
        reply_markup=main_menu_kb(groups),
        parse_mode="HTML",
    )
    log.info("User %s opened the dashboard", user.id)
