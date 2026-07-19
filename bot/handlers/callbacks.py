"""
All CallbackQuery handlers — Version 3 (Professional UX & Security Update).

Security model (V3)
-------------------
Every callback that touches a specific group checks that the user is
authorised for that group via _ensure_authorized().  Non-admins see:
  ⛔ ليس لديك صلاحية لاستخدام أدوات الإدارة.

New in V3
---------
- prot namespace: dedicated protection menu with 🟢/🔴 per filter and master switch
- Confirmation step for ban, mute, kick, reset-warns
- Security guard on every group-scoped callback
- Improved message formatting / navigation

Callback data format:  <namespace>:<action>[:<args...>]

Namespaces
----------
menu    – top-level navigation
grp     – group panel actions
prot    – V3 protection menu
mod     – advanced moderation section
filter  – filter configuration
settings – group settings
member  – member actions (with confirmations)
admin   – admin management
ch      – channel actions

Future: paginated logs, warning history pagination, plugin hook points.
"""

from __future__ import annotations

from aiogram import Bot, Router, F
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.filters.admin_filter import is_bot_owner_id
from bot.keyboards.builder import (
    admins_list_kb,
    back_kb,
    channel_panel_kb,
    channels_menu_kb,
    confirm_kb,
    filter_action_kb,
    filter_actions_menu_kb,
    filters_list_kb,
    group_list_kb,
    group_panel_kb,
    main_menu_kb,
    member_action_kb,
    moderation_menu_kb,
    protection_menu_kb,
    punishment_kb,
    settings_menu_kb,
    _FILTER_LABELS,
    _ACTION_LABELS,
)
from bot.services import moderation_service as mod
from bot.services.stats_service import build_stats_text, refresh_member_count
from bot.services.warning_service import warn_user
from bot.strings.ar import S
from database import repository as repo
from bot.security import ensure_authorized
from utils.helpers import escape_html, format_datetime_ar, mention_html
from utils.logger import get_logger

log = get_logger(__name__)
router = Router(name="callbacks")


# ---------------------------------------------------------------------------
# FSM states
# ---------------------------------------------------------------------------

class SettingsState(StatesGroup):
    waiting_for_welcome_text = State()
    waiting_for_warn_limit   = State()


# ---------------------------------------------------------------------------
# Core helpers
# ---------------------------------------------------------------------------

async def _answer(cb: CallbackQuery, text: str = "✅") -> None:
    try:
        await cb.answer(text)
    except Exception:
        pass


async def _answer_alert(cb: CallbackQuery, text: str) -> None:
    try:
        await cb.answer(text, show_alert=True)
    except Exception:
        pass


async def _edit(cb: CallbackQuery, text: str, reply_markup=None) -> None:
    try:
        await cb.message.edit_text(text, parse_mode="HTML", reply_markup=reply_markup)
    except TelegramBadRequest:
        pass


# _ensure_authorized removed — use bot.security.ensure_authorized (live Telegram API check).


# ---------------------------------------------------------------------------
# menu namespace
# ---------------------------------------------------------------------------

@router.callback_query(F.data == "menu:home")
async def cb_home(cb: CallbackQuery, bot: Bot, session: AsyncSession) -> None:
    await _answer(cb)
    groups = await repo.get_groups_for_user(session, cb.from_user.id)
    name = escape_html(cb.from_user.first_name)
    if groups:
        title = S.home_title.format(name=name, group=escape_html(groups[0].title))
    else:
        title = S.home_title_no_group.format(name=name)
    await _edit(cb, title, reply_markup=main_menu_kb(groups, is_bot_owner=is_bot_owner_id(cb.from_user.id)))


@router.callback_query(F.data == "menu:groups")
async def cb_groups(cb: CallbackQuery, bot: Bot, session: AsyncSession) -> None:
    await _answer(cb)
    groups = await repo.get_groups_for_user(session, cb.from_user.id)
    if not groups:
        await _edit(cb, S.no_groups_yet, reply_markup=back_kb("menu:home"))
        return
    await _edit(cb, S.groups_title, reply_markup=group_list_kb(groups))


@router.callback_query(F.data == "menu:channels")
async def cb_channels(cb: CallbackQuery, bot: Bot, session: AsyncSession) -> None:
    await _answer(cb)
    channels = await repo.get_channels_for_user(session, cb.from_user.id)
    if not channels:
        await _edit(cb, S.channels_none, reply_markup=back_kb("menu:home"))
        return
    await _edit(cb, S.channels_title, reply_markup=channels_menu_kb(channels))


