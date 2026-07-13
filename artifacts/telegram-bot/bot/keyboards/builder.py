"""
Inline keyboard builders — Version 2 (Arabic UI).

All user-facing labels are pulled from bot.strings.ar.S.
Every screen in the bot has its builder here; handlers import only from this module.

Future: per-group language selection (pass lang param), dynamic plugin buttons,
        paginated keyboards for large group/user lists.
"""

from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.strings.ar import S
from database.models import Filter, Group


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _back_btn(cb: str) -> InlineKeyboardButton:
    return InlineKeyboardButton(text=S.btn_back, callback_data=cb)


# ---------------------------------------------------------------------------
# Main dashboard
# ---------------------------------------------------------------------------

def main_menu_kb(groups: list[Group]) -> InlineKeyboardMarkup:
    """Home screen shown in private chat after /start."""
    builder = InlineKeyboardBuilder()

    if groups:
        for g in groups[:5]:
            builder.button(
                text=f"🏠 {g.title[:35]}",
                callback_data=f"grp:select:{g.group_id}",
            )
        builder.adjust(1)

    builder.button(text="📋 " + "مجموعاتي", callback_data="menu:groups")
    builder.button(text=S.btn_channels,    callback_data="menu:channels")
    builder.button(text=S.btn_stats,       callback_data="menu:stats_global")
    builder.button(text=S.btn_help,        callback_data="menu:help")
    builder.adjust(2)
    return builder.as_markup()


# ---------------------------------------------------------------------------
# Group list
# ---------------------------------------------------------------------------

