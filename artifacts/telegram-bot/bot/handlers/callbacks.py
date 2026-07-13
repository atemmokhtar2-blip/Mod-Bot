"""
All CallbackQuery handlers — Version 2 (full Arabic UI).

Callback data format:  <namespace>:<action>[:<args...>]

Namespaces
----------
menu    – top-level navigation
grp     – group panel actions
mod     – moderation section
filter  – filter configuration
settings – group settings
member  – member actions
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

from bot.keyboards.builder import (
    admins_list_kb,
    back_kb,
    channel_panel_kb,
    channels_menu_kb,
    filter_action_kb,
    filter_actions_menu_kb,
    filters_list_kb,
    group_list_kb,
    group_panel_kb,
    main_menu_kb,
    member_action_kb,
    moderation_menu_kb,
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
from utils.helpers import escape_html, format_datetime_ar, mention_html
from utils.logger import get_logger

log = get_logger(__name__)
router = Router(name="callbacks")


# ---------------------------------------------------------------------------
# FSM states
# ---------------------------------------------------------------------------

class SettingsState(StatesGroup):
    waiting_for_welcome_text = State()
    waiting_for_warn_limit = State()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _answer(cb: CallbackQuery, text: str = "✅") -> None:
    try:
        await cb.answer(text)
    except Exception:
        pass


async def _edit(cb: CallbackQuery, text: str, reply_markup=None) -> None:
    try:
        await cb.message.edit_text(text, parse_mode="HTML", reply_markup=reply_markup)
    except TelegramBadRequest:
        pass


# ---------------------------------------------------------------------------
# menu namespace
# ---------------------------------------------------------------------------

@router.callback_query(F.data == "menu:home")
async def cb_home(cb: CallbackQuery, session: AsyncSession) -> None:
    await _answer(cb)
    groups = await repo.get_groups_for_user(session, cb.from_user.id)
    await _edit(
        cb,
        S.home_title.format(name=escape_html(cb.from_user.first_name)),
        reply_markup=main_menu_kb(groups),
    )


@router.callback_query(F.data == "menu:groups")
async def cb_groups(cb: CallbackQuery, session: AsyncSession) -> None:
    await _answer(cb)
    groups = await repo.get_groups_for_user(session, cb.from_user.id)
    if not groups:
        await _edit(cb, S.no_groups_yet, reply_markup=back_kb("menu:home"))
        return
    await _edit(cb, S.groups_title, reply_markup=group_list_kb(groups))


@router.callback_query(F.data == "menu:channels")
async def cb_channels(cb: CallbackQuery, session: AsyncSession) -> None:
    await _answer(cb)
    channels = await repo.get_all_channels(session)
    if not channels:
        await _edit(cb, S.channels_none, reply_markup=back_kb("menu:home"))
        return
    await _edit(cb, S.channels_title, reply_markup=channels_menu_kb(channels))


@router.callback_query(F.data == "menu:stats_global")
async def cb_stats_global(cb: CallbackQuery, session: AsyncSession) -> None:
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
async def cb_grp_select(cb: CallbackQuery, session: AsyncSession) -> None:
    await _answer(cb)
    group_id = int(cb.data.split(":")[2])
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
async def cb_grp_panel(cb: CallbackQuery, session: AsyncSession) -> None:
    await _answer(cb)
    group_id = int(cb.data.split(":")[2])
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
async def cb_grp_mod(cb: CallbackQuery, session: AsyncSession) -> None:
    await _answer(cb)
    group_id = int(cb.data.split(":")[2])
    group = await repo.get_group(session, group_id)
    filters = await repo.get_filters(session, group_id)
    title = escape_html(group.title) if group else str(group_id)
    await _edit(
        cb,
        S.mod_title.format(title=title),
        reply_markup=moderation_menu_kb(group_id, filters),
    )


@router.callback_query(F.data.startswith("grp:settings:"))
async def cb_grp_settings(cb: CallbackQuery, session: AsyncSession) -> None:
    await _answer(cb)
    group_id = int(cb.data.split(":")[2])
    group = await repo.get_group(session, group_id)
    settings = await repo.get_settings(session, group_id)
    if not settings:
        await _edit(cb, S.not_found, reply_markup=back_kb(f"grp:panel:{group_id}"))
        return
    title = escape_html(group.title) if group else str(group_id)
    await _edit(
        cb,
        S.settings_title.format(title=title),
        reply_markup=settings_menu_kb(group_id, settings.welcome_enabled, settings.log_events),
    )


@router.callback_query(F.data.startswith("grp:stats:"))
async def cb_grp_stats(cb: CallbackQuery, bot: Bot, session: AsyncSession) -> None:
    await _answer(cb)
    group_id = int(cb.data.split(":")[2])
    group = await repo.get_group(session, group_id)
    await refresh_member_count(bot, session, group_id)
    rows = await repo.get_stats(session, group_id, days=7)
    text = build_stats_text(rows, group.title if group else str(group_id))
    await _edit(cb, text, reply_markup=back_kb(f"grp:panel:{group_id}"))


@router.callback_query(F.data.startswith("grp:logs:"))
async def cb_grp_logs(cb: CallbackQuery, session: AsyncSession) -> None:
    await _answer(cb)
    group_id = int(cb.data.split(":")[2])
    logs = await repo.get_recent_logs(session, group_id, limit=15)

    # Arabic event-type labels
    event_labels: dict[str, str] = {
        "user_joined":       S.log_user_joined,
        "user_left":         S.log_user_left,
        "user_banned":       S.log_user_banned,
        "user_unbanned":     S.log_user_unbanned,
        "user_muted":        S.log_user_muted,
        "user_unmuted":      S.log_user_unmuted,
        "user_warned":       S.log_user_warned,
        "message_deleted":   S.log_message_deleted,
        "message_pinned":    S.log_message_pinned,
        "message_unpinned":  S.log_message_unpinned,
        "settings_changed":  S.log_settings_changed,
        "filter_triggered":  S.log_filter_triggered,
        "bot_added":         S.log_bot_added,
        "bot_removed":       S.log_bot_removed,
    }

    if not logs:
        await _edit(cb, S.logs_none, reply_markup=back_kb(f"grp:panel:{group_id}"))
        return

    lines = [S.logs_title, ""]
    for entry in logs:
        label = event_labels.get(entry.event_type, entry.event_type)
        ts = format_datetime_ar(entry.created_at)
        detail = f" — {escape_html(entry.details[:60])}" if entry.details else ""
        lines.append(f"• <b>{label}</b> [{ts}]{detail}")

    await _edit(cb, "\n".join(lines), reply_markup=back_kb(f"grp:panel:{group_id}"))


@router.callback_query(F.data.startswith("grp:members:"))
async def cb_grp_members(cb: CallbackQuery, session: AsyncSession) -> None:
    await _answer(cb)
    group_id = int(cb.data.split(":")[2])
    await _edit(cb, S.members_title, reply_markup=back_kb(f"grp:panel:{group_id}"))


@router.callback_query(F.data.startswith("grp:admins:"))
async def cb_grp_admins(cb: CallbackQuery, session: AsyncSession) -> None:
    await _answer(cb)
    group_id = int(cb.data.split(":")[2])
    admins = await repo.get_admins(session, group_id)
    if not admins:
        await _edit(cb, S.admins_no_extra, reply_markup=back_kb(f"grp:panel:{group_id}"))
        return
    admin_ids = [a.user_id for a in admins]
    await _edit(cb, S.admins_title, reply_markup=admins_list_kb(group_id, admin_ids))


# ---------------------------------------------------------------------------
# mod namespace
# ---------------------------------------------------------------------------

@router.callback_query(F.data.startswith("mod:filters:"))
async def cb_mod_filters(cb: CallbackQuery, session: AsyncSession) -> None:
    await _answer(cb)
    group_id = int(cb.data.split(":")[2])
    filters = await repo.get_filters(session, group_id)
    await _edit(cb, S.filters_title, reply_markup=filters_list_kb(group_id, filters))


@router.callback_query(F.data.startswith("mod:actions:"))
async def cb_mod_actions(cb: CallbackQuery, session: AsyncSession) -> None:
    await _answer(cb)
    group_id = int(cb.data.split(":")[2])
    filters = await repo.get_filters(session, group_id)
    await _edit(cb, S.filter_actions_title, reply_markup=filter_actions_menu_kb(group_id, filters))


@router.callback_query(F.data.startswith("mod:warnlimit:"))
async def cb_mod_warnlimit(cb: CallbackQuery, session: AsyncSession, state: FSMContext) -> None:
    await _answer(cb)
    group_id = int(cb.data.split(":")[2])
    settings = await repo.get_settings(session, group_id)
    current = settings.warning_limit if settings else 3
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
async def cb_filter_toggle(cb: CallbackQuery, session: AsyncSession) -> None:
    await _answer(cb)
    _, _, group_id_str, filter_type = cb.data.split(":", 3)
    group_id = int(group_id_str)
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
async def cb_filter_actions(cb: CallbackQuery, session: AsyncSession) -> None:
    await _answer(cb)
    group_id = int(cb.data.split(":")[2])
    filters = await repo.get_filters(session, group_id)
    await _edit(cb, S.filter_actions_title, reply_markup=filter_actions_menu_kb(group_id, filters))


@router.callback_query(F.data.startswith("filter:editaction:"))
async def cb_filter_editaction(cb: CallbackQuery, session: AsyncSession) -> None:
    await _answer(cb)
    _, _, group_id_str, filter_type = cb.data.split(":", 3)
    group_id = int(group_id_str)
    f = await repo.get_filter(session, group_id, filter_type)
    if not f:
        return
    fname = _FILTER_LABELS.get(filter_type, filter_type)
    faction = _ACTION_LABELS.get(f.action, f.action)
    await _edit(
        cb,
        S.filter_edit_action_title.format(name=fname, action=faction),
        reply_markup=filter_action_kb(group_id, filter_type, f.action),
    )


@router.callback_query(F.data.startswith("filter:setaction:"))
async def cb_filter_setaction(cb: CallbackQuery, session: AsyncSession) -> None:
    await _answer(cb)
    parts = cb.data.split(":")
    group_id = int(parts[2])
    filter_type = parts[3]
    action = parts[4]
    await repo.update_filter(session, group_id, filter_type, action=action)
    await repo.add_log(
        session, group_id=group_id, event_type="settings_changed",
        actor_id=cb.from_user.id,
        details=f"filter {filter_type} action → {action}",
    )
    fname = _FILTER_LABELS.get(filter_type, filter_type)
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
async def cb_toggle_welcome(cb: CallbackQuery, session: AsyncSession) -> None:
    await _answer(cb)
    group_id = int(cb.data.split(":")[2])
    settings = await repo.get_settings(session, group_id)
    if not settings:
        return
    new_val = not settings.welcome_enabled
    await repo.update_settings(session, group_id, welcome_enabled=new_val)
    await repo.add_log(
        session, group_id=group_id, event_type="settings_changed",
        actor_id=cb.from_user.id,
        details=f"welcome_enabled → {new_val}",
    )
    updated = await repo.get_settings(session, group_id)
    group = await repo.get_group(session, group_id)
    title = escape_html(group.title) if group else str(group_id)
    await _edit(
        cb,
        S.settings_title.format(title=title),
        reply_markup=settings_menu_kb(group_id, updated.welcome_enabled, updated.log_events),
    )


@router.callback_query(F.data.startswith("settings:toggle_logs:"))
async def cb_toggle_logs(cb: CallbackQuery, session: AsyncSession) -> None:
    await _answer(cb)
    group_id = int(cb.data.split(":")[2])
    settings = await repo.get_settings(session, group_id)
    if not settings:
        return
    new_val = not settings.log_events
    await repo.update_settings(session, group_id, log_events=new_val)
    updated = await repo.get_settings(session, group_id)
    group = await repo.get_group(session, group_id)
    title = escape_html(group.title) if group else str(group_id)
    await _edit(
        cb,
        S.settings_title.format(title=title),
        reply_markup=settings_menu_kb(group_id, updated.welcome_enabled, updated.log_events),
    )


@router.callback_query(F.data.startswith("settings:edit_welcome:"))
async def cb_edit_welcome(cb: CallbackQuery, session: AsyncSession, state: FSMContext) -> None:
    await _answer(cb)
    group_id = int(cb.data.split(":")[2])
    settings = await repo.get_settings(session, group_id)
    current = settings.welcome_text if settings else ""
    await state.update_data(group_id=group_id)
    await state.set_state(SettingsState.waiting_for_welcome_text)
    await _edit(
        cb,
        S.welcome_edit_prompt.format(current=escape_html(current)),
        reply_markup=back_kb(f"grp:settings:{group_id}"),
    )


@router.callback_query(F.data.startswith("settings:punishment:"))
async def cb_punishment(cb: CallbackQuery, session: AsyncSession) -> None:
    await _answer(cb)
    group_id = int(cb.data.split(":")[2])
    settings = await repo.get_settings(session, group_id)
    current = settings.auto_punishment if settings else "mute"
    await _edit(cb, S.punishment_title, reply_markup=punishment_kb(group_id, current))


@router.callback_query(F.data.startswith("settings:setpunishment:"))
async def cb_set_punishment(cb: CallbackQuery, session: AsyncSession) -> None:
    await _answer(cb)
    parts = cb.data.split(":")
    group_id = int(parts[2])
    punishment = parts[3]
    await repo.update_settings(session, group_id, auto_punishment=punishment)
    await repo.add_log(
        session, group_id=group_id, event_type="settings_changed",
        actor_id=cb.from_user.id,
        details=f"auto_punishment → {punishment}",
    )
    p_labels = {"mute": S.punishment_mute, "kick": S.punishment_kick, "ban": S.punishment_ban}
    await _edit(
        cb,
        S.punishment_set.format(p=p_labels.get(punishment, punishment)),
        reply_markup=punishment_kb(group_id, punishment),
    )


@router.callback_query(F.data.startswith("settings:warnlimit:"))
async def cb_settings_warnlimit(cb: CallbackQuery, session: AsyncSession, state: FSMContext) -> None:
    await _answer(cb)
    group_id = int(cb.data.split(":")[2])
    settings = await repo.get_settings(session, group_id)
    current = settings.warning_limit if settings else 3
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
    data = await state.get_data()
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
    data = await state.get_data()
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
# member namespace
# ---------------------------------------------------------------------------

@router.callback_query(F.data.startswith("member:ban:"))
async def cb_member_ban(cb: CallbackQuery, bot: Bot, session: AsyncSession) -> None:
    await _answer(cb, "جارٍ الحظر…")
    _, _, group_id_str, user_id_str = cb.data.split(":")
    group_id, user_id = int(group_id_str), int(user_id_str)
    success = await mod.ban_user(bot, session, chat_id=group_id, user_id=user_id,
                                  actor_id=cb.from_user.id)
    await _edit(cb,
                S.member_banned if success else S.member_ban_fail,
                reply_markup=back_kb(f"grp:members:{group_id}"))


@router.callback_query(F.data.startswith("member:unban:"))
async def cb_member_unban(cb: CallbackQuery, bot: Bot, session: AsyncSession) -> None:
    await _answer(cb, "جارٍ رفع الحظر…")
    _, _, group_id_str, user_id_str = cb.data.split(":")
    group_id, user_id = int(group_id_str), int(user_id_str)
    success = await mod.unban_user(bot, session, chat_id=group_id, user_id=user_id,
                                    actor_id=cb.from_user.id)
    await _edit(cb,
                S.member_unbanned if success else S.member_unban_fail,
                reply_markup=back_kb(f"grp:members:{group_id}"))


@router.callback_query(F.data.startswith("member:mute:"))
async def cb_member_mute(cb: CallbackQuery, bot: Bot, session: AsyncSession) -> None:
    await _answer(cb, "جارٍ الكتم…")
    parts = cb.data.split(":")
    group_id, user_id, duration = int(parts[2]), int(parts[3]), int(parts[4])
    success = await mod.mute_user(bot, session, chat_id=group_id, user_id=user_id,
                                   duration_seconds=duration, actor_id=cb.from_user.id)
    await _edit(cb,
                S.member_muted if success else S.member_mute_fail,
                reply_markup=back_kb(f"grp:members:{group_id}"))


@router.callback_query(F.data.startswith("member:unmute:"))
async def cb_member_unmute(cb: CallbackQuery, bot: Bot, session: AsyncSession) -> None:
    await _answer(cb, "جارٍ رفع الكتم…")
    _, _, group_id_str, user_id_str = cb.data.split(":")
    group_id, user_id = int(group_id_str), int(user_id_str)
    success = await mod.unmute_user(bot, session, chat_id=group_id, user_id=user_id,
                                     actor_id=cb.from_user.id)
    await _edit(cb,
                S.member_unmuted if success else S.member_unmute_fail,
                reply_markup=back_kb(f"grp:members:{group_id}"))


@router.callback_query(F.data.startswith("member:warn:"))
async def cb_member_warn(cb: CallbackQuery, bot: Bot, session: AsyncSession) -> None:
    await _answer(cb, "جارٍ التحذير…")
    _, _, group_id_str, user_id_str = cb.data.split(":")
    group_id, user_id = int(group_id_str), int(user_id_str)
    count, limit, punished = await warn_user(
        bot, session, chat_id=group_id, user_id=user_id, actor_id=cb.from_user.id,
    )
    msg = (S.member_warned_punished if punished else S.member_warned).format(
        count=count, limit=limit
    )
    await _edit(cb, msg, reply_markup=back_kb(f"grp:members:{group_id}"))


@router.callback_query(F.data.startswith("member:resetwarns:"))
async def cb_member_resetwarns(cb: CallbackQuery, session: AsyncSession) -> None:
    await _answer(cb)
    _, _, group_id_str, user_id_str = cb.data.split(":")
    group_id, user_id = int(group_id_str), int(user_id_str)
    await repo.reset_warnings(session, group_id, user_id)
    await _edit(cb, S.member_warns_reset, reply_markup=back_kb(f"grp:members:{group_id}"))


@router.callback_query(F.data.startswith("member:warnhist:"))
async def cb_member_warnhist(cb: CallbackQuery, session: AsyncSession) -> None:
    """Show the warning history for a member."""
    await _answer(cb)
    _, _, group_id_str, user_id_str = cb.data.split(":")
    group_id, user_id = int(group_id_str), int(user_id_str)

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
        ts = format_datetime_ar(entry.created_at)
        reason = escape_html(entry.reason or "—")
        actor = f"<code>{entry.actor_id}</code>" if entry.actor_id else "البوت"
        lines.append(
            S.warn_history_entry.format(date=ts, reason=reason, actor=actor)
        )

    await _edit(cb, "".join(lines), reply_markup=back_kb(f"grp:members:{group_id}"))


# ---------------------------------------------------------------------------
# Channel namespace
# ---------------------------------------------------------------------------

@router.callback_query(F.data.startswith("ch:select:"))
async def cb_ch_select(cb: CallbackQuery, session: AsyncSession) -> None:
    await _answer(cb)
    channel_id = int(cb.data.split(":")[2])
    channel = await repo.get_channel(session, channel_id)
    if not channel:
        await _edit(cb, S.not_found, reply_markup=back_kb("menu:channels"))
        return
    await _edit(
        cb,
        f"📢 <b>{escape_html(channel.title)}</b>",
        reply_markup=channel_panel_kb(channel_id),
    )


@router.callback_query(F.data.startswith("ch:pin:"))
async def cb_ch_pin(cb: CallbackQuery, bot: Bot, session: AsyncSession) -> None:
    await _answer(cb, "استخدم /pin داخل القناة لتثبيت آخر منشور.")