@router.callback_query(F.data == "menu:stats_global")
async def cb_stats_global(cb: CallbackQuery, bot: Bot, session: AsyncSession) -> None:
    await _answer(cb)
    groups = await repo.get_groups_for_user(session, cb.from_user.id)
    if not groups:
        await _edit(cb, S.stats_no_data, reply_markup=back_kb("menu:home"))
        return
    g = groups[0]
    rows = await repo.get_stats(session, g.group_id, days=7)
    text = build_stats_text(rows, g.title)
    await _edit(cb, text, reply_markup=back_kb("menu:home"))


@router.callback_query(F.data == "menu:help")
async def cb_help(cb: CallbackQuery) -> None:
    await _answer(cb)
    await _edit(cb, S.help_text, reply_markup=back_kb("menu:home"))


# ---------------------------------------------------------------------------
# grp namespace
# ---------------------------------------------------------------------------

@router.callback_query(F.data.startswith("grp:select:"))
async def cb_grp_select(cb: CallbackQuery, bot: Bot, session: AsyncSession) -> None:
    await _answer(cb)
    group_id = int(cb.data.split(":")[2])

    if not await ensure_authorized(cb, bot, session, group_id):
        return

    group = await repo.get_group(session, group_id)
    if not group:
        await _edit(cb, S.not_found, reply_markup=back_kb("menu:groups"))
        return
    await _edit(
        cb,
        S.group_panel_title.format(title=escape_html(group.title)),
        reply_markup=group_panel_kb(group_id),
    )


@router.callback_query(F.data.startswith("grp:panel:"))
async def cb_grp_panel(cb: CallbackQuery, bot: Bot, session: AsyncSession) -> None:
    await _answer(cb)
    group_id = int(cb.data.split(":")[2])

    if not await ensure_authorized(cb, bot, session, group_id):
        return

    group = await repo.get_group(session, group_id)
    if not group:
        await _edit(cb, S.not_found, reply_markup=back_kb("menu:groups"))
        return
    await _edit(
        cb,
        S.group_panel_title.format(title=escape_html(group.title)),
        reply_markup=group_panel_kb(group_id),
    )


@router.callback_query(F.data.startswith("grp:mod:"))
async def cb_grp_mod(cb: CallbackQuery, bot: Bot, session: AsyncSession) -> None:
    """Advanced moderation section (full filter list)."""
    await _answer(cb)
    group_id = int(cb.data.split(":")[2])

    if not await ensure_authorized(cb, bot, session, group_id):
        return

    group   = await repo.get_group(session, group_id)
    filters = await repo.get_filters(session, group_id)
    title   = escape_html(group.title) if group else str(group_id)
    await _edit(
        cb,
        S.mod_title.format(title=title),
        reply_markup=moderation_menu_kb(group_id, filters),
    )


@router.callback_query(F.data.startswith("grp:settings:"))
async def cb_grp_settings(cb: CallbackQuery, bot: Bot, session: AsyncSession) -> None:
    """V4: redirect to the Advanced Settings Center."""
    await _answer(cb)
    group_id = int(cb.data.split(":")[2])

    if not await ensure_authorized(cb, bot, session, group_id):
        return

    # Delegate to V4 settings menu — reuse its rendering directly
    from bot.keyboards.builder import v4_settings_menu_kb

    group = await repo.get_group(session, group_id)
    title = escape_html(group.title) if group else str(group_id)
    await _edit(
        cb,
        S.v4_settings_title.format(title=title),
        reply_markup=v4_settings_menu_kb(group_id),
    )


@router.callback_query(F.data.startswith("grp:stats:"))
async def cb_grp_stats(cb: CallbackQuery, bot: Bot, session: AsyncSession) -> None:
    await _answer(cb)
    group_id = int(cb.data.split(":")[2])

    if not await ensure_authorized(cb, bot, session, group_id):
        return

    group = await repo.get_group(session, group_id)
    await refresh_member_count(bot, session, group_id)
    rows = await repo.get_stats(session, group_id, days=7)
    text = build_stats_text(rows, group.title if group else str(group_id))
    await _edit(cb, text, reply_markup=back_kb(f"grp:panel:{group_id}"))


