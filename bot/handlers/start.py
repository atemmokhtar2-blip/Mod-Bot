"""
/start command handler — Version 4.0 (Security hardened — live permission verification).

Handles:
  - Plain /start  → show home dashboard (live-verified groups only)
  - /start grp_{group_id}  → deep link from "➕ إدارة هذه المجموعة" button in group.

Security (V4.0)
---------------
On every /start invocation — deep link OR plain — the handler:
  1. Clears all FSM state to destroy any previous management session.
  2. Verifies the user's CURRENT Telegram role via getChatMember().
  3. Never trusts cached DB admin records.

Deep link path:
  - Always verifies via live API before granting any panel access.
  - Denies anyone whose Telegram status is not creator/administrator.
  - Owner auto-assignment fires ONLY when the Telegram API confirms "creator"
    AND the group currently has no DB owner.

Plain /start path:
  - Loads groups from DB, then verifies live Telegram role for each group
    where the user is registered as an admin (not owner).
  - Stale admin DB records are pruned automatically for groups where the
    user is no longer a Telegram administrator.
  - Only verified groups appear in the dashboard.
"""

from __future__ import annotations

from aiogram import Bot, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.filters.admin_filter import is_bot_owner_id
from bot.keyboards.builder import group_panel_kb, main_menu_kb
from bot.security import verify_live_tg_permission
from bot.strings.ar import S
from database import repository as repo
from utils.helpers import escape_html
from utils.logger import get_logger

log = get_logger(__name__)
router = Router(name="start")


@router.message(CommandStart())
async def cmd_start(message: Message, bot: Bot, session: AsyncSession, state: FSMContext) -> None:
    """Entry point — works in private chat, handles optional deep link."""
    user = message.from_user
    if not user:
        return

    # ── SECURITY: Destroy every previous management session on /start ────────
    # This prevents any stale FSM state, cached group selection, or old
    # authorization data from carrying over to a new management session.
    await state.clear()
    log.info("session_cleared: user=%s (new /start)", user.id)

    # Upsert user record
    await repo.upsert_user(
        session,
        user_id=user.id,
        first_name=user.first_name,
        last_name=user.last_name,
        username=user.username,
    )

    # ------------------------------------------------------------------
    # V4.0: Deep link handling — /start grp_{group_id}
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
    # SECURITY: Verify live Telegram role for each DB-registered admin group.
    # Groups where the user is no longer a Telegram admin are filtered out
    # and their stale DB records are pruned.
    # ------------------------------------------------------------------
    raw_groups = await repo.get_groups_for_user(session, user.id)
    log.info(
        "dashboard_load: user_id=%s raw_db_groups=%d — verifying live permissions",
        user.id, len(raw_groups),
    )

    verified_groups = []
    for g in raw_groups:
        is_owner_in_db = (g.owner_id == user.id)
        if is_owner_in_db:
            # Owner status was established via deep link with live creator check;
            # Telegram group ownership cannot change, so this is safe.
            verified_groups.append(g)
        else:
            # Admin — verify current Telegram role via live API.
            live_ok = await verify_live_tg_permission(bot, g.group_id, user.id)
            if live_ok:
                verified_groups.append(g)
            else:
                # User was in the DB admins table but is no longer a Telegram admin.
                # Prune the stale record so it doesn't reappear.
                try:
                    await repo.remove_admin(session, g.group_id, user.id)
                    log.info(
                        "stale_admin_pruned_on_start: user=%s group=%s",
                        user.id, g.group_id,
                    )
                except Exception as exc:
                    log.warning(
                        "stale_admin_prune_failed: user=%s group=%s — %s",
                        user.id, g.group_id, exc,
                    )

    groups = verified_groups
    log.info(
        "dashboard_load: user_id=%s verified_groups=%d (pruned %d stale)",
        user.id, len(groups), len(raw_groups) - len(groups),
    )

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
    log.info("User %s opened the dashboard (v4.0 security)", user.id)
