"""
Inline keyboard builders — Version 4 (Advanced Settings & Administration).

All user-facing labels are pulled from bot.strings.ar.S.
Every screen has a ⬅️ رجوع button.
Confirmations are required for destructive actions.
"""

from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.strings.ar import S
from database.models import Filter, Group, GroupSettings


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _back_btn(cb: str, label: str = S.btn_back) -> InlineKeyboardButton:
    return InlineKeyboardButton(text=label, callback_data=cb)


def _status(enabled: bool) -> str:
    return S.on if enabled else S.off


# ---------------------------------------------------------------------------
# Group activation (V3) — URL button for deep linking
# ---------------------------------------------------------------------------

def manage_group_url_kb(group_id: int, bot_username: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text=S.btn_manage_group,
        url=f"https://t.me/{bot_username}?start=grp_{group_id}",
    )
    return builder.as_markup()


# ---------------------------------------------------------------------------
# Main dashboard (private chat)
# ---------------------------------------------------------------------------

def main_menu_kb(
    groups: list[Group],
    active_group_id: int | None = None,
    is_bot_owner: bool = False,
) -> InlineKeyboardMarkup:
    """V5 main dashboard — full menu with updates channel & donations."""
    builder = InlineKeyboardBuilder()
    rows: list[int] = []

    if groups:
        if len(groups) > 1:
            builder.button(text=f"📋 مجموعاتي ({len(groups)})", callback_data="menu:groups")
            rows.append(1)
        gid = active_group_id or groups[0].group_id
        builder.button(text=S.btn_home,        callback_data="menu:home")
        builder.button(text=S.btn_protection,  callback_data=f"prot:menu:{gid}")
        builder.button(text=S.btn_members,     callback_data=f"grp:members:{gid}")
        builder.button(text=S.btn_admins,      callback_data=f"grp:admins:{gid}")
        builder.button(text=S.btn_channels,    callback_data="menu:channels")
        builder.button(text=S.btn_settings,    callback_data=f"grp:settings:{gid}")
        rows.append(2)
        rows.append(2)
        rows.append(2)
    else:
        builder.button(text=S.btn_home, callback_data="menu:home")
        rows.append(1)

    builder.button(text=S.btn_updates_channel, url=S.updates_channel_url)
    builder.button(text=S.btn_donate,          callback_data="donate:menu")
    rows.append(2)

    if is_bot_owner:
        # V7.1: global Gemini key manager — bot-owner only, never shown to
        # group owners/admins (they only control per-group AI toggles).
        builder.button(text=S.btn_ai_key_manager, callback_data="aisetup:open")
        rows.append(1)

    builder.button(text=S.btn_help, callback_data="menu:help")
    rows.append(1)

    builder.adjust(*rows)
    return builder.as_markup()


# ---------------------------------------------------------------------------
# V7.1 — Gemini API key setup wizard (bot-owner only)
# ---------------------------------------------------------------------------

def ai_setup_wizard_kb() -> InlineKeyboardMarkup:
    """No keys registered yet — first-time setup wizard."""
    builder = InlineKeyboardBuilder()
    builder.button(text=S.btn_ai_add_key, callback_data="aisetup:add")
    builder.row(InlineKeyboardButton(text=S.btn_back, callback_data="menu:home"))
    return builder.as_markup()


def ai_key_manager_kb(keys: list) -> InlineKeyboardMarkup:
    """Keys already exist — management screen with per-key delete buttons."""
    builder = InlineKeyboardBuilder()
    builder.button(text=S.btn_ai_add_key,    callback_data="aisetup:add")
    builder.button(text=S.btn_ai_del_key,    callback_data="aisetup:delmenu")
    builder.button(text=S.btn_ai_count_only, callback_data="aisetup:count")
    builder.row(InlineKeyboardButton(text=S.btn_back, callback_data="menu:home"))
    builder.adjust(2, 1, 1)
    return builder.as_markup()


def ai_key_delete_menu_kb(keys: list) -> InlineKeyboardMarkup:
    """List of keys as buttons — pressing one deletes that key (after confirmation)."""
    builder = InlineKeyboardBuilder()
    for k in keys:
        label = f"❌ #{k.id} — {k.masked_key()}"
        if k.label:
            label += f" ({k.label})"
        builder.button(text=label, callback_data=f"aisetup:delconfirm:{k.id}")
    builder.row(InlineKeyboardButton(text=S.btn_back, callback_data="aisetup:open"))
    builder.adjust(1)
    return builder.as_markup()