@router.callback_query(F.data.startswith("grp:logs:"))
async def cb_grp_logs(cb: CallbackQuery, bot: Bot, session: AsyncSession) -> None:
    await _answer(cb)
    group_id = int(cb.data.split(":")[2])

    if not await ensure_authorized(cb, bot, session, group_id):
        return

    logs = await repo.get_recent_logs(session, group_id, limit=15)

    event_labels: dict[str, str] = {
        "user_joined":      S.log_user_joined,
        "user_left":        S.log_user_left,
        "user_banned":      S.log_user_banned,
        "user_unbanned":    S.log_user_unbanned,
        "user_muted":       S.log_user_muted,
        "user_unmuted":     S.log_user_unmuted,
        "user_warned":      S.log_user_warned,
        "message_deleted":  S.log_message_deleted,
        "message_pinned":   S.log_message_pinned,
        "message_unpinned": S.log_message_unpinned,
        "settings_changed": S.log_settings_changed,
        "filter_triggered": S.log_filter_triggered,
        "bot_added":        S.log_bot_added,
        "bot_removed":      S.log_bot_removed,
    }

    if not logs:
        await _edit(cb, S.logs_none, reply_markup=back_kb(f"grp:panel:{group_id}"))
        return

    lines = [S.logs_title, ""]
    for entry in logs:
        label  = event_labels.get(entry.event_type, entry.event_type)
        ts     = format_datetime_ar(entry.created_at)
        detail = f" — {escape_html(entry.details[:60])}" if entry.details else ""
        lines.append(f"• <b>{label}</b> [{ts}]{detail}")

    await _edit(cb, "\n".join(lines), reply_markup=back_kb(f"grp:panel:{group_id}"))


@router.callback_query(F.data.startswith("grp:members:"))
async def cb_grp_members(cb: CallbackQuery, bot: Bot, session: AsyncSession) -> None:
    await _answer(cb)
    group_id = int(cb.data.split(":")[2])

    if not await ensure_authorized(cb, bot, session, group_id):
        return

    await _edit(cb, S.members_title, reply_markup=back_kb(f"grp:panel:{group_id}"))


@router.callback_query(F.data.startswith("grp:admins:"))
async def cb_grp_admins(cb: CallbackQuery, bot: Bot, session: AsyncSession) -> None:
    await _answer(cb)
    group_id = int(cb.data.split(":")[2])

    if not await ensure_authorized(cb, bot, session, group_id):
        return

    admins = await repo.get_admins(session, group_id)
    if not admins:
        await _edit(cb, S.admins_no_extra, reply_markup=back_kb(f"grp:panel:{group_id}"))
        return
    admin_ids = [a.user_id for a in admins]
    await _edit(cb, S.admins_title, reply_markup=admins_list_kb(group_id, admin_ids))


# ---------------------------------------------------------------------------
# prot namespace — V3 Protection Menu
# ---------------------------------------------------------------------------

@router.callback_query(F.data.startswith("prot:menu:"))
async def cb_prot_menu(cb: CallbackQuery, bot: Bot, session: AsyncSession) -> None:
    """Show the V3 protection menu with 🟢/🔴 per filter."""
    await _answer(cb)
    group_id = int(cb.data.split(":")[2])

    if not await ensure_authorized(cb, bot, session, group_id):
        return

    filters  = await repo.get_filters(session, group_id)
    settings = await repo.get_settings(session, group_id)
    auto     = settings.auto_protect_enabled if settings else False

    # Build the filter status lines for the header — must match _PROT_FILTERS in builder.py
    _PROT_MAP = [
        ("telegram_links",     S.filter_telegram_links),
        ("duplicate_messages", S.filter_duplicates),
        ("advertisement",      S.filter_advertisement),
        ("flood",              S.filter_flood),
        ("bad_words",          S.filter_bad_words),
    ]
    fmap = {f.filter_type: f for f in filters}
    lines = []
    for ft, label in _PROT_MAP:
        f  = fmap.get(ft)
        st = (S.on if f and f.enabled else S.off)
        lines.append(f"{st} {label}")

    auto_line = f"{S.on if auto else S.off} التفعيل التلقائي"
    lines.append(auto_line)

    text = S.protection_title.format(filters="\n".join(lines) + "\n")
    await _edit(cb, text, reply_markup=protection_menu_kb(group_id, filters, auto))


