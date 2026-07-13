"""
All CallbackQuery handlers — the inline keyboard brain of the bot.

Every button in the dashboard is handled here.
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

Future: FSM-based text input (welcome message editor), paginated logs.
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
)
from bot.services import moderation_service as mod
from bot.services.stats_service import build_stats_text, refresh_member_count
from bot.services.warning_service import warn_user
from database import repository as repo
from utils.helpers import escape_html, mention_html
from utils.logger import get_logger

log = get_logger(__name__)
router = Router(name="callbacks")


# ---------------------------------------------------------------------------
# FSM states (welcome message editing)
# ---------------------------------------------------------------------------

class SettingsState(StatesGroup):
    waiting_for_welcome_text = State()
    waiting_for_warn_limit = State()


# ---------------------------------------------------------------------------
# Helper: safe answer + edit
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
    user_id = cb.from_user.id
    groups = await repo.get_groups_for_user(session, user_id)
    await _edit(
        cb,
        f"🏠 <b>Dashboard</b>\n\nWelcome back, <b>{escape_html(cb.from_user.first_name)}</b>!",
        reply_markup=main_menu_kb(groups),
    )


@router.callback_query(F.data == "menu:groups")
async def cb_groups(cb: CallbackQuery, session: AsyncSession) -> None:
    await _answer(cb)
    groups = await repo.get_groups_for_user(session, cb.from_user.id)
    if not groups:
        await _edit(cb, "📋 You don't manage any groups yet.\n\nAdd me to a group and make me admin.",
                    reply_markup=back_kb("menu:home"))
        return
    await _edit(cb, "📋 <b>Your Groups</b>\n\nSelect a group to manage:",
                reply_markup=group_list_kb(groups))


@router.callback_query(F.data == "menu:channels")
async def cb_channels(cb: CallbackQuery, session: AsyncSession) -> None:
    await _answer(cb)
    channels = await repo.get_all_channels(session)
    if not channels:
        await _edit(cb, "📢 No channels connected yet.\n\nAdd me to a channel as admin.",
                    reply_markup=back_kb("menu:home"))
        return
    await _edit(cb, "📢 <b>Your Channels</b>", reply_markup=channels_menu_kb(channels))


@router.callback_query(F.data == "menu:stats_global")
async def cb_stats_global(cb: CallbackQuery, session: AsyncSession) -> None:
    await _answer(cb)
    groups = await repo.get_groups_for_user(session, cb.from_user.id)
    if not groups:
        await _edit(cb, "No groups to show stats for.", reply_markup=back_kb("menu:home"))
        return
    # Show stats for first group as overview
    g = groups[0]
    rows = await repo.get_stats(session, g.group_id, days=7)
    text = build_stats_text(rows, g.title)
    await _edit(cb, text, reply_markup=back_kb("menu:home"))


@router.callback_query(F.data == "menu:help")
async def cb_help(cb: CallbackQuery) -> None:
    await _answer(cb)
    text = (
        "❓ <b>Help</b>\n\n"
        "<b>Getting Started</b>\n"
        "1. Add the bot to your group\n"
        "2. Make it an Administrator\n"
        "3. Use /start in private chat\n\n"
        "<b>Admin Commands (in group)</b>\n"
        "/ban — Ban a user (reply or @username)\n"
        "/unban — Unban a user\n"
        "/mute [duration] — Mute (e.g. 2h, 30m)\n"
        "/unmute — Unmute a user\n"
        "/warn — Warn a user\n"
        "/resetwarns — Reset warnings\n"
        "/del — Delete a message\n"
        "/pin — Pin a message\n"
        "/unpin — Unpin a message\n"
        "/info — Show user info\n\n"
        "<b>Dashboard</b>\n"
        "Use /start in private chat to open the control panel."
    )
    await _edit(cb, text, reply_markup=back_kb("menu:home"))


# ---------------------------------------------------------------------------
# grp namespace
# ---------------------------------------------------------------------------

@router.callback_query(F.data.startswith("grp:select:"))
async def cb_grp_select(cb: CallbackQuery, session: AsyncSession) -> None:
    await _answer(cb)
    group_id = int(cb.data.split(":")[2])
    group = await repo.get_group(session, group_id)
    if not group:
        await _edit(cb, "❌ Group not found.", reply_markup=back_kb("menu:groups"))
        return
    await _edit(
        cb,
        f"🏠 <b>{escape_html(group.title)}</b>\n\nSelect an option:",
        reply_markup=group_panel_kb(group_id),
    )


@router.callback_query(F.data.startswith("grp:panel:"))
async def cb_grp_panel(cb: CallbackQuery, session: AsyncSession) -> None:
    await _answer(cb)
    group_id = int(cb.data.split(":")[2])
    group = await repo.get_group(session, group_id)
    if not group:
        await _edit(cb, "❌ Group not found.", reply_markup=back_kb("menu:groups"))
        return
    await _edit(
        cb,
        f"🏠 <b>{escape_html(group.title)}</b>\n\nSelect an option:",
        reply_markup=group_panel_kb(group_id),
    )


@router.callback_query(F.data.startswith("grp:mod:"))
async def cb_grp_mod(cb: CallbackQuery, session: AsyncSession) -> None:
    await _answer(cb)
    group_id = int(cb.data.split(":")[2])
    group = await repo.get_group(session, group_id)
    filters = await repo.get_filters(session, group_id)
    await _edit(
        cb,
        f"🛡 <b>Moderation — {escape_html(group.title if group else str(group_id))}</b>",
        reply_markup=moderation_menu_kb(group_id, filters),
    )


@router.callback_query(F.data.startswith("grp:settings:"))
async def cb_grp_settings(cb: CallbackQuery, session: AsyncSession) -> None:
    await _answer(cb)
    group_id = int(cb.data.split(":")[2])
    group = await repo.get_group(session, group_id)
    settings = await repo.get_settings(session, group_id)
    if not settings:
        await _edit(cb, "❌ Settings not found.", reply_markup=back_kb(f"grp:panel:{group_id}"))
        return
    await _edit(
        cb,
        f"⚙ <b>Settings — {escape_html(group.title if group else str(group_id))}</b>",
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
    logs = await repo.get_recent_logs(session, group_id, limit=10)
    if not logs:
        await _edit(cb, "📋 No logs yet.", reply_markup=back_kb(f"grp:panel:{group_id}"))
        return
    lines = ["📋 <b>Recent Events</b>\n"]
    for entry in logs:
        lines.append(f"• <b>{entry.event_type}</b> — {entry.created_at.strftime('%m/%d %H:%M')}"
                     + (f"\n  {escape_html(entry.details[:60])}" if entry.details else ""))
    await _edit(cb, "\n".join(lines), reply_markup=back_kb(f"grp:panel:{group_id}"))


@router.callback_query(F.data.startswith("grp:members:"))
async def cb_grp_members(cb: CallbackQuery, session: AsyncSession) -> None:
    await _answer(cb)
    group_id = int(cb.data.split(":")[2])
    await _edit(
        cb,
        "👥 <b>Member Actions</b>\n\n"
        "Reply to a user's message with /ban, /mute, /warn, etc.\n"
        "Or use /info to look up a user.",
        reply_markup=back_kb(f"grp:panel:{group_id}"),
    )


@router.callback_query(F.data.startswith("grp:admins:"))
async def cb_grp_admins(cb: CallbackQuery, session: AsyncSession) -> None:
    await _answer(cb)
    group_id = int(cb.data.split(":")[2])
    admins = await repo.get_admins(session, group_id)
    if not admins:
        await _edit(
            cb,
            "👮 No extra admins registered in the bot.\n"
            "Telegram administrators can already use all commands.",
            reply_markup=back_kb(f"grp:panel:{group_id}"),
        )
        return
    admin_ids = [a.user_id for a in admins]
    await _edit(cb, "👮 <b>Bot Admins</b>", reply_markup=admins_list_kb(group_id, admin_ids))


# ---------------------------------------------------------------------------
# mod namespace
# ---------------------------------------------------------------------------

@router.callback_query(F.data.startswith("mod:filters:"))
async def cb_mod_filters(cb: CallbackQuery, session: AsyncSession) -> None:
    await _answer(cb)
    group_id = int(cb.data.split(":")[2])
    filters = await repo.get_filters(session, group_id)
    await _edit(
        cb,
        "🔍 <b>Moderation Filters</b>\n\nToggle each filter on/off:",
        reply_markup=filters_list_kb(group_id, filters),
    )


@router.callback_query(F.data.startswith("mod:actions:"))
async def cb_mod_actions(cb: CallbackQuery, session: AsyncSession) -> None:
    await _answer(cb)
    group_id = int(cb.data.split(":")[2])
    filters = await repo.get_filters(session, group_id)
    await _edit(
        cb,
        "⚡ <b>Filter Actions</b>\n\nChoose a filter to configure its action:",
        reply_markup=filter_actions_menu_kb(group_id, filters),
    )


@router.callback_query(F.data.startswith("mod:warnlimit:"))
async def cb_mod_warnlimit(cb: CallbackQuery, session: AsyncSession, state: FSMContext) -> None:
    await _answer(cb)
    group_id = int(cb.data.split(":")[2])
    settings = await repo.get_settings(session, group_id)
    current = settings.warning_limit if settings else 3
    await state.update_data(group_id=group_id, context="warnlimit")
    await state.set_state(SettingsState.waiting_for_warn_limit)
    await _edit(
        cb,
        f"⚠️ Current warning limit: <b>{current}</b>\n\nSend a number (1–20):",
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
    await repo.update_filter(session, group_id, filter_type, enabled=not f.enabled)
    filters = await repo.get_filters(session, group_id)
    await _edit(
        cb,
        "🔍 <b>Moderation Filters</b>\n\nToggle each filter on/off:",
        reply_markup=filters_list_kb(group_id, filters),
    )
    await repo.add_log(
        session, group_id=group_id, event_type="settings_changed",
        actor_id=cb.from_user.id,
        details=f"filter {filter_type} → {'on' if not f.enabled else 'off'}",
    )


@router.callback_query(F.data.startswith("filter:actions:"))
async def cb_filter_actions(cb: CallbackQuery, session: AsyncSession) -> None:
    await _answer(cb)
    group_id = int(cb.data.split(":")[2])
    filters = await repo.get_filters(session, group_id)
    await _edit(
        cb,
        "⚡ <b>Filter Actions</b>\n\nChoose a filter:",
        reply_markup=filter_actions_menu_kb(group_id, filters),
    )


@router.callback_query(F.data.startswith("filter:editaction:"))
async def cb_filter_editaction(cb: CallbackQuery, session: AsyncSession) -> None:
    await _answer(cb)
    _, _, group_id_str, filter_type = cb.data.split(":", 3)
    group_id = int(group_id_str)
    f = await repo.get_filter(session, group_id, filter_type)
    if not f:
        return
    await _edit(
        cb,
        f"⚡ <b>Action for: {filter_type}</b>\n\nCurrent: <b>{f.action}</b>",
        reply_markup=filter_action_kb(group_id, filter_type, f.action),
    )


@router.callback_query(F.data.startswith("filter:setaction:"))
async def cb_filter_setaction(cb: CallbackQuery, session: AsyncSession) -> None:
    await _answer(cb)
    parts = cb.data.split(":")
    # format: filter:setaction:<group_id>:<filter_type>:<action>
    group_id = int(parts[2])
    filter_type = parts[3]
    action = parts[4]
    await repo.update_filter(session, group_id, filter_type, action=action)
    await repo.add_log(
        session, group_id=group_id, event_type="settings_changed",
        actor_id=cb.from_user.id,
        details=f"filter {filter_type} action → {action}",
    )
    f = await repo.get_filter(session, group_id, filter_type)
    await _edit(
        cb,
        f"✅ Action for <b>{filter_type}</b> set to <b>{action}</b>.",
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
    await _edit(
        cb,
        "⚙ <b>Settings</b>",
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
    await _edit(
        cb,
        "⚙ <b>Settings</b>",
        reply_markup=settings_menu_kb(group_id, updated.welcome_enabled, updated.log_events),
    )


@router.callback_query(F.data.startswith("settings:edit_welcome:"))
async def cb_edit_welcome(cb: CallbackQuery, session: AsyncSession, state: FSMContext) -> None:
    await _answer(cb)
    group_id = int(cb.data.split(":")[2])
    settings = await repo.get_settings(session, group_id)
    current = settings.welcome_text if settings else ""
    await state.update_data(group_id=group_id, context="welcome")
    await state.set_state(SettingsState.waiting_for_welcome_text)
    await _edit(
        cb,
        "✏️ <b>Edit Welcome Message</b>\n\n"
        f"Current:\n<i>{escape_html(current)}</i>\n\n"
        "Send the new welcome text.\n"
        "Placeholders: <code>{first_name}</code> <code>{username}</code> <code>{group_name}</code>",
        reply_markup=back_kb(f"grp:settings:{group_id}"),
    )


@router.callback_query(F.data.startswith("settings:punishment:"))
async def cb_punishment(cb: CallbackQuery, session: AsyncSession) -> None:
    await _answer(cb)
    group_id = int(cb.data.split(":")[2])
    settings = await repo.get_settings(session, group_id)
    current = settings.auto_punishment if settings else "mute"
    await _edit(
        cb,
        "🔨 <b>Auto-punishment</b>\n\nApplied when warning limit is reached:",
        reply_markup=punishment_kb(group_id, current),
    )


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
    await _edit(
        cb,
        f"✅ Auto-punishment set to <b>{punishment}</b>.",
        reply_markup=punishment_kb(group_id, punishment),
    )


@router.callback_query(F.data.startswith("settings:warnlimit:"))
async def cb_settings_warnlimit(cb: CallbackQuery, session: AsyncSession, state: FSMContext) -> None:
    await _answer(cb)
    group_id = int(cb.data.split(":")[2])
    settings = await repo.get_settings(session, group_id)
    current = settings.warning_limit if settings else 3
    await state.update_data(group_id=group_id, context="warnlimit")
    await state.set_state(SettingsState.waiting_for_warn_limit)
    await _edit(
        cb,
        f"⚠️ Current warning limit: <b>{current}</b>\n\nSend a number (1–20):",
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
        await message.reply("❌ Invalid input.")
        return
    await repo.update_settings(session, group_id, welcome_text=text)
    await message.reply(
        "✅ Welcome message updated!\n\n"
        f"Preview:\n<i>{escape_html(text)}</i>",
        parse_mode="HTML",
    )


@router.message(SettingsState.waiting_for_warn_limit)
async def fsm_warn_limit(message: Message, session: AsyncSession, state: FSMContext) -> None:
    data = await state.get_data()
    group_id = data.get("group_id")
    await state.clear()
    text = (message.text or "").strip()
    if not text.isdigit() or not (1 <= int(text) <= 20):
        await message.reply("❌ Please send a number between 1 and 20.")
        return
    limit = int(text)
    await repo.update_settings(session, group_id, warning_limit=limit)
    await message.reply(f"✅ Warning limit set to <b>{limit}</b>.", parse_mode="HTML")


# ---------------------------------------------------------------------------
# member namespace (inline member actions)
# ---------------------------------------------------------------------------

@router.callback_query(F.data.startswith("member:ban:"))
async def cb_member_ban(cb: CallbackQuery, bot: Bot, session: AsyncSession) -> None:
    await _answer(cb, "Banning…")
    _, _, group_id_str, user_id_str = cb.data.split(":")
    group_id, user_id = int(group_id_str), int(user_id_str)
    success = await mod.ban_user(
        bot, session, chat_id=group_id, user_id=user_id, actor_id=cb.from_user.id,
    )
    await _edit(
        cb,
        f"{'✅ User banned.' if success else '❌ Could not ban user.'}",
        reply_markup=back_kb(f"grp:members:{group_id}"),
    )


@router.callback_query(F.data.startswith("member:unban:"))
async def cb_member_unban(cb: CallbackQuery, bot: Bot, session: AsyncSession) -> None:
    await _answer(cb, "Unbanning…")
    _, _, group_id_str, user_id_str = cb.data.split(":")
    group_id, user_id = int(group_id_str), int(user_id_str)
    success = await mod.unban_user(
        bot, session, chat_id=group_id, user_id=user_id, actor_id=cb.from_user.id,
    )
    await _edit(
        cb,
        f"{'✅ User unbanned.' if success else '❌ Could not unban user.'}",
        reply_markup=back_kb(f"grp:members:{group_id}"),
    )


@router.callback_query(F.data.startswith("member:mute:"))
async def cb_member_mute(cb: CallbackQuery, bot: Bot, session: AsyncSession) -> None:
    await _answer(cb, "Muting…")
    parts = cb.data.split(":")
    group_id, user_id, duration = int(parts[2]), int(parts[3]), int(parts[4])
    success = await mod.mute_user(
        bot, session, chat_id=group_id, user_id=user_id,
        duration_seconds=duration, actor_id=cb.from_user.id,
    )
    await _edit(
        cb,
        f"{'✅ User muted for 1h.' if success else '❌ Could not mute user.'}",
        reply_markup=back_kb(f"grp:members:{group_id}"),
    )


@router.callback_query(F.data.startswith("member:unmute:"))
async def cb_member_unmute(cb: CallbackQuery, bot: Bot, session: AsyncSession) -> None:
    await _answer(cb, "Unmuting…")
    _, _, group_id_str, user_id_str = cb.data.split(":")
    group_id, user_id = int(group_id_str), int(user_id_str)
    success = await mod.unmute_user(
        bot, session, chat_id=group_id, user_id=user_id, actor_id=cb.from_user.id,
    )
    await _edit(
        cb,
        f"{'✅ User unmuted.' if success else '❌ Could not unmute user.'}",
        reply_markup=back_kb(f"grp:members:{group_id}"),
    )


@router.callback_query(F.data.startswith("member:warn:"))
async def cb_member_warn(cb: CallbackQuery, bot: Bot, session: AsyncSession) -> None:
    await _answer(cb, "Warning…")
    _, _, group_id_str, user_id_str = cb.data.split(":")
    group_id, user_id = int(group_id_str), int(user_id_str)
    count, limit, punished = await warn_user(
        bot, session, chat_id=group_id, user_id=user_id, actor_id=cb.from_user.id,
    )
    msg = f"✅ Warning {count}/{limit} issued."
    if punished:
        msg += " Auto-punishment applied."
    await _edit(cb, msg, reply_markup=back_kb(f"grp:members:{group_id}"))


@router.callback_query(F.data.startswith("member:resetwarns:"))
async def cb_member_resetwarns(cb: CallbackQuery, session: AsyncSession) -> None:
    await _answer(cb)
    _, _, group_id_str, user_id_str = cb.data.split(":")
    group_id, user_id = int(group_id_str), int(user_id_str)
    await repo.reset_warnings(session, group_id, user_id)
    await _edit(cb, "✅ Warnings reset.", reply_markup=back_kb(f"grp:members:{group_id}"))


# ---------------------------------------------------------------------------
# Channel namespace
# ---------------------------------------------------------------------------

@router.callback_query(F.data.startswith("ch:select:"))
async def cb_ch_select(cb: CallbackQuery, session: AsyncSession) -> None:
    await _answer(cb)
    channel_id = int(cb.data.split(":")[2])
    channel = await repo.get_channel(session, channel_id)
    if not channel:
        await _edit(cb, "❌ Channel not found.", reply_markup=back_kb("menu:channels"))
        return
    await _edit(
        cb,
        f"📢 <b>{escape_html(channel.title)}</b>",
        reply_markup=channel_panel_kb(channel_id),
    )


@router.callback_query(F.data.startswith("ch:pin:"))
async def cb_ch_pin(cb: CallbackQuery, bot: Bot, session: AsyncSession) -> None:
    await _answer(cb, "Use /pin in the channel to pin the latest post.")
