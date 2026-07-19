"""
V4 Settings handlers — Advanced Settings & Administration.

Namespace: v4s

Callback patterns
-----------------
v4s:menu:{gid}              — Settings Center (main page)
v4s:protection:{gid}        — All 14 protection filters with ON/OFF
v4s:prot_toggle:{gid}:{ft}  — Toggle a single filter
v4s:punishments:{gid}       — Per-filter punishment list
v4s:pf_pick:{gid}:{ft}      — Pick punishment for one filter
v4s:pf_set:{gid}:{ft}:{act} — Save punishment for one filter
v4s:perms:{gid}             — Admin permission toggles (owner only)
v4s:perm_toggle:{gid}:{key} — Toggle one permission
v4s:welcome:{gid}           — Welcome message page
v4s:welcome_toggle:{gid}    — Toggle welcome on/off
v4s:welcome_edit:{gid}      — Enter FSM to edit welcome text
v4s:welcome_preview:{gid}   — Preview welcome message
v4s:goodbye:{gid}           — Goodbye message page
v4s:goodbye_toggle:{gid}    — Toggle goodbye on/off
v4s:goodbye_edit:{gid}      — Enter FSM to edit goodbye text
v4s:goodbye_preview:{gid}   — Preview goodbye message
v4s:media:{gid}             — Media lock page
v4s:media_toggle:{gid}:{key}— Toggle a media lock
v4s:channel:{gid}           — Channel settings (pick channel)
v4s:ch_panel:{gid}:{chid}   — Channel action panel
v4s:ch_info:{gid}:{chid}    — Show channel info
v4s:ch_verify:{gid}:{chid}  — Verify bot permissions
v4s:ch_pin:{gid}:{chid}     — Pin latest post
v4s:ch_delete:{gid}:{chid}  — Delete latest post
v4s:lang:{gid}              — Language picker
v4s:lang_set:{gid}:{code}   — Save language choice
v4s:reset:{gid}             — Reset confirmation prompt
v4s:reset_confirm:{gid}     — Execute reset
"""

from __future__ import annotations

from aiogram import Bot, Router, F
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.ai.manager import ai_manager
from bot.filters.admin_filter import is_bot_owner_id
from bot.keyboards.builder import (
    _ACTION_LABELS,
    _FILTER_LABELS,
    _V4_ALL_FILTERS,
    _V4_MEDIA_LOCKS,
    _V4_PERMS,
    ai_setup_wizard_kb,
    back_kb,
    v4_ai_actions_kb,
    v4_ai_sensitivity_kb,
    v4_ai_settings_kb,
    v4_ai_status_kb,
    v4_channel_list_kb,
    v4_channel_panel_kb,
    v4_goodbye_kb,
    v4_language_kb,
    v4_media_kb,
    v4_permissions_kb,
    v4_protection_kb,
    v4_punishment_filter_kb,
    v4_punishments_kb,
    v4_reset_confirm_kb,
    v4_settings_menu_kb,
    v4_welcome_kb,
)
from bot.strings.ar import S
from database import repository as repo
from utils.ai_helpers import gemini_err_to_arabic as _gemini_err_to_arabic
from bot.security import ensure_authorized, ensure_owner
from utils.helpers import escape_html, format_welcome, mention_html
from utils.logger import get_logger

log = get_logger(__name__)
router = Router(name="v4_settings")


# ---------------------------------------------------------------------------
# FSM states
# ---------------------------------------------------------------------------

class V4State(StatesGroup):
    waiting_for_welcome_text = State()
    waiting_for_goodbye_text = State()


# ---------------------------------------------------------------------------
# Helpers
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


# _ensure_owner removed — use bot.security.ensure_owner (live Telegram API check).


def _lang_name(code: str) -> str:
    return {"ar": S.lang_ar, "en": S.lang_en}.get(code, code)


# ---------------------------------------------------------------------------
# ── V4 Settings Center ──────────────────────────────────────────────────────
# ---------------------------------------------------------------------------

@router.callback_query(F.data.startswith("v4s:menu:"))
async def cb_v4_menu(cb: CallbackQuery, bot: Bot, session: AsyncSession) -> None:
    await _answer(cb)
    group_id = int(cb.data.split(":")[2])
    if not await ensure_authorized(cb, bot, session, group_id):
        return

    group = await repo.get_group(session, group_id)
    title = escape_html(group.title) if group else str(group_id)
    await _edit(
        cb,
        S.v4_settings_title.format(title=title),
        reply_markup=v4_settings_menu_kb(group_id),
    )


# ---------------------------------------------------------------------------
# ── Protection ──────────────────────────────────────────────────────────────
# ---------------------------------------------------------------------------

@router.callback_query(F.data.startswith("v4s:protection:"))
async def cb_v4_protection(cb: CallbackQuery, bot: Bot, session: AsyncSession) -> None:
    await _answer(cb)
    group_id = int(cb.data.split(":")[2])
    if not await ensure_authorized(cb, bot, session, group_id):
        return

    group   = await repo.get_group(session, group_id)
    filters = await repo.get_filters(session, group_id)
    title   = escape_html(group.title) if group else str(group_id)
    await _edit(
        cb,
        S.v4_protection_title.format(title=title),
        reply_markup=v4_protection_kb(group_id, filters),
    )