@router.callback_query(F.data.startswith("prot:toggle:"))
async def cb_prot_toggle(cb: CallbackQuery, bot: Bot, session: AsyncSession) -> None:
    """Toggle a single quick-protection filter."""
    await _answer(cb)
    parts     = cb.data.split(":")  # prot:toggle:{group_id}:{filter_type}
    group_id  = int(parts[2])
    ft        = parts[3]

    if not await ensure_authorized(cb, bot, session, group_id):
        return

    f = await repo.get_filter(session, group_id, ft)
    if not f:
        return
    new_state = not f.enabled
    await repo.update_filter(session, group_id, ft, enabled=new_state)

    # If toggling links, also toggle external_links in sync
    if ft == "telegram_links":
        await repo.update_filter(session, group_id, "external_links", enabled=new_state)

    await repo.add_log(
        session, group_id=group_id, event_type="settings_changed",
        actor_id=cb.from_user.id,
        details=f"prot filter {ft} → {'on' if new_state else 'off'}",
    )

    # Reload and re-render
    filters  = await repo.get_filters(session, group_id)
    settings = await repo.get_settings(session, group_id)
    auto     = settings.auto_protect_enabled if settings else False

    _PROT_MAP = [
        ("telegram_links",     S.filter_telegram_links),
        ("duplicate_messages", S.filter_duplicates),
        ("advertisement",      S.filter_advertisement),
        ("flood",              S.filter_flood),
        ("bad_words",          S.filter_bad_words),
    ]
    fmap  = {f.filter_type: f for f in filters}
    lines = []
    for ft2, label in _PROT_MAP:
        f2 = fmap.get(ft2)
        st = (S.on if f2 and f2.enabled else S.off)
        lines.append(f"{st} {label}")
    auto_line = f"{S.on if auto else S.off} التفعيل التلقائي"
    lines.append(auto_line)
    text = S.protection_title.format(filters="\n".join(lines) + "\n")
    await _edit(cb, text, reply_markup=protection_menu_kb(group_id, filters, auto))


@router.callback_query(F.data.startswith("prot:auto:"))
async def cb_prot_auto(cb: CallbackQuery, bot: Bot, session: AsyncSession) -> None:
    """Master auto-protection switch: enable/disable all key filters at once."""
    await _answer(cb)
    group_id = int(cb.data.split(":")[2])

    if not await ensure_authorized(cb, bot, session, group_id):
        return

    settings  = await repo.get_settings(session, group_id)
    current   = settings.auto_protect_enabled if settings else False
    new_state = not current

    # Toggle all filters
    await repo.toggle_all_filters(session, group_id, enabled=new_state)
    # Save master switch state
    await repo.update_settings(session, group_id, auto_protect_enabled=new_state)

    await repo.add_log(
        session, group_id=group_id, event_type="settings_changed",
        actor_id=cb.from_user.id,
        details=f"auto_protect → {'on' if new_state else 'off'}",
    )

    msg = S.auto_protect_enabled_msg if new_state else S.auto_protect_disabled_msg
    await _answer_alert(cb, msg)

    # Re-render protection menu
    filters  = await repo.get_filters(session, group_id)
    _PROT_MAP = [
        ("telegram_links",     S.filter_telegram_links),
        ("duplicate_messages", S.filter_duplicates),
        ("advertisement",      S.filter_advertisement),
        ("flood",              S.filter_flood),
        ("bad_words",          S.filter_bad_words),
    ]
    fmap  = {f.filter_type: f for f in filters}
    lines = []
    for ft, label in _PROT_MAP:
        f  = fmap.get(ft)
        st = (S.on if f and f.enabled else S.off)
        lines.append(f"{st} {label}")
    auto_line = f"{S.on if new_state else S.off} التفعيل التلقائي"
    lines.append(auto_line)
    text = S.protection_title.format(filters="\n".join(lines) + "\n")
    await _edit(cb, text, reply_markup=protection_menu_kb(group_id, filters, new_state))


# ---------------------------------------------------------------------------
# mod namespace (advanced — full filter list)
# ---------------------------------------------------------------------------

@router.callback_query(F.data.startswith("mod:filters:"))
async def cb_mod_filters(cb: CallbackQuery, bot: Bot, session: AsyncSession) -> None:
    await _answer(cb)
    group_id = int(cb.data.split(":")[2])

    if not await ensure_authorized(cb, bot, session, group_id):
        return

    filters = await repo.get_filters(session, group_id)
    await _edit(cb, S.filters_title, reply_markup=filters_list_kb(group_id, filters))


@router.callback_query(F.data.startswith("mod:actions:"))
async def cb_mod_actions(cb: CallbackQuery, bot: Bot, session: AsyncSession) -> None:
    await _answer(cb)
    group_id = int(cb.data.split(":")[2])

    if not await ensure_authorized(cb, bot, session, group_id):
        return

    filters = await repo.get_filters(session, group_id)
    await _edit(cb, S.filter_actions_title, reply_markup=filter_actions_menu_kb(group_id, filters))


@router.callback_query(F.data.startswith("mod:warnlimit:"))
async def cb_mod_warnlimit(cb: CallbackQuery, bot: Bot, session: AsyncSession, state: FSMContext) -> None:
    await _answer(cb)
    group_id = int(cb.data.split(":")[2])

    if not await ensure_authorized(cb, bot, session, group_id):
        return

    settings = await repo.get_settings(session, group_id)
    current  = settings.warning_limit if settings else 3
    await state.update_data(group_id=group_id)
    await state.set_state(SettingsState.waiting_for_warn_limit)
    await _edit(
        cb,
        S.warn_limit_prompt.format(current=current),
        reply_markup=back_kb(f"grp:mod:{group_id}"),
    )