def group_list_kb(groups: list[Group]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for g in groups:
        builder.button(
            text=f"🏠 {g.title[:40]}",
            callback_data=f"grp:select:{g.group_id}",
        )
    builder.row(InlineKeyboardButton(text=S.btn_back, callback_data="menu:home"))
    builder.adjust(1)
    return builder.as_markup()


# ---------------------------------------------------------------------------
# Group control panel
# ---------------------------------------------------------------------------

def group_panel_kb(group_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=S.btn_mod,             callback_data=f"grp:mod:{group_id}")
    builder.button(text=S.btn_panel_members,   callback_data=f"grp:members:{group_id}")
    builder.button(text=S.btn_panel_admins,    callback_data=f"grp:admins:{group_id}")
    builder.button(text=S.btn_panel_settings,  callback_data=f"grp:settings:{group_id}")
    builder.button(text=S.btn_stats,           callback_data=f"grp:stats:{group_id}")
    builder.button(text=S.btn_logs,            callback_data=f"grp:logs:{group_id}")
    builder.row(InlineKeyboardButton(text=S.btn_panel_back, callback_data="menu:groups"))
    builder.adjust(2, 2, 2, 1)
    return builder.as_markup()


# ---------------------------------------------------------------------------
# Moderation menu
# ---------------------------------------------------------------------------

def moderation_menu_kb(group_id: int, filters: list[Filter]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    active = sum(1 for f in filters if f.enabled)
    total = len(filters)
    builder.button(
        text=S.btn_filters.format(active=active, total=total),
        callback_data=f"mod:filters:{group_id}",
    )
    builder.button(text=S.btn_actions,    callback_data=f"mod:actions:{group_id}")
    builder.button(text=S.btn_warn_limit, callback_data=f"mod:warnlimit:{group_id}")
    builder.row(_back_btn(f"grp:panel:{group_id}"))
    builder.adjust(1)
    return builder.as_markup()


# ---------------------------------------------------------------------------
# Filter list
# ---------------------------------------------------------------------------

_FILTER_LABELS: dict[str, str] = {
    "bad_words":          S.filter_bad_words,
    "insults":            S.filter_insults,
    "spam":               S.filter_spam,
    "flood":              S.filter_flood,
    "duplicate_messages": S.filter_duplicates,
    "advertisement":      S.filter_advertisement,
    "telegram_links":     S.filter_telegram_links,
    "external_links":     S.filter_external_links,
    "excessive_emojis":   S.filter_excessive_emojis,
    "repeated_chars":     S.filter_repeated_chars,
    "long_messages":      S.filter_long_messages,
}

_ACTION_LABELS: dict[str, str] = {
    "ignore": S.action_ignore,
    "delete": S.action_delete,
    "warn":   S.action_warn,
    "mute":   S.action_mute,
    "kick":   S.action_kick,
    "ban":    S.action_ban,
}


def filters_list_kb(group_id: int, filters: list[Filter]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for f in filters:
        label = _FILTER_LABELS.get(f.filter_type, f.filter_type)
        status = "✅" if f.enabled else "❌"
        builder.button(
            text=f"{status} {label}",
            callback_data=f"filter:toggle:{group_id}:{f.filter_type}",
        )
    builder.button(text="⚙️ ضبط الإجراءات", callback_data=f"filter:actions:{group_id}")
    builder.row(_back_btn(f"grp:mod:{group_id}"))
    builder.adjust(1)
    return builder.as_markup()


def filter_action_kb(group_id: int, filter_type: str, current_action: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for action, label in _ACTION_LABELS.items():
        tick = "✓ " if action == current_action else ""
        builder.button(
            text=f"{tick}{label}",
            callback_data=f"filter:setaction:{group_id}:{filter_type}:{action}",
        )
    builder.row(_back_btn(f"filter:actions:{group_id}"))
    builder.adjust(2, 2, 2, 1)
    return builder.as_markup()


def filter_actions_menu_kb(group_id: int, filters: list[Filter]) -> InlineKeyboardMarkup:
    """List all filters so admin can pick which to configure."""
    builder = InlineKeyboardBuilder()
    for f in filters:
        label = _FILTER_LABELS.get(f.filter_type, f.filter_type)
        action_label = _ACTION_LABELS.get(f.action, f.action)
        builder.button(
            text=f"{label} ← {action_label}",
            callback_data=f"filter:editaction:{group_id}:{f.filter_type}",
        )
    builder.row(_back_btn(f"mod:filters:{group_id}"))
    builder.adjust(1)
    return builder.as_markup()


# ---------------------------------------------------------------------------
# Settings menu
# ---------------------------------------------------------------------------

def settings_menu_kb(group_id: int, welcome_enabled: bool, log_events: bool) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    w_status = S.enabled if welcome_enabled else S.disabled
    l_status = S.enabled if log_events else S.disabled

    builder.button(
        text=S.btn_welcome_toggle.format(status=w_status),
        callback_data=f"settings:toggle_welcome:{group_id}",
    )
    builder.button(text=S.btn_welcome_edit, callback_data=f"settings:edit_welcome:{group_id}")
    builder.button(
        text=S.btn_logs_toggle.format(status=l_status),
        callback_data=f"settings:toggle_logs:{group_id}",
    )
    builder.button(text=S.btn_warn_limit_setting, callback_data=f"settings:warnlimit:{group_id}")
    builder.button(text=S.btn_punishment,          callback_data=f"settings:punishment:{group_id}")
    builder.row(_back_btn(f"grp:panel:{group_id}"))
    builder.adjust(1)
    return builder.as_markup()


def punishment_kb(group_id: int, current: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    options = [
        ("mute", S.punishment_mute),
        ("kick", S.punishment_kick),
        ("ban",  S.punishment_ban),
    ]
    for p, label in options:
        tick = "✓ " if p == current else ""
        builder.button(
            text=f"{tick}{label}",
            callback_data=f"settings:setpunishment:{group_id}:{p}",
        )
    builder.row(_back_btn(f"grp:settings:{group_id}"))
    builder.adjust(3, 1)
    return builder.as_markup()


# ---------------------------------------------------------------------------
# Member management
# ---------------------------------------------------------------------------

def member_action_kb(group_id: int, user_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=S.btn_member_ban,         callback_data=f"member:ban:{group_id}:{user_id}")
    builder.button(text=S.btn_member_unban,       callback_data=f"member:unban:{group_id}:{user_id}")
    builder.button(text=S.btn_member_mute,        callback_data=f"member:mute:{group_id}:{user_id}:3600")
    builder.button(text=S.btn_member_unmute,      callback_data=f"member:unmute:{group_id}:{user_id}")
    builder.button(text=S.btn_member_warn,        callback_data=f"member:warn:{group_id}:{user_id}")
    builder.button(text=S.btn_member_reset_warns, callback_data=f"member:resetwarns:{group_id}:{user_id}")
    builder.button(text=S.btn_member_history,     callback_data=f"member:warnhist:{group_id}:{user_id}")
    builder.row(_back_btn(f"grp:members:{group_id}"))
    builder.adjust(2, 2, 2, 1, 1)
    return builder.as_markup()


# ---------------------------------------------------------------------------
# Admin management
# ---------------------------------------------------------------------------

def admins_list_kb(group_id: int, admin_ids: list[int]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for uid in admin_ids:
        builder.button(
            text=f"👤 {uid}",
            callback_data=f"admin:view:{group_id}:{uid}",
        )
    builder.row(_back_btn(f"grp:panel:{group_id}"))
    builder.adjust(2)
    return builder.as_markup()


# ---------------------------------------------------------------------------
# Channels menu
# ---------------------------------------------------------------------------

def channels_menu_kb(channels) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for ch in channels:
        builder.button(
            text=f"📢 {ch.title[:40]}",
            callback_data=f"ch:select:{ch.channel_id}",
        )
    builder.row(_back_btn("menu:home"))
    builder.adjust(1)
    return builder.as_markup()


def channel_panel_kb(channel_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=S.btn_ch_post, callback_data=f"ch:post:{channel_id}")
    builder.button(text=S.btn_ch_pin,  callback_data=f"ch:pin:{channel_id}")
    builder.row(InlineKeyboardButton(text=S.btn_ch_back, callback_data="menu:channels"))
    builder.adjust(2, 1)
    return builder.as_markup()


# ---------------------------------------------------------------------------
# Generic navigation
# ---------------------------------------------------------------------------

def back_kb(callback_data: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=S.btn_back, callback_data=callback_data)
    return builder.as_markup()


def confirm_kb(yes_data: str, no_data: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=S.confirm, callback_data=yes_data)
    builder.button(text=S.cancel,  callback_data=no_data)
    builder.adjust(2)
    return builder.as_markup()