@router.callback_query(F.data.startswith("v4s:prot_toggle:"))
async def cb_v4_prot_toggle(cb: CallbackQuery, bot: Bot, session: AsyncSession) -> None:
    await _answer(cb)
    parts    = cb.data.split(":")   # v4s:prot_toggle:{gid}:{ft}
    group_id = int(parts[2])
    ft       = parts[3]

    if not await ensure_authorized(cb, bot, session, group_id):
        return

    f = await repo.get_filter(session, group_id, ft)
    if not f:
        return
    new_state = not f.enabled
    await repo.update_filter(session, group_id, ft, enabled=new_state)

    # Sync external_links when toggling telegram_links
    if ft == "telegram_links":
        await repo.update_filter(session, group_id, "external_links", enabled=new_state)

    await repo.add_log(
        session, group_id=group_id, event_type="settings_changed",
        actor_id=cb.from_user.id,
        details=f"v4 prot {ft} → {'on' if new_state else 'off'}",
    )

    group   = await repo.get_group(session, group_id)
    filters = await repo.get_filters(session, group_id)
    title   = escape_html(group.title) if group else str(group_id)
    await _edit(
        cb,
        S.v4_protection_title.format(title=title),
        reply_markup=v4_protection_kb(group_id, filters),
    )


# ---------------------------------------------------------------------------
# ── Punishments ─────────────────────────────────────────────────────────────
# ---------------------------------------------------------------------------

@router.callback_query(F.data.startswith("v4s:punishments:"))
async def cb_v4_punishments(cb: CallbackQuery, bot: Bot, session: AsyncSession) -> None:
    await _answer(cb)
    group_id = int(cb.data.split(":")[2])
    if not await ensure_authorized(cb, bot, session, group_id):
        return

    group   = await repo.get_group(session, group_id)
    filters = await repo.get_filters(session, group_id)
    title   = escape_html(group.title) if group else str(group_id)
    await _edit(
        cb,
        S.v4_punishments_title.format(title=title),
        reply_markup=v4_punishments_kb(group_id, filters),
    )


@router.callback_query(F.data.startswith("v4s:pf_pick:"))
async def cb_v4_pf_pick(cb: CallbackQuery, bot: Bot, session: AsyncSession) -> None:
    await _answer(cb)
    _, _, group_id_str, ft = cb.data.split(":", 3)
    group_id = int(group_id_str)
    if not await ensure_authorized(cb, bot, session, group_id):
        return

    f = await repo.get_filter(session, group_id, ft)
    if not f:
        return

    filter_name  = _FILTER_LABELS.get(ft, ft)
    current_name = _ACTION_LABELS.get(f.action, f.action)
    await _edit(
        cb,
        S.v4_punishment_filter_title.format(
            filter_name=filter_name,
            current=current_name,
        ),
        reply_markup=v4_punishment_filter_kb(group_id, ft, f.action),
    )


@router.callback_query(F.data.startswith("v4s:pf_set:"))
async def cb_v4_pf_set(cb: CallbackQuery, bot: Bot, session: AsyncSession) -> None:
    await _answer(cb)
    parts       = cb.data.split(":")   # v4s:pf_set:{gid}:{ft}:{action}
    group_id    = int(parts[2])
    ft          = parts[3]
    action      = parts[4]

    if not await ensure_authorized(cb, bot, session, group_id):
        return

    await repo.update_filter(session, group_id, ft, action=action)
    await repo.add_log(
        session, group_id=group_id, event_type="settings_changed",
        actor_id=cb.from_user.id,
        details=f"v4 punishment {ft} → {action}",
    )

    filter_name  = _FILTER_LABELS.get(ft, ft)
    action_name  = _ACTION_LABELS.get(action, action)
    await _answer_alert(cb, f"✅ {filter_name} ← {action_name}")

    # Re-render the filter picker with updated selection
    await _edit(
        cb,
        S.v4_punishment_filter_title.format(
            filter_name=filter_name,
            current=action_name,
        ),
        reply_markup=v4_punishment_filter_kb(group_id, ft, action),
    )


# ---------------------------------------------------------------------------
# ── Admin Permissions ────────────────────────────────────────────────────────
# ---------------------------------------------------------------------------

@router.callback_query(F.data.startswith("v4s:perms:"))
async def cb_v4_perms(cb: CallbackQuery, bot: Bot, session: AsyncSession) -> None:
    await _answer(cb)
    group_id = int(cb.data.split(":")[2])
    if not await ensure_authorized(cb, bot, session, group_id):
        return

    group    = await repo.get_group(session, group_id)
    settings = await repo.get_settings(session, group_id)
    if not settings:
        return
    title = escape_html(group.title) if group else str(group_id)
    await _edit(
        cb,
        S.v4_permissions_title.format(title=title),
        reply_markup=v4_permissions_kb(group_id, settings),
    )