# ---------------------------------------------------------------------------
# filter namespace
# ---------------------------------------------------------------------------

@router.callback_query(F.data.startswith("filter:toggle:"))
async def cb_filter_toggle(cb: CallbackQuery, bot: Bot, session: AsyncSession) -> None:
    await _answer(cb)
    _, _, group_id_str, filter_type = cb.data.split(":", 3)
    group_id = int(group_id_str)

    if not await ensure_authorized(cb, bot, session, group_id):
        return

    f = await repo.get_filter(session, group_id, filter_type)
    if not f:
        return
    new_state = not f.enabled
    await repo.update_filter(session, group_id, filter_type, enabled=new_state)
    await repo.add_log(
        session, group_id=group_id, event_type="settings_changed",
        actor_id=cb.from_user.id,
        details=f"filter {filter_type} → {'on' if new_state else 'off'}",
    )
    filters = await repo.get_filters(session, group_id)
    await _edit(cb, S.filters_title, reply_markup=filters_list_kb(group_id, filters))


@router.callback_query(F.data.startswith("filter:actions:"))
async def cb_filter_actions(cb: CallbackQuery, bot: Bot, session: AsyncSession) -> None:
    await _answer(cb)
    group_id = int(cb.data.split(":")[2])

    if not await ensure_authorized(cb, bot, session, group_id):
        return

    filters = await repo.get_filters(session, group_id)
    await _edit(cb, S.filter_actions_title, reply_markup=filter_actions_menu_kb(group_id, filters))


@router.callback_query(F.data.startswith("filter:editaction:"))
async def cb_filter_editaction(cb: CallbackQuery, bot: Bot, session: AsyncSession) -> None:
    await _answer(cb)
    _, _, group_id_str, filter_type = cb.data.split(":", 3)
    group_id = int(group_id_str)

    if not await ensure_authorized(cb, bot, session, group_id):
        return

    f = await repo.get_filter(session, group_id, filter_type)
    if not f:
        return
    fname  = _FILTER_LABELS.get(filter_type, filter_type)
    faction = _ACTION_LABELS.get(f.action, f.action)
    await _edit(
        cb,
        S.filter_edit_action_title.format(name=fname, action=faction),
        reply_markup=filter_action_kb(group_id, filter_type, f.action),
    )


@router.callback_query(F.data.startswith("filter:setaction:"))
async def cb_filter_setaction(cb: CallbackQuery, bot: Bot, session: AsyncSession) -> None:
    await _answer(cb)
    parts       = cb.data.split(":")
    group_id    = int(parts[2])
    filter_type = parts[3]
    action      = parts[4]

    if not await ensure_authorized(cb, bot, session, group_id):
        return

    await repo.update_filter(session, group_id, filter_type, action=action)
    await repo.add_log(
        session, group_id=group_id, event_type="settings_changed",
        actor_id=cb.from_user.id,
        details=f"filter {filter_type} action → {action}",
    )
    fname  = _FILTER_LABELS.get(filter_type, filter_type)
    faction = _ACTION_LABELS.get(action, action)
    await _edit(
        cb,
        S.action_set_ok.format(filter=fname, action=faction),
        reply_markup=filter_action_kb(group_id, filter_type, action),
    )


# ---------------------------------------------------------------------------
# settings namespace
# ---------------------------------------------------------------------------

@router.callback_query(F.data.startswith("settings:toggle_welcome:"))
async def cb_toggle_welcome(cb: CallbackQuery, bot: Bot, session: AsyncSession) -> None:
    await _answer(cb)
    group_id = int(cb.data.split(":")[2])

    if not await ensure_authorized(cb, bot, session, group_id):
        return

    settings = await repo.get_settings(session, group_id)
    if not settings:
        return
    new_val = not settings.welcome_enabled
    await repo.update_settings(session, group_id, welcome_enabled=new_val)
    await repo.add_log(
        session, group_id=group_id, event_type="settings_changed",
        actor_id=cb.from_user.id, details=f"welcome_enabled → {new_val}",
    )
    updated = await repo.get_settings(session, group_id)
    group   = await repo.get_group(session, group_id)
    title   = escape_html(group.title) if group else str(group_id)
    await _edit(
        cb,
        S.settings_title.format(title=title),
        reply_markup=settings_menu_kb(group_id, updated.welcome_enabled, updated.log_events),
    )