def ai_key_delete_confirm_kb(key_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=S.btn_confirm_delete, callback_data=f"aisetup:del:{key_id}")
    builder.button(text=S.btn_back,            callback_data="aisetup:delmenu")
    builder.adjust(1)
    return builder.as_markup()


def ai_setup_cancel_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=S.btn_cancel, callback_data="aisetup:open")
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
    builder.button(text=S.btn_mod,             callback_data=f"prot:menu:{group_id}")
    builder.button(text=S.btn_panel_members,   callback_data=f"grp:members:{group_id}")
    builder.button(text=S.btn_panel_admins,    callback_data=f"grp:admins:{group_id}")
    builder.button(text=S.btn_panel_settings,  callback_data=f"grp:settings:{group_id}")
    builder.row(InlineKeyboardButton(text=S.btn_panel_back, callback_data="menu:groups"))
    builder.adjust(2, 2, 1)
    return builder.as_markup()


# ---------------------------------------------------------------------------
# V3 Protection menu  (quick 5-filter view — kept for backwards compat)
# ---------------------------------------------------------------------------

_PROT_FILTERS = [
    ("telegram_links",     S.filter_telegram_links),
    ("duplicate_messages", S.filter_duplicates),
    ("advertisement",      S.filter_advertisement),
    ("flood",              S.filter_flood),
    ("bad_words",          S.filter_bad_words),
]