@router.callback_query(F.data.startswith("v4s:perm_toggle:"))
async def cb_v4_perm_toggle(cb: CallbackQuery, bot: Bot, session: AsyncSession) -> None:
    await _answer(cb)
    _, _, group_id_str, perm_key = cb.data.split(":", 3)
    group_id = int(group_id_str)

    # Only the group owner can change permissions
    if not await ensure_owner(cb, bot, session, group_id):
        return

    settings = await repo.get_settings(session, group_id)
    if not settings:
        return

    current_val = getattr(settings, perm_key, None)
    if current_val is None:
        return

    new_val = not current_val
    await repo.update_settings(session, group_id, **{perm_key: new_val})
    await repo.add_log(
        session, group_id=group_id, event_type="settings_changed",
        actor_id=cb.from_user.id,
        details=f"v4 perm {perm_key} → {new_val}",
    )

    # Re-render
    group    = await repo.get_group(session, group_id)
    updated  = await repo.get_settings(session, group_id)
    title    = escape_html(group.title) if group else str(group_id)
    await _edit(
        cb,
        S.v4_permissions_title.format(title=title),
        reply_markup=v4_permissions_kb(group_id, updated),
    )


# ---------------------------------------------------------------------------
# ── Welcome Message ──────────────────────────────────────────────────────────
# ---------------------------------------------------------------------------

@router.callback_query(F.data.startswith("v4s:welcome:"))
async def cb_v4_welcome(cb: CallbackQuery, bot: Bot, session: AsyncSession) -> None:
    await _answer(cb)
    group_id = int(cb.data.split(":")[2])
    if not await ensure_authorized(cb, bot, session, group_id):
        return

    group    = await repo.get_group(session, group_id)
    settings = await repo.get_settings(session, group_id)
    if not settings:
        return
    title  = escape_html(group.title) if group else str(group_id)
    status = f"{S.on} {S.enabled}" if settings.welcome_enabled else f"{S.off} {S.disabled}"
    await _edit(
        cb,
        S.v4_welcome_title.format(
            title=title,
            status=status,
            text=escape_html(settings.welcome_text),
        ),
        reply_markup=v4_welcome_kb(group_id, settings.welcome_enabled),
    )


@router.callback_query(F.data.startswith("v4s:welcome_toggle:"))
async def cb_v4_welcome_toggle(cb: CallbackQuery, bot: Bot, session: AsyncSession) -> None:
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

    group    = await repo.get_group(session, group_id)
    updated  = await repo.get_settings(session, group_id)
    title    = escape_html(group.title) if group else str(group_id)
    status   = f"{S.on} {S.enabled}" if updated.welcome_enabled else f"{S.off} {S.disabled}"
    await _edit(
        cb,
        S.v4_welcome_title.format(
            title=title,
            status=status,
            text=escape_html(updated.welcome_text),
        ),
        reply_markup=v4_welcome_kb(group_id, updated.welcome_enabled),
    )


@router.callback_query(F.data.startswith("v4s:welcome_edit:"))
async def cb_v4_welcome_edit(cb: CallbackQuery, bot: Bot, session: AsyncSession, state: FSMContext) -> None:
    await _answer(cb)
    group_id = int(cb.data.split(":")[2])
    if not await ensure_authorized(cb, bot, session, group_id):
        return

    settings = await repo.get_settings(session, group_id)
    current  = settings.welcome_text if settings else ""
    await state.update_data(group_id=group_id, fsm_type="welcome")
    await state.set_state(V4State.waiting_for_welcome_text)
    await _edit(
        cb,
        S.welcome_edit_prompt.format(current=escape_html(current)),
        reply_markup=back_kb(f"v4s:welcome:{group_id}"),
    )


@router.callback_query(F.data.startswith("v4s:welcome_preview:"))
async def cb_v4_welcome_preview(cb: CallbackQuery, bot: Bot, session: AsyncSession) -> None:
    await _answer(cb)
    group_id = int(cb.data.split(":")[2])
    if not await ensure_authorized(cb, bot, session, group_id):
        return

    settings = await repo.get_settings(session, group_id)
    if not settings:
        return
    name = escape_html(cb.from_user.first_name)
    username = cb.from_user.username or ""
    group    = await repo.get_group(session, group_id)
    group_name = escape_html(group.title) if group else ""
    preview_text = format_welcome(
        settings.welcome_text,
        first_name=cb.from_user.first_name,
        username=username,
        group_name=group.title if group else "",
    )
    await _answer_alert(cb, f"👁️ معاينة:\n\n{preview_text}")


# ---------------------------------------------------------------------------
# ── Goodbye Message ──────────────────────────────────────────────────────────
# ---------------------------------------------------------------------------

@router.callback_query(F.data.startswith("v4s:goodbye:"))
async def cb_v4_goodbye(cb: CallbackQuery, bot: Bot, session: AsyncSession) -> None:
    await _answer(cb)
    group_id = int(cb.data.split(":")[2])
    if not await ensure_authorized(cb, bot, session, group_id):
        return

    group    = await repo.get_group(session, group_id)
    settings = await repo.get_settings(session, group_id)
    if not settings:
        return
    title  = escape_html(group.title) if group else str(group_id)
    status = f"{S.on} {S.enabled}" if settings.goodbye_enabled else f"{S.off} {S.disabled}"
    await _edit(
        cb,
        S.v4_goodbye_title.format(
            title=title,
            status=status,
            text=escape_html(settings.goodbye_text),
        ),
        reply_markup=v4_goodbye_kb(group_id, settings.goodbye_enabled),
    )