@router.callback_query(F.data.startswith("settings:toggle_logs:"))
async def cb_toggle_logs(cb: CallbackQuery, bot: Bot, session: AsyncSession) -> None:
    await _answer(cb)
    group_id = int(cb.data.split(":")[2])

    if not await ensure_authorized(cb, bot, session, group_id):
        return

    settings = await repo.get_settings(session, group_id)
    if not settings:
        return
    new_val = not settings.log_events
    await repo.update_settings(session, group_id, log_events=new_val)
    updated = await repo.get_settings(session, group_id)
    group   = await repo.get_group(session, group_id)
    title   = escape_html(group.title) if group else str(group_id)
    await _edit(
        cb,
        S.settings_title.format(title=title),
        reply_markup=settings_menu_kb(group_id, updated.welcome_enabled, updated.log_events),
    )


@router.callback_query(F.data.startswith("settings:edit_welcome:"))
async def cb_edit_welcome(cb: CallbackQuery, bot: Bot, session: AsyncSession, state: FSMContext) -> None:
    await _answer(cb)
    group_id = int(cb.data.split(":")[2])

    if not await ensure_authorized(cb, bot, session, group_id):
        return

    settings = await repo.get_settings(session, group_id)
    current  = settings.welcome_text if settings else ""
    await state.update_data(group_id=group_id)
    await state.set_state(SettingsState.waiting_for_welcome_text)
    await _edit(
        cb,
        S.welcome_edit_prompt.format(current=escape_html(current)),
        reply_markup=back_kb(f"grp:settings:{group_id}"),
    )


@router.callback_query(F.data.startswith("settings:punishment:"))
async def cb_punishment(cb: CallbackQuery, bot: Bot, session: AsyncSession) -> None:
    await _answer(cb)
    group_id = int(cb.data.split(":")[2])

    if not await ensure_authorized(cb, bot, session, group_id):
        return

    settings = await repo.get_settings(session, group_id)
    current  = settings.auto_punishment if settings else "mute"
    await _edit(cb, S.punishment_title, reply_markup=punishment_kb(group_id, current))


@router.callback_query(F.data.startswith("settings:setpunishment:"))
async def cb_set_punishment(cb: CallbackQuery, bot: Bot, session: AsyncSession) -> None:
    await _answer(cb)
    parts      = cb.data.split(":")
    group_id   = int(parts[2])
    punishment = parts[3]

    if not await ensure_authorized(cb, bot, session, group_id):
        return

    await repo.update_settings(session, group_id, auto_punishment=punishment)
    await repo.add_log(
        session, group_id=group_id, event_type="settings_changed",
        actor_id=cb.from_user.id, details=f"auto_punishment → {punishment}",
    )
    p_labels = {"mute": S.punishment_mute, "kick": S.punishment_kick, "ban": S.punishment_ban}
    await _edit(
        cb,
        S.punishment_set.format(p=p_labels.get(punishment, punishment)),
        reply_markup=punishment_kb(group_id, punishment),
    )


@router.callback_query(F.data.startswith("settings:warnlimit:"))
async def cb_settings_warnlimit(cb: CallbackQuery, bot: Bot, session: AsyncSession, state: FSMContext) -> None:
    await _answer(cb)
    group_id = int(cb.data.split(":")[2])

    if not await ensure_authorized(cb, bot, session, group_id):
        return

    settings = await repo.get_settings(session, group_id)
    current  = settings.warning_limit if settings else 3
    await state.update_data(group_id=group_id)
    await state.set_state(SettingsState.waiting_for_warn_limit)
    await _edit(
        cb,
        S.warn_limit_prompt.format(current=current),
        reply_markup=back_kb(f"grp:settings:{group_id}"),
    )


# ---------------------------------------------------------------------------
# FSM: text input handlers
# ---------------------------------------------------------------------------

@router.message(SettingsState.waiting_for_welcome_text)
async def fsm_welcome_text(message: Message, session: AsyncSession, state: FSMContext) -> None:
    data     = await state.get_data()
    group_id = data.get("group_id")
    await state.clear()
    text = message.text or ""
    if not text or not group_id:
        await message.reply(S.error)
        return
    await repo.update_settings(session, group_id, welcome_text=text)
    await message.reply(
        S.welcome_updated.format(text=escape_html(text)),
        parse_mode="HTML",
    )