def protection_menu_kb(
    group_id: int,
    filters: list[Filter],
    auto_protect: bool,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    fmap = {f.filter_type: f for f in filters}

    for ft, label in _PROT_FILTERS:
        f = fmap.get(ft)
        st = _status(f.enabled if f else False)
        builder.button(
            text=f"{st} {label}",
            callback_data=f"prot:toggle:{group_id}:{ft}",
        )

    ap_label = S.btn_auto_protect_on if auto_protect else S.btn_auto_protect_off
    builder.button(text=ap_label, callback_data=f"prot:auto:{group_id}")
    builder.button(text="🔍 فلاتر متقدمة", callback_data=f"grp:mod:{group_id}")

    builder.row(_back_btn(f"grp:panel:{group_id}"))
    builder.adjust(1)
    return builder.as_markup()


# ---------------------------------------------------------------------------
# Moderation menu (advanced — kept for backwards compat)
# ---------------------------------------------------------------------------

def moderation_menu_kb(group_id: int, filters: list[Filter]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    active = sum(1 for f in filters if f.enabled)
    total  = len(filters)
    builder.button(
        text=S.btn_filters.format(active=active, total=total),
        callback_data=f"mod:filters:{group_id}",
    )
    builder.button(text=S.btn_actions,    callback_data=f"mod:actions:{group_id}")
    builder.button(text=S.btn_warn_limit, callback_data=f"mod:warnlimit:{group_id}")
    builder.row(_back_btn(f"prot:menu:{group_id}"))
    builder.adjust(1)
    return builder.as_markup()


# ---------------------------------------------------------------------------
# Filter list (full — advanced)
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
    # V4
    "forwarded":          S.filter_forwarded,
    "mass_mention":       S.filter_mass_mention,
    "hashtag":            S.filter_hashtag,
    # V6 — AI Protection
    "ai_text":            S.filter_ai_text,
    "ai_image":           S.filter_ai_image,
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
        label  = _FILTER_LABELS.get(f.filter_type, f.filter_type)
        status = _status(f.enabled)
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
    builder = InlineKeyboardBuilder()
    for f in filters:
        label        = _FILTER_LABELS.get(f.filter_type, f.filter_type)
        action_label = _ACTION_LABELS.get(f.action, f.action)
        builder.button(
            text=f"{label} ← {action_label}",
            callback_data=f"filter:editaction:{group_id}:{f.filter_type}",
        )
    builder.row(_back_btn(f"mod:filters:{group_id}"))
    builder.adjust(1)
    return builder.as_markup()


# ---------------------------------------------------------------------------
# Settings menu (legacy — redirects to V4 settings center)
# ---------------------------------------------------------------------------

def settings_menu_kb(group_id: int, welcome_enabled: bool, log_events: bool) -> InlineKeyboardMarkup:
    """Legacy settings keyboard — kept for backwards compat with old callbacks."""
    builder = InlineKeyboardBuilder()
    w_status = f"{_status(welcome_enabled)} {S.enabled if welcome_enabled else S.disabled}"
    l_status = f"{_status(log_events)} {S.enabled if log_events else S.disabled}"

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
# Generic navigation & confirmations
# ---------------------------------------------------------------------------

def back_kb(callback_data: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=S.btn_back, callback_data=callback_data)
    return builder.as_markup()


def confirm_kb(yes_data: str, no_data: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=S.confirm_yes, callback_data=yes_data)
    builder.button(text=S.confirm_no,  callback_data=no_data)
    builder.adjust(2)
    return builder.as_markup()


# ===========================================================================
# V4 Keyboards
# ===========================================================================

# ---------------------------------------------------------------------------
# V4 Settings Center
# ---------------------------------------------------------------------------

def v4_settings_menu_kb(group_id: int) -> InlineKeyboardMarkup:
    """V4 main settings center with all sections."""
    builder = InlineKeyboardBuilder()
    builder.button(text=S.btn_v4_protection,  callback_data=f"v4s:protection:{group_id}")
    builder.button(text=S.btn_v4_punishments, callback_data=f"v4s:punishments:{group_id}")
    builder.button(text=S.btn_v4_permissions, callback_data=f"v4s:perms:{group_id}")
    builder.button(text=S.btn_v4_welcome,     callback_data=f"v4s:welcome:{group_id}")
    builder.button(text=S.btn_v4_goodbye,     callback_data=f"v4s:goodbye:{group_id}")
    builder.button(text=S.btn_v4_media,       callback_data=f"v4s:media:{group_id}")
    builder.button(text=S.btn_v4_channel,     callback_data=f"v4s:channel:{group_id}")
    builder.button(text=S.btn_v4_language,    callback_data=f"v4s:lang:{group_id}")
    builder.button(text=S.btn_v4_ai,          callback_data=f"v4s:ai:{group_id}")
    builder.button(text=S.btn_v4_reset,       callback_data=f"v4s:reset:{group_id}")
    builder.row(_back_btn(f"grp:panel:{group_id}"))
    builder.adjust(2, 2, 2, 2, 2, 1)
    return builder.as_markup()


# ---------------------------------------------------------------------------
# V4 Protection — all 14 filters
# ---------------------------------------------------------------------------

# All active filters shown on V4 protection page
_V4_ALL_FILTERS = [
    ("bad_words",          S.filter_bad_words),
    ("flood",              S.filter_flood),
    ("duplicate_messages", S.filter_duplicates),
    ("advertisement",      S.filter_advertisement),
    ("telegram_links",     S.filter_telegram_links),
    ("external_links",     S.filter_external_links),
    ("excessive_emojis",   S.filter_excessive_emojis),
    ("repeated_chars",     S.filter_repeated_chars),
    ("long_messages",      S.filter_long_messages),
    ("forwarded",          S.filter_forwarded),
    ("mass_mention",       S.filter_mass_mention),
    ("hashtag",            S.filter_hashtag),
    ("bad_words",          S.filter_bad_words),
    # V6 — AI Protection (moderation action reuses the standard punishment picker)
    ("ai_text",            S.filter_ai_text),
    ("ai_image",           S.filter_ai_image),
]


def v4_protection_kb(group_id: int, filters: list[Filter]) -> InlineKeyboardMarkup:
    """V4 protection page — all filters with 🟢/🔴."""
    builder = InlineKeyboardBuilder()
    fmap = {f.filter_type: f for f in filters}

    for ft, label in _V4_ALL_FILTERS:
        f = fmap.get(ft)
        st = _status(f.enabled if f else False)
        builder.button(
            text=f"{st} {label}",
            callback_data=f"v4s:prot_toggle:{group_id}:{ft}",
        )

    builder.row(_back_btn(f"v4s:menu:{group_id}"))
    builder.adjust(1)
    return builder.as_markup()


# ---------------------------------------------------------------------------
# V4 Punishments — per-filter action picker
# ---------------------------------------------------------------------------

def v4_punishments_kb(group_id: int, filters: list[Filter]) -> InlineKeyboardMarkup:
    """List all filters showing current punishment action."""
    builder = InlineKeyboardBuilder()
    fmap = {f.filter_type: f for f in filters}

    for ft, label in _V4_ALL_FILTERS:
        f = fmap.get(ft)
        action_label = _ACTION_LABELS.get(f.action, f.action) if f else S.action_delete
        builder.button(
            text=f"{label} ← {action_label}",
            callback_data=f"v4s:pf_pick:{group_id}:{ft}",
        )

    builder.row(_back_btn(f"v4s:menu:{group_id}"))
    builder.adjust(1)
    return builder.as_markup()


def v4_punishment_filter_kb(group_id: int, filter_type: str, current_action: str) -> InlineKeyboardMarkup:
    """Action picker for a single filter."""
    builder = InlineKeyboardBuilder()
    for action, label in _ACTION_LABELS.items():
        tick = "✓ " if action == current_action else ""
        builder.button(
            text=f"{tick}{label}",
            callback_data=f"v4s:pf_set:{group_id}:{filter_type}:{action}",
        )
    builder.row(_back_btn(f"v4s:punishments:{group_id}"))
    builder.adjust(2, 2, 2, 1)
    return builder.as_markup()


# ---------------------------------------------------------------------------
# V4 Admin Permissions
# ---------------------------------------------------------------------------

_V4_PERMS = [
    ("perm_delete",        S.perm_delete),
    ("perm_ban",           S.perm_ban),
    ("perm_unban",         S.perm_unban),
    ("perm_mute",          S.perm_mute),
    ("perm_unmute",        S.perm_unmute),
    ("perm_pin",           S.perm_pin),
    ("perm_unpin",         S.perm_unpin),
    ("perm_warn",          S.perm_warn),
    ("perm_edit_settings", S.perm_edit_settings),
    ("perm_manage_admins", S.perm_manage_admins),
]


def v4_permissions_kb(group_id: int, settings: GroupSettings) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for perm_key, label in _V4_PERMS:
        val = getattr(settings, perm_key, False)
        st = _status(val)
        builder.button(
            text=f"{st} {label}",
            callback_data=f"v4s:perm_toggle:{group_id}:{perm_key}",
        )
    builder.row(_back_btn(f"v4s:menu:{group_id}"))
    builder.adjust(1)
    return builder.as_markup()


# ---------------------------------------------------------------------------
# V4 Welcome / Goodbye
# ---------------------------------------------------------------------------

def v4_welcome_kb(group_id: int, enabled: bool) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    st = _status(enabled)
    builder.button(
        text=S.btn_v4_welcome_toggle.format(status=st),
        callback_data=f"v4s:welcome_toggle:{group_id}",
    )
    builder.button(text=S.btn_v4_welcome_edit,    callback_data=f"v4s:welcome_edit:{group_id}")
    builder.button(text=S.btn_v4_welcome_preview, callback_data=f"v4s:welcome_preview:{group_id}")
    builder.row(_back_btn(f"v4s:menu:{group_id}"))
    builder.adjust(1)
    return builder.as_markup()


def v4_goodbye_kb(group_id: int, enabled: bool) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    st = _status(enabled)
    builder.button(
        text=S.btn_v4_goodbye_toggle.format(status=st),
        callback_data=f"v4s:goodbye_toggle:{group_id}",
    )
    builder.button(text=S.btn_v4_goodbye_edit,    callback_data=f"v4s:goodbye_edit:{group_id}")
    builder.button(text=S.btn_v4_goodbye_preview, callback_data=f"v4s:goodbye_preview:{group_id}")
    builder.row(_back_btn(f"v4s:menu:{group_id}"))
    builder.adjust(1)
    return builder.as_markup()


# ---------------------------------------------------------------------------
# V4 Media Settings
# ---------------------------------------------------------------------------

_V4_MEDIA_LOCKS = [
    ("lock_photos",    S.media_photos),
    ("lock_video",     S.media_video),
    ("lock_audio",     S.media_audio),
    ("lock_documents", S.media_documents),
    ("lock_stickers",  S.media_stickers),
    ("lock_gifs",      S.media_gifs),
    ("lock_polls",     S.media_polls),
    ("lock_locations", S.media_locations),
    ("lock_voice",     S.media_voice),
]


def v4_media_kb(group_id: int, settings: GroupSettings) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for lock_key, label in _V4_MEDIA_LOCKS:
        locked = getattr(settings, lock_key, False)
        # locked=True → 🔴 (blocked), locked=False → 🟢 (allowed)
        st = S.off if locked else S.on
        builder.button(
            text=f"{st} {label}",
            callback_data=f"v4s:media_toggle:{group_id}:{lock_key}",
        )
    builder.row(_back_btn(f"v4s:menu:{group_id}"))
    builder.adjust(1)
    return builder.as_markup()


# ---------------------------------------------------------------------------
# V4 Channel Settings
# ---------------------------------------------------------------------------

def v4_channel_list_kb(channels, group_id: int) -> InlineKeyboardMarkup:
    """Pick which channel to manage."""
    builder = InlineKeyboardBuilder()
    for ch in channels:
        builder.button(
            text=f"📢 {ch.title[:35]}",
            callback_data=f"v4s:ch_panel:{group_id}:{ch.channel_id}",
        )
    builder.row(_back_btn(f"v4s:menu:{group_id}"))
    builder.adjust(1)
    return builder.as_markup()


def v4_channel_panel_kb(group_id: int, channel_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=S.btn_v4_ch_info,   callback_data=f"v4s:ch_info:{group_id}:{channel_id}")
    builder.button(text=S.btn_v4_ch_verify, callback_data=f"v4s:ch_verify:{group_id}:{channel_id}")
    builder.button(text=S.btn_v4_ch_pin,    callback_data=f"v4s:ch_pin:{group_id}:{channel_id}")
    builder.button(text=S.btn_v4_ch_delete, callback_data=f"v4s:ch_delete:{group_id}:{channel_id}")
    builder.row(_back_btn(f"v4s:channel:{group_id}"))
    builder.adjust(2, 2, 1)
    return builder.as_markup()


# ---------------------------------------------------------------------------
# V4 Language
# ---------------------------------------------------------------------------

_LANGUAGES = [
    ("ar", S.lang_ar),
    ("en", S.lang_en),
]


def v4_language_kb(group_id: int, current_lang: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for code, label in _LANGUAGES:
        tick = "✓ " if code == current_lang else ""
        builder.button(
            text=f"{tick}{label}",
            callback_data=f"v4s:lang_set:{group_id}:{code}",
        )
    builder.row(_back_btn(f"v4s:menu:{group_id}"))
    builder.adjust(1)
    return builder.as_markup()


# ---------------------------------------------------------------------------
# V4 Reset
# ---------------------------------------------------------------------------

def v4_reset_confirm_kb(group_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ نعم، إعادة الضبط", callback_data=f"v4s:reset_confirm:{group_id}")
    builder.button(text="❌ إلغاء",             callback_data=f"v4s:menu:{group_id}")
    builder.adjust(2)
    return builder.as_markup()


# ---------------------------------------------------------------------------
# V6/V7 — AI Protection settings panel (Gemini)
# ---------------------------------------------------------------------------

def v4_ai_settings_kb(group_id: int, settings: GroupSettings) -> InlineKeyboardMarkup:
    """V7: 7-button AI panel — toggle, analyse (msgs/images/links), sensitivity, actions, status."""
    sensitivity_labels = {
        "low": S.ai_sensitivity_low,
        "medium": S.ai_sensitivity_medium,
        "high": S.ai_sensitivity_high,
    }
    builder = InlineKeyboardBuilder()
    builder.button(
        text=S.btn_ai_toggle.format(status=_status(settings.ai_enabled)),
        callback_data=f"v4s:ai_toggle:{group_id}",
    )
    builder.button(
        text=S.btn_ai_analyze_msgs.format(status=_status(settings.ai_analyze_messages)),
        callback_data=f"v4s:ai_toggle_msgs:{group_id}",
    )
    builder.button(
        text=S.btn_ai_analyze_images.format(status=_status(settings.ai_analyze_images)),
        callback_data=f"v4s:ai_toggle_images:{group_id}",
    )
    # V7 — link analysis toggle
    builder.button(
        text=S.btn_ai_analyze_links.format(
            status=_status(getattr(settings, "ai_analyze_links", False))
        ),
        callback_data=f"v4s:ai_toggle_links:{group_id}",
    )
    # V7.2 — username/display-name + group description screening
    builder.button(
        text=S.btn_ai_toggle_profiles.format(
            status=_status(getattr(settings, "ai_analyze_profiles", True))
        ),
        callback_data=f"v4s:ai_toggle_profiles:{group_id}",
    )
    builder.button(
        text=S.btn_ai_sensitivity.format(
            level=sensitivity_labels.get(settings.ai_sensitivity, settings.ai_sensitivity)
        ),
        callback_data=f"v4s:ai_sens:{group_id}",
    )
    # V7 — multi-action picker
    builder.button(text=S.btn_ai_actions, callback_data=f"v4s:ai_actions:{group_id}")
    builder.button(text=S.btn_ai_status,  callback_data=f"v4s:ai_status:{group_id}")
    builder.row(_back_btn(f"v4s:menu:{group_id}"))
    builder.adjust(1)
    return builder.as_markup()


def v4_ai_actions_kb(group_id: int, settings: GroupSettings) -> InlineKeyboardMarkup:
    """V7: Multi-action selection (checkmark = enabled, circle = disabled)."""
    def _tick(flag: bool) -> str:
        return "✓" if flag else "○"

    builder = InlineKeyboardBuilder()
    builder.button(
        text=S.btn_ai_action_delete.format(status=_tick(getattr(settings, "ai_action_delete", True))),
        callback_data=f"v4s:ai_action_toggle:{group_id}:delete",
    )
    builder.button(
        text=S.btn_ai_action_warn.format(status=_tick(getattr(settings, "ai_action_warn", False))),
        callback_data=f"v4s:ai_action_toggle:{group_id}:warn",
    )
    builder.button(
        text=S.btn_ai_action_mute.format(status=_tick(getattr(settings, "ai_action_mute", False))),
        callback_data=f"v4s:ai_action_toggle:{group_id}:mute",
    )
    builder.button(
        text=S.btn_ai_action_ban.format(status=_tick(getattr(settings, "ai_action_ban", False))),
        callback_data=f"v4s:ai_action_toggle:{group_id}:ban",
    )
    builder.row(_back_btn(f"v4s:ai:{group_id}"))
    builder.adjust(1)
    return builder.as_markup()


def v4_ai_sensitivity_kb(group_id: int, current: str) -> InlineKeyboardMarkup:
    levels = [
        ("low", S.ai_sensitivity_low),
        ("medium", S.ai_sensitivity_medium),
        ("high", S.ai_sensitivity_high),
    ]
    builder = InlineKeyboardBuilder()
    for level, label in levels:
        tick = "✓ " if level == current else ""
        builder.button(
            text=f"{tick}{label}",
            callback_data=f"v4s:ai_sens_set:{group_id}:{level}",
        )
    builder.row(_back_btn(f"v4s:ai:{group_id}"))
    builder.adjust(1)
    return builder.as_markup()


def v4_ai_status_kb(group_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=S.btn_ai_test, callback_data=f"v4s:ai_test:{group_id}")
    builder.row(_back_btn(f"v4s:ai:{group_id}"))
    return builder.as_markup()


# ===========================================================================
# V5 Keyboards — Telegram Stars Donations
# ===========================================================================

DONATION_AMOUNTS = [25, 50, 100, 250, 500, 1000]


def donate_amounts_kb() -> InlineKeyboardMarkup:
    """Preset Telegram Stars amounts + a cancel button."""
    builder = InlineKeyboardBuilder()
    for amount in DONATION_AMOUNTS:
        builder.button(
            text=S.btn_donate_amount.format(amount=amount),
            callback_data=f"donate:pay:{amount}",
        )
    builder.row(InlineKeyboardButton(text=S.btn_donate_cancel, callback_data="donate:cancel"))
    builder.adjust(3, 3, 1)
    return builder.as_markup()