@router.callback_query(F.data.startswith("v4s:goodbye_toggle:"))
async def cb_v4_goodbye_toggle(cb: CallbackQuery, bot: Bot, session: AsyncSession) -> None:
    await _answer(cb)
    group_id = int(cb.data.split(":")[2])
    if not await ensure_authorized(cb, bot, session, group_id):
        return

    settings = await repo.get_settings(session, group_id)
    if not settings:
        return
    new_val = not settings.goodbye_enabled
    await repo.update_settings(session, group_id, goodbye_enabled=new_val)
    await repo.add_log(
        session, group_id=group_id, event_type="settings_changed",
        actor_id=cb.from_user.id, details=f"goodbye_enabled → {new_val}",
    )

    group    = await repo.get_group(session, group_id)
    updated  = await repo.get_settings(session, group_id)
    title    = escape_html(group.title) if group else str(group_id)
    status   = f"{S.on} {S.enabled}" if updated.goodbye_enabled else f"{S.off} {S.disabled}"
    await _edit(
        cb,
        S.v4_goodbye_title.format(
            title=title,
            status=status,
            text=escape_html(updated.goodbye_text),
        ),
        reply_markup=v4_goodbye_kb(group_id, updated.goodbye_enabled),
    )


@router.callback_query(F.data.startswith("v4s:goodbye_edit:"))
async def cb_v4_goodbye_edit(cb: CallbackQuery, bot: Bot, session: AsyncSession, state: FSMContext) -> None:
    await _answer(cb)
    group_id = int(cb.data.split(":")[2])
    if not await ensure_authorized(cb, bot, session, group_id):
        return

    settings = await repo.get_settings(session, group_id)
    current  = settings.goodbye_text if settings else ""
    await state.update_data(group_id=group_id, fsm_type="goodbye")
    await state.set_state(V4State.waiting_for_goodbye_text)
    await _edit(
        cb,
        S.goodbye_edit_prompt.format(current=escape_html(current)),
        reply_markup=back_kb(f"v4s:goodbye:{group_id}"),
    )


@router.callback_query(F.data.startswith("v4s:goodbye_preview:"))
async def cb_v4_goodbye_preview(cb: CallbackQuery, bot: Bot, session: AsyncSession) -> None:
    await _answer(cb)
    group_id = int(cb.data.split(":")[2])
    if not await ensure_authorized(cb, bot, session, group_id):
        return

    settings = await repo.get_settings(session, group_id)
    if not settings:
        return
    group = await repo.get_group(session, group_id)
    preview_text = format_welcome(
        settings.goodbye_text,
        first_name=cb.from_user.first_name,
        username=cb.from_user.username or "",
        group_name=group.title if group else "",
    )
    await _answer_alert(cb, f"👁️ معاينة:\n\n{preview_text}")


# ---------------------------------------------------------------------------
# ── FSM: text input handlers ─────────────────────────────────────────────────
# ---------------------------------------------------------------------------

@router.message(V4State.waiting_for_welcome_text)
async def fsm_v4_welcome_text(message: Message, session: AsyncSession, state: FSMContext) -> None:
    data     = await state.get_data()
    group_id = data.get("group_id")
    await state.clear()
    text = (message.text or "").strip()
    if not text or not group_id:
        await message.reply(S.error)
        return
    await repo.update_settings(session, group_id, welcome_text=text)
    await message.reply(
        S.welcome_updated.format(text=escape_html(text)),
        parse_mode="HTML",
    )


@router.message(V4State.waiting_for_goodbye_text)
async def fsm_v4_goodbye_text(message: Message, session: AsyncSession, state: FSMContext) -> None:
    data     = await state.get_data()
    group_id = data.get("group_id")
    await state.clear()
    text = (message.text or "").strip()
    if not text or not group_id:
        await message.reply(S.error)
        return
    await repo.update_settings(session, group_id, goodbye_text=text)
    await message.reply(
        S.goodbye_updated.format(text=escape_html(text)),
        parse_mode="HTML",
    )


# ---------------------------------------------------------------------------
# ── Media Settings ───────────────────────────────────────────────────────────
# ---------------------------------------------------------------------------

@router.callback_query(F.data.startswith("v4s:media:"))
async def cb_v4_media(cb: CallbackQuery, bot: Bot, session: AsyncSession) -> None:
    await _answer(cb)
    group_id = int(cb.data.split(":")[2])
    if not await ensure_authorized(cb, bot, session, group_id):
        return

    group    = await repo.get_group(session, group_id)
    settings = await repo.get_settings(session, group_id)
    if not settings:
        return
    title = escape_html(group.title) if group else str(group_id)
    await _edit(
        cb,
        S.v4_media_title.format(title=title),
        reply_markup=v4_media_kb(group_id, settings),
    )