@router.message(SettingsState.waiting_for_warn_limit)
async def fsm_warn_limit(message: Message, session: AsyncSession, state: FSMContext) -> None:
    data     = await state.get_data()
    group_id = data.get("group_id")
    await state.clear()
    text = (message.text or "").strip()
    if not text.isdigit() or not (1 <= int(text) <= 20):
        await message.reply(S.warn_limit_invalid)
        return
    limit = int(text)
    await repo.update_settings(session, group_id, warning_limit=limit)
    await message.reply(S.warn_limit_set.format(limit=limit), parse_mode="HTML")


# ---------------------------------------------------------------------------
# member namespace — with V3 confirmation step for destructive actions
# ---------------------------------------------------------------------------

@router.callback_query(F.data.startswith("member:ban:"))
async def cb_member_ban(cb: CallbackQuery, bot: Bot, session: AsyncSession) -> None:
    """Show confirmation before banning."""
    await _answer(cb)
    parts    = cb.data.split(":")
    group_id = int(parts[2])
    user_id  = int(parts[3])

    if not await ensure_authorized(cb, bot, session, group_id):
        return

    await _edit(
        cb,
        S.confirm_ban,
        reply_markup=confirm_kb(
            yes_data=f"member:ban_do:{group_id}:{user_id}",
            no_data=f"grp:members:{group_id}",
        ),
    )


@router.callback_query(F.data.startswith("member:ban_do:"))
async def cb_member_ban_do(cb: CallbackQuery, bot: Bot, session: AsyncSession) -> None:
    await _answer(cb, "جارٍ الحظر…")
    parts    = cb.data.split(":")
    group_id = int(parts[2])
    user_id  = int(parts[3])

    if not await ensure_authorized(cb, bot, session, group_id):
        return

    success = await mod.ban_user(bot, session, chat_id=group_id, user_id=user_id,
                                  actor_id=cb.from_user.id)
    await _edit(
        cb,
        S.member_banned if success else S.member_ban_fail,
        reply_markup=back_kb(f"grp:members:{group_id}"),
    )


@router.callback_query(F.data.startswith("member:unban:"))
async def cb_member_unban(cb: CallbackQuery, bot: Bot, session: AsyncSession) -> None:
    await _answer(cb, "جارٍ رفع الحظر…")
    _, _, group_id_str, user_id_str = cb.data.split(":")
    group_id, user_id = int(group_id_str), int(user_id_str)

    if not await ensure_authorized(cb, bot, session, group_id):
        return

    success = await mod.unban_user(bot, session, chat_id=group_id, user_id=user_id,
                                    actor_id=cb.from_user.id)
    await _edit(
        cb,
        S.member_unbanned if success else S.member_unban_fail,
        reply_markup=back_kb(f"grp:members:{group_id}"),
    )


@router.callback_query(F.data.startswith("member:mute:"))
async def cb_member_mute(cb: CallbackQuery, bot: Bot, session: AsyncSession) -> None:
    """Show confirmation before muting."""
    await _answer(cb)
    parts    = cb.data.split(":")
    group_id = int(parts[2])
    user_id  = int(parts[3])
    duration = parts[4] if len(parts) > 4 else "3600"

    if not await ensure_authorized(cb, bot, session, group_id):
        return

    await _edit(
        cb,
        S.confirm_mute,
        reply_markup=confirm_kb(
            yes_data=f"member:mute_do:{group_id}:{user_id}:{duration}",
            no_data=f"grp:members:{group_id}",
        ),
    )


@router.callback_query(F.data.startswith("member:mute_do:"))
async def cb_member_mute_do(cb: CallbackQuery, bot: Bot, session: AsyncSession) -> None:
    await _answer(cb, "جارٍ الكتم…")
    parts    = cb.data.split(":")
    group_id = int(parts[2])
    user_id  = int(parts[3])
    duration = int(parts[4])

    if not await ensure_authorized(cb, bot, session, group_id):
        return

    success = await mod.mute_user(bot, session, chat_id=group_id, user_id=user_id,
                                   duration_seconds=duration, actor_id=cb.from_user.id)
    await _edit(
        cb,
        S.member_muted if success else S.member_mute_fail,
        reply_markup=back_kb(f"grp:members:{group_id}"),
    )


@router.callback_query(F.data.startswith("member:unmute:"))
async def cb_member_unmute(cb: CallbackQuery, bot: Bot, session: AsyncSession) -> None:
    await _answer(cb, "جارٍ رفع الكتم…")
    _, _, group_id_str, user_id_str = cb.data.split(":")
    group_id, user_id = int(group_id_str), int(user_id_str)

    if not await ensure_authorized(cb, bot, session, group_id):
        return

    success = await mod.unmute_user(bot, session, chat_id=group_id, user_id=user_id,
                                     actor_id=cb.from_user.id)
    await _edit(
        cb,
        S.member_unmuted if success else S.member_unmute_fail,
        reply_markup=back_kb(f"grp:members:{group_id}"),
    )


