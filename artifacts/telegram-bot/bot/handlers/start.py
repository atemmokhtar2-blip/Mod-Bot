"""
/start command handler — Version 3.

Handles:
  - Plain /start  → show home dashboard
  - /start grp_{group_id}  → deep link from "➕ إدارة هذه المجموعة" button in group.
    Registers the user as owner of that group and shows its panel directly.

Future: onboarding wizard for first-time users, language selection.
"""

from __future__ import annotations

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.builder import group_panel_kb, main_menu_kb
from bot.strings.ar import S
from database import repository as repo
from utils.helpers import escape_html
from utils.logger import get_logger

log = get_logger(__name__)
router = Router(name="start")


@router.message(CommandStart())
async def cmd_start(message: Message, session: AsyncSession) -> None:
    """Entry point — works in private chat, handles optional deep link."""
    user = message.from_user
    if not user:
        return

    # Upsert user record
    await repo.upsert_user(
        session,
        user_id=user.id,
        first_name=user.first_name,
        last_name=user.last_name,
        username=user.username,
    )

    # ------------------------------------------------------------------
    # V3: Deep link handling — /start grp_{group_id}
    # ------------------------------------------------------------------
    args = message.text.split(maxsplit=1)[1] if message.text and " " in message.text else ""
    if args.startswith("grp_"):
        try:
            group_id = int(args[4:])
        except ValueError:
            group_id = None

        if group_id:
            group = await repo.get_group(session, group_id)
            if group:
                # Register this user as owner if not already set
                if not group.owner_id:
                    await repo.set_owner(session, group_id, user.id)
                    group = await repo.get_group(session, group_id)

                # Show the success message and the group panel directly
                await message.answer(
                    S.group_linked.format(title=escape_html(group.title)),
                    parse_mode="HTML",
                    reply_markup=group_panel_kb(group_id),
                )
                log.info("User %s linked group %s via deep link", user.id, group_id)
                return

    # ------------------------------------------------------------------
    # Normal /start — show home dashboard
    # ------------------------------------------------------------------
    groups = await repo.get_groups_for_user(session, user.id)
    name = escape_html(user.first_name)

    if groups:
        status = S.start_has_groups.format(count=len(groups))
        active_group = groups[0]
        title = (
            S.home_title.format(name=name, group=escape_html(active_group.title))
        )
    else:
        status = S.start_no_groups
        title = S.home_title_no_group.format(name=name)

    text = S.start_greeting.format(name=name, status=status)

    await message.answer(
        text,
        reply_markup=main_menu_kb(groups),
        parse_mode="HTML",
    )
    log.info("User %s opened the dashboard (v3)", user.id)