@router.callback_query(F.data.startswith("v4s:media_toggle:"))
async def cb_v4_media_toggle(cb: CallbackQuery, bot: Bot, session: AsyncSession) -> None:
    await _answer(cb)
    _, _, group_id_str, lock_key = cb.data.split(":", 3)
    group_id = int(group_id_str)
    if not await ensure_authorized(cb, bot, session, group_id):
        return

    settings = await repo.get_settings(session, group_id)
    if not settings:
        return
    current_val = getattr(settings, lock_key, False)
    new_val = not current_val
    await repo.update_settings(session, group_id, **{lock_key: new_val})
    await repo.add_log(
        session, group_id=group_id, event_type="settings_changed",
        actor_id=cb.from_user.id,
        details=f"v4 media {lock_key} → {'locked' if new_val else 'unlocked'}",
    )

    # Find the label for the media type
    label = next((lbl for k, lbl in _V4_MEDIA_LOCKS if k == lock_key), lock_key)
    alert = S.v4_media_locked.format(media_type=label) if new_val else S.v4_media_unlocked.format(media_type=label)
    await _answer_alert(cb, alert)

    group    = await repo.get_group(session, group_id)
    updated  = await repo.get_settings(session, group_id)
    title    = escape_html(group.title) if group else str(group_id)
    await _edit(
        cb,
        S.v4_media_title.format(title=title),
        reply_markup=v4_media_kb(group_id, updated),
    )


# ---------------------------------------------------------------------------
# ── Channel Settings ─────────────────────────────────────────────────────────
# ---------------------------------------------------------------------------

@router.callback_query(F.data.startswith("v4s:channel:"))
async def cb_v4_channel(cb: CallbackQuery, bot: Bot, session: AsyncSession) -> None:
    await _answer(cb)
    group_id = int(cb.data.split(":")[2])
    if not await ensure_authorized(cb, bot, session, group_id):
        return

    channels = await repo.get_all_channels(session)
    if not channels:
        await _edit(cb, S.v4_channel_no_channels, reply_markup=back_kb(f"v4s:menu:{group_id}"))
        return
    await _edit(
        cb,
        S.v4_channel_no_channels if not channels else S.channels_title,
        reply_markup=v4_channel_list_kb(channels, group_id),
    )


@router.callback_query(F.data.startswith("v4s:ch_panel:"))
async def cb_v4_ch_panel(cb: CallbackQuery, bot: Bot, session: AsyncSession) -> None:
    await _answer(cb)
    parts      = cb.data.split(":")   # v4s:ch_panel:{gid}:{chid}
    group_id   = int(parts[2])
    channel_id = int(parts[3])
    if not await ensure_authorized(cb, bot, session, group_id):
        return

    channel = await repo.get_channel(session, channel_id)
    if not channel:
        await _edit(cb, S.not_found, reply_markup=back_kb(f"v4s:channel:{group_id}"))
        return
    await _edit(
        cb,
        S.v4_channel_title.format(title=escape_html(channel.title)),
        reply_markup=v4_channel_panel_kb(group_id, channel_id),
    )


@router.callback_query(F.data.startswith("v4s:ch_info:"))
async def cb_v4_ch_info(cb: CallbackQuery, bot: Bot, session: AsyncSession) -> None:
    await _answer(cb)
    parts      = cb.data.split(":")
    group_id   = int(parts[2])
    channel_id = int(parts[3])
    if not await ensure_authorized(cb, bot, session, group_id):
        return

    channel = await repo.get_channel(session, channel_id)
    if not channel:
        await _answer_alert(cb, S.not_found)
        return

    username = f"@{channel.username}" if channel.username else "—"
    await _edit(
        cb,
        S.v4_ch_info_text.format(
            channel_id=channel_id,
            title=escape_html(channel.title),
            username=username,
        ),
        reply_markup=back_kb(f"v4s:ch_panel:{group_id}:{channel_id}"),
    )


@router.callback_query(F.data.startswith("v4s:ch_verify:"))
async def cb_v4_ch_verify(cb: CallbackQuery, bot: Bot, session: AsyncSession) -> None:
    await _answer(cb)
    parts      = cb.data.split(":")
    group_id   = int(parts[2])
    channel_id = int(parts[3])
    if not await ensure_authorized(cb, bot, session, group_id):
        return

    try:
        me = await bot.get_me()
        member = await bot.get_chat_member(channel_id, me.id)
        # Check if bot is admin with post permission
        has_perms = (
            member.status == "administrator"
            and getattr(member, "can_post_messages", False)
        )
        msg = S.v4_ch_verify_ok if has_perms else S.v4_ch_verify_fail
    except Exception:
        msg = S.v4_ch_verify_fail

    await _answer_alert(cb, msg)


@router.callback_query(F.data.startswith("v4s:ch_pin:"))
async def cb_v4_ch_pin(cb: CallbackQuery, bot: Bot, session: AsyncSession) -> None:
    await _answer(cb)
    parts      = cb.data.split(":")
    group_id   = int(parts[2])
    channel_id = int(parts[3])
    if not await ensure_authorized(cb, bot, session, group_id):
        return

    try:
        # Get the latest message id in the channel by sending and immediately deleting a temp message
        chat = await bot.get_chat(channel_id)
        # Pin the latest pinned message's message_id, or just attempt via Telegram
        # We attempt to fetch recent updates — simplest approach: ask user to use /pin in channel
        await _answer_alert(cb, "📌 استخدم /pin داخل القناة على الرسالة المطلوبة.")
    except Exception:
        await _answer_alert(cb, S.v4_ch_pin_fail)


