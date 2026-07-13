"""
Inline keyboard builders for every screen in the bot.
All keyboards are built here — handlers import from this module only.
Future: i18n support (pass language param), dynamic plugin buttons.
"""

from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database.models import Filter, Group


# ---------------------------------------------------------------------------
# Main dashboard
# ---------------------------------------------------------------------------

def main_menu_kb(groups: list[Group]) -> InlineKeyboardMarkup:
    """Dashboard shown in private chat after /start."""
    builder = InlineKeyboardBuilder()

    if groups:
        # Show first group as quick-access
        for g in groups[:3]:
            builder.button(
                text=f"🏠 {g.title[:30]}",
                callback_data=f"grp:select:{g.group_id}",
            )
        builder.adjust(1)

    builder.button(text="📋 My Groups", callback_data="menu:groups")
    builder.button(text="📢 My Channels", callback_data="menu:channels")
    builder.button(text="📊 Statistics", callback_data="menu:stats_global")
    builder.button(text="❓ Help", callback_data="menu:help")
    builder.adjust(2)
    return builder.as_markup()


# ---------------------------------------------------------------------------
# Group selection
# ---------------------------------------------------------------------------

def group_list_kb(groups: list[Group]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for g in groups:
        builder.button(
            text=f"🏠 {g.title[:40]}",
            callback_data=f"grp:select:{g.group_id}",
        )
    builder.button(text="🔙 Back", callback_data="menu:home")
    builder.adjust(1)
    return builder.as_markup()


# ---------------------------------------------------------------------------
# Group control panel
# ---------------------------------------------------------------------------

def group_panel_kb(group_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🛡 Moderation", callback_data=f"grp:mod:{group_id}")
    builder.button(text="👥 Members",    callback_data=f"grp:members:{group_id}")
    builder.button(text="👮 Admins",     callback_data=f"grp:admins:{group_id}")
    builder.button(text="⚙ Settings",   callback_data=f"grp:settings:{group_id}")
    builder.button(text="📊 Statistics", callback_data=f"grp:stats:{group_id}")
    builder.button(text="📋 Logs",       callback_data=f"grp:logs:{group_id}")
    builder.button(text="🔙 My Groups",  callback_data="menu:groups")
    builder.adjust(2, 2, 2, 1)
    return builder.as_markup()


# ---------------------------------------------------------------------------
# Moderation menu
# ---------------------------------------------------------------------------

def moderation_menu_kb(group_id: int, filters: list[Filter]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    enabled_count = sum(1 for f in filters if f.enabled)
    builder.button(
        text=f"🔍 Filters ({enabled_count}/{len(filters)} active)",
        callback_data=f"mod:filters:{group_id}",
    )
    builder.button(text="⚡ Actions",      callback_data=f"mod:actions:{group_id}")
    builder.button(text="⚠️ Warning Limit", callback_data=f"mod:warnlimit:{group_id}")
    builder.button(text="🔙 Back",          callback_data=f"grp:panel:{group_id}")
    builder.adjust(1)
    return builder.as_markup()


# ---------------------------------------------------------------------------
# Filter list
# ---------------------------------------------------------------------------

_FILTER_LABELS: dict[str, str] = {
    "bad_words":         "🤬 Bad Words",
    "insults":           "😡 Insults",
    "spam":              "📨 Spam",
    "flood":             "🌊 Flood",
    "duplicate_messages":"🔁 Duplicates",
    "advertisement":     "📣 Advertisement",
    "telegram_links":    "🔗 Telegram Links",
    "external_links":    "🌐 External Links",
    "excessive_emojis":  "😂 Excessive Emojis",
    "repeated_chars":    "🔤 Repeated Chars",
    "long_messages":     "📜 Long Messages",
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
    builder.button(text="⚙ Configure Actions", callback_data=f"filter:actions:{group_id}")
    builder.button(text="🔙 Back", callback_data=f"grp:mod:{group_id}")
    builder.adjust(1)
    return builder.as_markup()


# ---------------------------------------------------------------------------
# Filter action selection
# ---------------------------------------------------------------------------

_ACTION_LABELS: dict[str, str] = {
    "ignore": "👁 Ignore",
    "delete": "🗑 Delete",
    "warn":   "⚠️ Warn",
    "mute":   "🔇 Mute",
    "kick":   "👢 Kick",
    "ban":    "🚫 Ban",
}


def filter_action_kb(group_id: int, filter_type: str, current_action: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for action, label in _ACTION_LABELS.items():
        tick = "✓ " if action == current_action else ""
        builder.button(
            text=f"{tick}{label}",
            callback_data=f"filter:setaction:{group_id}:{filter_type}:{action}",
        )
    builder.button(text="🔙 Back", callback_data=f"filter:actions:{group_id}")
    builder.adjust(2, 2, 2, 1)
    return builder.as_markup()


def filter_actions_menu_kb(group_id: int, filters: list[Filter]) -> InlineKeyboardMarkup:
    """List all filters so admin can pick which one to configure action for."""
    builder = InlineKeyboardBuilder()
    for f in filters:
        label = _FILTER_LABELS.get(f.filter_type, f.filter_type)
        action_label = _ACTION_LABELS.get(f.action, f.action)
        builder.button(
            text=f"{label} → {action_label}",
            callback_data=f"filter:editaction:{group_id}:{f.filter_type}",
        )
    builder.button(text="🔙 Back", callback_data=f"mod:filters:{group_id}")
    builder.adjust(1)
    return builder.as_markup()


# ---------------------------------------------------------------------------
# Settings menu
# ---------------------------------------------------------------------------

def settings_menu_kb(group_id: int, welcome_enabled: bool, log_events: bool) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    w_status = "✅ Enabled" if welcome_enabled else "❌ Disabled"
    l_status = "✅ Enabled" if log_events else "❌ Disabled"
    builder.button(text=f"👋 Welcome: {w_status}", callback_data=f"settings:toggle_welcome:{group_id}")
    builder.button(text="✏️ Edit Welcome Text",    callback_data=f"settings:edit_welcome:{group_id}")
    builder.button(text=f"📋 Event Logs: {l_status}", callback_data=f"settings:toggle_logs:{group_id}")
    builder.button(text="⚠️ Warning Limit",           callback_data=f"settings:warnlimit:{group_id}")
    builder.button(text="🔨 Auto-punishment",          callback_data=f"settings:punishment:{group_id}")
    builder.button(text="🔙 Back",                    callback_data=f"grp:panel:{group_id}")
    builder.adjust(1)
    return builder.as_markup()


def punishment_kb(group_id: int, current: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for p in ["mute", "kick", "ban"]:
        tick = "✓ " if p == current else ""
        builder.button(
            text=f"{tick}{p.capitalize()}",
            callback_data=f"settings:setpunishment:{group_id}:{p}",
        )
    builder.button(text="🔙 Back", callback_data=f"grp:settings:{group_id}")
    builder.adjust(3, 1)
    return builder.as_markup()


# ---------------------------------------------------------------------------
# Member management
# ---------------------------------------------------------------------------

def member_action_kb(group_id: int, user_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🚫 Ban",           callback_data=f"member:ban:{group_id}:{user_id}")
    builder.button(text="✅ Unban",         callback_data=f"member:unban:{group_id}:{user_id}")
    builder.button(text="🔇 Mute 1h",       callback_data=f"member:mute:{group_id}:{user_id}:3600")
    builder.button(text="🔊 Unmute",        callback_data=f"member:unmute:{group_id}:{user_id}")
    builder.button(text="⚠️ Warn",          callback_data=f"member:warn:{group_id}:{user_id}")
    builder.button(text="🔄 Reset Warns",   callback_data=f"member:resetwarns:{group_id}:{user_id}")
    builder.button(text="🔙 Back",          callback_data=f"grp:members:{group_id}")
    builder.adjust(2, 2, 2, 1)
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
    builder.button(text="🔙 Back", callback_data=f"grp:panel:{group_id}")
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
    builder.button(text="🔙 Back", callback_data="menu:home")
    builder.adjust(1)
    return builder.as_markup()


def channel_panel_kb(channel_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="📝 Post Message", callback_data=f"ch:post:{channel_id}")
    builder.button(text="📌 Pin Last",     callback_data=f"ch:pin:{channel_id}")
    builder.button(text="🔙 My Channels",  callback_data="menu:channels")
    builder.adjust(1)
    return builder.as_markup()


# ---------------------------------------------------------------------------
# Generic navigation
# ---------------------------------------------------------------------------

def back_kb(callback_data: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🔙 Back", callback_data=callback_data)
    return builder.as_markup()


def confirm_kb(yes_data: str, no_data: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Confirm", callback_data=yes_data)
    builder.button(text="❌ Cancel",  callback_data=no_data)
    builder.adjust(2)
    return builder.as_markup()