@router.callback_query(F.data.startswith("member:warn:"))
async def cb_member_warn(cb: CallbackQuery, bot: Bot, session: AsyncSession) -> None:
    await _answer(cb, "جارٍ التحذير…")
    _, _, group_id_str, user_id_str = cb.data.split(":")
    group_id, user_id = int(group_id_str), int(user_id_str)

    if not await ensure_authorized(cb, bot, session, group_id):
        return

    count, limit, punished = await warn_user(
        bot, session, chat_id=group_id, user_id=user_id, actor_id=cb.from_user.id,
    )
    msg = (S.member_warned_punished if punished else S.member_warned).format(
        count=count, limit=limit
    )
    await _edit(cb, msg, reply_markup=back_kb(f"grp:members:{group_id}"))


@router.callback_query(F.data.startswith("member:resetwarns:"))
async def cb_member_resetwarns(cb: CallbackQuery, bot: Bot, session: AsyncSession) -> None:
    """Show confirmation before resetting warnings."""
    await _answer(cb)
    _, _, group_id_str, user_id_str = cb.data.split(":")
    group_id, user_id = int(group_id_str), int(user_id_str)

    if not await ensure_authorized(cb, bot, session, group_id):
        return

    await _edit(
        cb,
        S.confirm_reset,
        reply_markup=confirm_kb(
            yes_data=f"member:resetwarns_do:{group_id}:{user_id}",
            no_data=f"grp:members:{group_id}",
        ),
    )


@router.callback_query(F.data.startswith("member:resetwarns_do:"))
async def cb_member_resetwarns_do(cb: CallbackQuery, bot: Bot, session: AsyncSession) -> None:
    await _answer(cb)
    _, _, group_id_str, user_id_str = cb.data.split(":")
    group_id, user_id = int(group_id_str), int(user_id_str)

    if not await ensure_authorized(cb, bot, session, group_id):
        return

    await repo.reset_warnings(session, group_id, user_id)
    await _edit(cb, S.member_warns_reset, reply_markup=back_kb(f"grp:members:{group_id}"))


@router.callback_query(F.data.startswith("member:warnhist:"))
async def cb_member_warnhist(cb: CallbackQuery, bot: Bot, session: AsyncSession) -> None:
    """Show the warning history for a member."""
    await _answer(cb)
    _, _, group_id_str, user_id_str = cb.data.split(":")
    group_id, user_id = int(group_id_str), int(user_id_str)

    if not await ensure_authorized(cb, bot, session, group_id):
        return

    history = await repo.get_warning_history(session, group_id, user_id, limit=10)

    if not history:
        await _edit(
            cb,
            S.warn_history_title + S.warn_history_none,
            reply_markup=back_kb(f"grp:members:{group_id}"),
        )
        return

    lines = [S.warn_history_title]
    for entry in history:
        ts     = format_datetime_ar(entry.created_at)
        reason = escape_html(entry.reason or "—")
        actor  = f"<code>{entry.actor_id}</code>" if entry.actor_id else "البوت"
        lines.append(S.warn_history_entry.format(date=ts, reason=reason, actor=actor))

    await _edit(cb, "".join(lines), reply_markup=back_kb(f"grp:members:{group_id}"))


# ---------------------------------------------------------------------------
# Channel namespace
# ---------------------------------------------------------------------------

@router.callback_query(F.data.startswith("ch:select:"))
async def cb_ch_select(cb: CallbackQuery, bot: Bot, session: AsyncSession) -> None:
    await _answer(cb)
    channel_id = int(cb.data.split(":")[2])
    channel    = await repo.get_channel(session, channel_id)
    if not channel:
        await _edit(cb, S.not_found, reply_markup=back_kb("menu:channels"))
        return
    # Security: only the channel owner may open its panel
    if channel.owner_id != cb.from_user.id:
        await _answer_alert(cb, S.no_permission_cb)
        return
    await _edit(
        cb,
        f"📢 <b>{escape_html(channel.title)}</b>",
        reply_markup=channel_panel_kb(channel_id),
    )


@router.callback_query(F.data.startswith("ch:pin:"))
async def cb_ch_pin(cb: CallbackQuery, bot: Bot, session: AsyncSession) -> None:
    channel_id = int(cb.data.split(":")[2])
    channel    = await repo.get_channel(session, channel_id)
    if not channel or channel.owner_id != cb.from_user.id:
        await _answer_alert(cb, S.no_permission_cb)
        return
    await _answer(cb, "استخدم /pin داخل القناة لتثبيت آخر منشور.")