@router.callback_query(F.data.startswith("v4s:ch_delete:"))
async def cb_v4_ch_delete(cb: CallbackQuery, bot: Bot, session: AsyncSession) -> None:
    await _answer(cb)
    parts      = cb.data.split(":")
    group_id   = int(parts[2])
    channel_id = int(parts[3])
    if not await ensure_authorized(cb, bot, session, group_id):
        return
    # Channel message deletion requires knowing the message_id which we don't have here.
    await _answer_alert(cb, "🗑️ استخدم /del داخل القناة بالرد على الرسالة المطلوبة.")


# ---------------------------------------------------------------------------
# ── Language ─────────────────────────────────────────────────────────────────
# ---------------------------------------------------------------------------

@router.callback_query(F.data.startswith("v4s:lang:"))
async def cb_v4_lang(cb: CallbackQuery, bot: Bot, session: AsyncSession) -> None:
    await _answer(cb)
    group_id = int(cb.data.split(":")[2])
    if not await ensure_authorized(cb, bot, session, group_id):
        return

    group    = await repo.get_group(session, group_id)
    settings = await repo.get_settings(session, group_id)
    if not settings:
        return
    title   = escape_html(group.title) if group else str(group_id)
    current = _lang_name(settings.language)
    await _edit(
        cb,
        S.v4_language_title.format(title=title, current=current),
        reply_markup=v4_language_kb(group_id, settings.language),
    )


@router.callback_query(F.data.startswith("v4s:lang_set:"))
async def cb_v4_lang_set(cb: CallbackQuery, bot: Bot, session: AsyncSession) -> None:
    await _answer(cb)
    _, _, group_id_str, lang_code = cb.data.split(":", 3)
    group_id = int(group_id_str)
    if not await ensure_authorized(cb, bot, session, group_id):
        return

    await repo.update_settings(session, group_id, language=lang_code)
    await repo.add_log(
        session, group_id=group_id, event_type="settings_changed",
        actor_id=cb.from_user.id, details=f"language → {lang_code}",
    )

    lang_name = _lang_name(lang_code)
    await _answer_alert(cb, S.v4_language_set.format(lang=lang_name))

    # Re-render
    group   = await repo.get_group(session, group_id)
    title   = escape_html(group.title) if group else str(group_id)
    await _edit(
        cb,
        S.v4_language_title.format(title=title, current=lang_name),
        reply_markup=v4_language_kb(group_id, lang_code),
    )


# ---------------------------------------------------------------------------
# ── V6/V7: AI Protection (Gemini) ─────────────────────────────────────────────
# ---------------------------------------------------------------------------

_AI_SENS_LABELS = {"low": S.ai_sensitivity_low, "medium": S.ai_sensitivity_medium, "high": S.ai_sensitivity_high}


async def _ai_system_status(session: AsyncSession, ai_enabled: bool) -> str:
    """
    V7: 3-state system status for the AI panel header.
    🟢 يعمل بشكل طبيعي  — AI on + usable keys
    🟡 جاري إعادة المحاولة — AI on + keys exist but all cooling down
    🔴 متوقف              — AI off, or no enabled keys at all
    """
    if not ai_enabled:
        return S.ai_status_no_keys

    from bot.ai.key_manager import key_manager
    counts = await repo.count_ai_keys(session, "gemini")

    if counts["enabled"] == 0:
        return S.ai_status_no_keys
    if key_manager.has_cooling_down_keys("gemini"):
        return S.ai_status_retrying
    return S.ai_status_ok


@router.callback_query(F.data.startswith("v4s:ai:"))
async def cb_v4_ai(cb: CallbackQuery, bot: Bot, session: AsyncSession) -> None:
    await _answer(cb)
    group_id = int(cb.data.split(":")[2])
    if not await ensure_authorized(cb, bot, session, group_id):
        return

    group         = await repo.get_group(session, group_id)
    settings      = await repo.get_settings(session, group_id)
    title         = escape_html(group.title) if group else str(group_id)
    system_status = await _ai_system_status(session, settings.ai_enabled)
    await _edit(
        cb,
        S.ai_settings_title.format(title=title, system_status=system_status),
        reply_markup=v4_ai_settings_kb(group_id, settings),
    )


async def _rerender_ai_panel(cb: CallbackQuery, session: AsyncSession, group_id: int) -> None:
    group         = await repo.get_group(session, group_id)
    settings      = await repo.get_settings(session, group_id)
    title         = escape_html(group.title) if group else str(group_id)
    system_status = await _ai_system_status(session, settings.ai_enabled)
    await _edit(
        cb,
        S.ai_settings_title.format(title=title, system_status=system_status),
        reply_markup=v4_ai_settings_kb(group_id, settings),
    )


