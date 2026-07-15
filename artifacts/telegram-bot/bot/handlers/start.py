"""
/start command handler — Version 3.1 (Security hardened).

Handles:
  - Plain /start  → show home dashboard
  - /start grp_{group_id}  → deep link from "➕ إدارة هذه المجموعة" button in group.

Security (V3.1)
---------------
The deep link handler now ALWAYS verifies the user's actual Telegram role via
get_chat_member() before granting any panel access or writing to the DB.
A member who simply obtains or guesses a grp_XXXX URL is denied immediately.
Owner auto-assignment only fires when the Telegram API confirms the user is
the group "creator" AND the group currently has no owner in the DB.
"""

from __future__ import annotations

from aiogram import Bot, Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.filters.admin_filter import is_bot_owner_id
from bot.keyboards.builder import group_panel_kb, main_menu_kb
from bot.strings.ar import S
from database import repository as repo
from utils.helpers import escape_html
from utils.logger import get_logger

log = get_logger(__name__)
router = Router(name="start")


@router.message(CommandStart())
async def cmd_start(message: Message, bot: Bot, session: AsyncSession) -> None:
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
    # V3.1: Deep link handling — /start grp_{group_id}
    # SECURITY: Always verify Telegram membership before any DB write.
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
                # ── Step 1: Verify actual Telegram role via live API ──────────
                # Never trust the deep link alone — anyone can construct a URL.
                try:
                    member = await bot.get_chat_member(group_id, user.id)
                    tg_status = member.status  # "creator" | "administrator" | "member" | ...
                except Exception as exc:
                    log.warning(
                        "deep_link: get_chat_member failed user=%s group=%s: %s",
                        user.id, group_id, exc,
                    )
                    await message.answer(S.no_permission_cb)
                    return

                if tg_status not in ("creator", "administrator"):
                    log.info(
                        "deep_link: denied user=%s group=%s tg_status=%s (not admin)",
                        user.id, group_id, tg_status,
                    )
                    await message.answer(S.no_permission_cb)
                    return

                # ── Step 2: Auto-assign owner only when safe to do so ─────────
                # Conditions: user IS the Telegram creator AND no DB owner set yet.
                if not group.owner_id and tg_status == "creator":
                    await repo.set_owner(session, group_id, user.id)
                    group = await repo.get_group(session, group_id)
                    log.info(
                        "owner_assigned: group_id=%s user_id=%s via deep link (creator verified)",
                        group_id, user.id,
                    )

                # ── Step 3: DB authorisation check ────────────────────────────
                # The user must be owner or pre-registered admin in the DB.
                if not await repo.is_authorized(session, group_id, user.id):
                    log.info(
                        "deep_link: not in DB as owner/admin user=%s group=%s tg_status=%s",
                        user.id, group_id, tg_status,
                    )
                    await message.answer(S.no_permission_cb)
                    return

                # ── Step 4: Grant access ───────────────────────────────────────
                await message.answer(
                    S.group_linked.format(title=escape_html(group.title)),
                    parse_mode="HTML",
                    reply_markup=group_panel_kb(group_id),
                )
                log.info(
                    "deep_link: user=%s granted panel access group=%s tg_status=%s",
                    user.id, group_id, tg_status,
                )
                return
            else:
                log.warning(
                    "group_lookup: deep link grp_%s referenced by user %s but group not found in DB "
                    "(bot may not be registered for this chat)", group_id, user.id,
                )

    # ------------------------------------------------------------------
    # Normal /start — show home dashboard
    # ------------------------------------------------------------------
    groups = await repo.get_groups_for_user(session, user.id)
    log.info("group_loaded: user_id=%s loaded %d group(s) for dashboard", user.id, len(groups))
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
        reply_markup=main_menu_kb(groups, is_bot_owner=is_bot_owner_id(user.id)),
        parse_mode="HTML",
    )
    log.info("User %s opened the dashboard (v3.1)", user.id)