@router.callback_query(F.data.startswith("v4s:ai_toggle:"))
async def cb_v4_ai_toggle(cb: CallbackQuery, bot: Bot, session: AsyncSession) -> None:
    await _answer(cb)
    group_id = int(cb.data.split(":")[2])
    if not await ensure_authorized(cb, bot, session, group_id):
        return

    settings = await repo.get_settings(session, group_id)
    new_state = not settings.ai_enabled
    await repo.update_settings(session, group_id, ai_enabled=new_state)
    await repo.add_log(
        session, group_id=group_id, event_type="settings_changed",
        actor_id=cb.from_user.id, details=f"ai_enabled → {new_state}",
    )

    # V7.1: if the person enabling AI is also the bot owner and no Gemini key
    # has ever been registered, send them straight to the setup wizard instead
    # of leaving them looking at a silent 🔴 "no keys" status. Group owners who
    # are NOT the bot owner never see this — they can't manage keys anyway.
    if new_state and is_bot_owner_id(cb.from_user.id):
        counts = await repo.count_ai_keys(session, "gemini")
        if counts["total"] == 0 and cb.message:
            await cb.message.edit_text(
                S.ai_setup_wizard_title, parse_mode="HTML", reply_markup=ai_setup_wizard_kb(),
            )
            return

    await _rerender_ai_panel(cb, session, group_id)


@router.callback_query(F.data.startswith("v4s:ai_toggle_msgs:"))
async def cb_v4_ai_toggle_msgs(cb: CallbackQuery, bot: Bot, session: AsyncSession) -> None:
    await _answer(cb)
    group_id = int(cb.data.split(":")[2])
    if not await ensure_authorized(cb, bot, session, group_id):
        return

    settings = await repo.get_settings(session, group_id)
    await repo.update_settings(session, group_id, ai_analyze_messages=not settings.ai_analyze_messages)
    await _rerender_ai_panel(cb, session, group_id)


@router.callback_query(F.data.startswith("v4s:ai_toggle_images:"))
async def cb_v4_ai_toggle_images(cb: CallbackQuery, bot: Bot, session: AsyncSession) -> None:
    await _answer(cb)
    group_id = int(cb.data.split(":")[2])
    if not await ensure_authorized(cb, bot, session, group_id):
        return

    settings = await repo.get_settings(session, group_id)
    await repo.update_settings(session, group_id, ai_analyze_images=not settings.ai_analyze_images)
    await _rerender_ai_panel(cb, session, group_id)


@router.callback_query(F.data.startswith("v4s:ai_toggle_links:"))
async def cb_v4_ai_toggle_links(cb: CallbackQuery, bot: Bot, session: AsyncSession) -> None:
    """V7: Toggle dedicated link / URL analysis."""
    await _answer(cb)
    group_id = int(cb.data.split(":")[2])
    if not await ensure_authorized(cb, bot, session, group_id):
        return

    settings = await repo.get_settings(session, group_id)
    new_state = not getattr(settings, "ai_analyze_links", False)
    await repo.update_settings(session, group_id, ai_analyze_links=new_state)
    await repo.add_log(
        session, group_id=group_id, event_type="settings_changed",
        actor_id=cb.from_user.id, details=f"ai_analyze_links → {new_state}",
    )
    await _rerender_ai_panel(cb, session, group_id)


@router.callback_query(F.data.startswith("v4s:ai_toggle_profiles:"))
async def cb_v4_ai_toggle_profiles(cb: CallbackQuery, bot: Bot, session: AsyncSession) -> None:
    """V7.2: Toggle username/display-name + group description AI screening."""
    await _answer(cb)
    group_id = int(cb.data.split(":")[2])
    if not await ensure_authorized(cb, bot, session, group_id):
        return

    settings = await repo.get_settings(session, group_id)
    new_state = not getattr(settings, "ai_analyze_profiles", True)
    await repo.update_settings(session, group_id, ai_analyze_profiles=new_state)
    await repo.add_log(
        session, group_id=group_id, event_type="settings_changed",
        actor_id=cb.from_user.id, details=f"ai_analyze_profiles → {new_state}",
    )
    await _rerender_ai_panel(cb, session, group_id)


@router.callback_query(F.data.startswith("v4s:ai_sens:"))
async def cb_v4_ai_sens(cb: CallbackQuery, bot: Bot, session: AsyncSession) -> None:
    await _answer(cb)
    group_id = int(cb.data.split(":")[2])
    if not await ensure_authorized(cb, bot, session, group_id):
        return

    settings = await repo.get_settings(session, group_id)
    await _edit(
        cb,
        S.ai_sensitivity_title,
        reply_markup=v4_ai_sensitivity_kb(group_id, settings.ai_sensitivity),
    )


@router.callback_query(F.data.startswith("v4s:ai_sens_set:"))
async def cb_v4_ai_sens_set(cb: CallbackQuery, bot: Bot, session: AsyncSession) -> None:
    await _answer(cb)
    _, _, group_id_str, level = cb.data.split(":", 3)
    group_id = int(group_id_str)
    if not await ensure_authorized(cb, bot, session, group_id):
        return

    await repo.update_settings(session, group_id, ai_sensitivity=level)
    await repo.add_log(
        session, group_id=group_id, event_type="settings_changed",
        actor_id=cb.from_user.id, details=f"ai_sensitivity → {level}",
    )
    await _rerender_ai_panel(cb, session, group_id)


@router.callback_query(F.data.startswith("v4s:ai_actions:"))
async def cb_v4_ai_actions(cb: CallbackQuery, bot: Bot, session: AsyncSession) -> None:
    """V7: Show multi-action selection panel."""
    await _answer(cb)
    group_id = int(cb.data.split(":")[2])
    if not await ensure_authorized(cb, bot, session, group_id):
        return

    settings = await repo.get_settings(session, group_id)
    await _edit(
        cb,
        S.ai_actions_title,
        reply_markup=v4_ai_actions_kb(group_id, settings),
    )


@router.callback_query(F.data.startswith("v4s:ai_action_toggle:"))
async def cb_v4_ai_action_toggle(cb: CallbackQuery, bot: Bot, session: AsyncSession) -> None:
    """V7: Toggle one AI action on / off."""
    await _answer(cb)
    parts = cb.data.split(":")   # v4s:ai_action_toggle:{gid}:{action}
    group_id = int(parts[2])
    action   = parts[3]          # delete | warn | mute | ban
    if not await ensure_authorized(cb, bot, session, group_id):
        return

    col_map = {
        "delete": "ai_action_delete",
        "warn":   "ai_action_warn",
        "mute":   "ai_action_mute",
        "ban":    "ai_action_ban",
    }
    col = col_map.get(action)
    if not col:
        return

    settings  = await repo.get_settings(session, group_id)
    new_state = not getattr(settings, col, False)
    await repo.update_settings(session, group_id, **{col: new_state})
    await repo.add_log(
        session, group_id=group_id, event_type="settings_changed",
        actor_id=cb.from_user.id, details=f"{col} → {new_state}",
    )
    # Re-render the actions panel
    settings = await repo.get_settings(session, group_id)
    await _edit(
        cb,
        S.ai_actions_title,
        reply_markup=v4_ai_actions_kb(group_id, settings),
    )


@router.callback_query(F.data.startswith("v4s:ai_status:"))
async def cb_v4_ai_status(cb: CallbackQuery, bot: Bot, session: AsyncSession) -> None:
    """V7: 3-state system status page."""
    await _answer(cb)
    group_id = int(cb.data.split(":")[2])
    if not await ensure_authorized(cb, bot, session, group_id):
        return

    settings = await repo.get_settings(session, group_id)
    counts   = await repo.count_ai_keys(session, "gemini")
    overall  = await _ai_system_status(session, settings.ai_enabled)
    await _edit(
        cb,
        S.ai_status_title.format(
            enabled_keys=counts["enabled"], total_keys=counts["total"], overall_status=overall,
        ),
        reply_markup=v4_ai_status_kb(group_id),
    )



@router.callback_query(F.data.startswith("v4s:ai_test:"))
async def cb_v4_ai_test(cb: CallbackQuery, bot: Bot, session: AsyncSession) -> None:
    """RC1: Live Gemini connectivity test — 🧪 test button on the AI status page."""
    await _answer(cb)
    group_id = int(cb.data.split(":")[2])
    if not await ensure_authorized(cb, bot, session, group_id):
        return

    # Show spinner immediately so the owner knows the request is in flight
    await _edit(cb, S.ai_test_running)

    counts = await repo.count_ai_keys(session, "gemini")
    if counts["enabled"] == 0:
        await _edit(
            cb,
            S.ai_test_no_keys,
            reply_markup=back_kb(f"v4s:ai_status:{group_id}"),
        )
        return

    result = await ai_manager.test_connection(session)

    if result["ok"]:
        text = S.ai_test_result_ok.format(
            latency_ms=result["latency_ms"],
            model=result["model"],
            key_mask=result.get("key_mask", "••••••••"),
            active_keys=counts["enabled"],
        )
    else:
        text = S.ai_test_result_fail.format(
            error=_gemini_err_to_arabic(result.get("error")),
        )

    await _edit(
        cb,
        text,
        reply_markup=back_kb(f"v4s:ai_status:{group_id}"),
    )


# ---------------------------------------------------------------------------
# ── Reset Settings ────────────────────────────────────────────────────────────
# ---------------------------------------------------------------------------

@router.callback_query(F.data.startswith("v4s:reset:"))
async def cb_v4_reset(cb: CallbackQuery, bot: Bot, session: AsyncSession) -> None:
    await _answer(cb)
    group_id = int(cb.data.split(":")[2])
    # Only owner can reset
    if not await ensure_owner(cb, bot, session, group_id):
        return

    await _edit(
        cb,
        S.v4_reset_confirm,
        reply_markup=v4_reset_confirm_kb(group_id),
    )


@router.callback_query(F.data.startswith("v4s:reset_confirm:"))
async def cb_v4_reset_confirm(cb: CallbackQuery, bot: Bot, session: AsyncSession) -> None:
    await _answer(cb, "جارٍ إعادة الضبط…")
    group_id = int(cb.data.split(":")[2])
    # Only owner can reset
    if not await ensure_owner(cb, bot, session, group_id):
        return

    await repo.reset_group_settings(session, group_id)
    await repo.add_log(
        session, group_id=group_id, event_type="settings_changed",
        actor_id=cb.from_user.id, details="full settings reset",
    )
    await _edit(
        cb,
        S.v4_reset_done,
        reply_markup=back_kb(f"v4s:menu:{group_id}"),
    )
