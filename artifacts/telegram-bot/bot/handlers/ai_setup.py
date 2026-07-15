"""
Gemini API Key Manager — inline-button setup wizard — V7.1.

Bot-owner-only (gated by IsBotOwner, same as the slash-command equivalents in
ai_admin.py, which remain fully functional for backwards compatibility).

Flow
----
1. Owner presses "🧠 إدارة مفاتيح Gemini" on the home dashboard.
2. No keys yet → first-time setup wizard (➕ إضافة مفتاح / 🔙 رجوع).
   Keys exist   → management screen (➕ add / ❌ delete / 📋 count-only / 🔙 back).
3. "➕ إضافة مفتاح" → bot sets FSM state and waits for the NEXT message, which
   is treated as the raw Gemini API key. It is masked + encrypted (never
   stored or logged in plaintext) and the triggering message is deleted.
4. "❌ حذف مفتاح" → pick a key from a list → confirm → delete.

Security
--------
- Every handler here is gated to bot owners only (group owners/admins never
  see this screen — they only control per-group AI toggles).
- Raw keys are never logged, never redisplayed after being saved — only the
  masked form computed at insertion time is ever shown again.
"""

from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.ai.key_manager import key_manager
from bot.ai.manager import ai_manager
from bot.filters.admin_filter import IsBotOwner
from utils.ai_helpers import gemini_err_to_arabic as _gemini_err_to_arabic
from bot.keyboards.builder import (
    ai_key_delete_confirm_kb,
    ai_key_delete_menu_kb,
    ai_key_manager_kb,
    ai_setup_cancel_kb,
    ai_setup_wizard_kb,
)
from bot.strings.ar import S
from database import repository as repo
from utils.logger import get_logger

log = get_logger(__name__)
router = Router(name="ai_setup")

_PROVIDER = "gemini"
_MIN_KEY_LENGTH = 10



class AIKeyState(StatesGroup):
    waiting_for_key = State()


async def _answer(cb: CallbackQuery) -> None:
    try:
        await cb.answer()
    except Exception:
        pass


async def _render_manager_screen(target: Message, session: AsyncSession) -> None:
    """Render either the empty-state wizard or the full key-manager screen."""
    keys = await repo.list_ai_keys(session, provider=_PROVIDER)
    log.info("ai_key_manager: rendering screen with %d key(s)", len(keys))

    if not keys:
        await target.edit_text(S.ai_setup_wizard_title, parse_mode="HTML", reply_markup=ai_setup_wizard_kb())
        return

    counts = await repo.count_ai_keys(session, _PROVIDER)
    lines = []
    for k in keys:
        status = S.ai_admin_key_status_enabled if k.enabled else S.ai_admin_key_status_disabled
        label = k.label or S.ai_setup_key_label_default.format(id=k.id)
        lines.append(S.ai_setup_key_line.format(
            label=f"#{k.id} {label}", status=status, health=k.health_status(), masked=k.masked_key(),
        ))

    text = S.ai_setup_manager_title.format(
        total=counts["total"], enabled=counts["enabled"], key_list="\n".join(lines) + "\n",
    )
    await target.edit_text(text, parse_mode="HTML", reply_markup=ai_key_manager_kb(keys))


@router.callback_query(F.data == "aisetup:open", IsBotOwner())
async def cb_ai_setup_open(cb: CallbackQuery, session: AsyncSession) -> None:
    await _answer(cb)
    if not cb.message:
        return
    await _render_manager_screen(cb.message, session)


@router.callback_query(F.data == "aisetup:open")
async def cb_ai_setup_open_denied(cb: CallbackQuery) -> None:
    """Non-owners can never reach this screen even if they guess the callback."""
    await cb.answer(S.ai_setup_not_owner, show_alert=True)


@router.callback_query(F.data == "aisetup:add", IsBotOwner())
async def cb_ai_setup_add(cb: CallbackQuery, state: FSMContext) -> None:
    await _answer(cb)
    if not cb.message:
        return
    await state.set_state(AIKeyState.waiting_for_key)
    await cb.message.edit_text(S.ai_setup_addkey_prompt, parse_mode="HTML", reply_markup=ai_setup_cancel_kb())


@router.message(AIKeyState.waiting_for_key, IsBotOwner())
async def fsm_receive_key(message: Message, state: FSMContext, session: AsyncSession) -> None:
    raw = (message.text or "").strip()

    if len(raw) < _MIN_KEY_LENGTH or " " in raw:
        await message.reply(S.ai_setup_addkey_invalid, parse_mode="HTML")
        return  # stay in the same state — let them try again

    # Delete the message containing the raw key immediately, regardless of the
    # outcome below — it must never linger in chat history either way.
    try:
        await message.delete()
    except Exception as exc:
        log.warning("Could not delete /aisetup key message: %s", exc)

    verifying = await message.answer(S.ai_setup_verifying, parse_mode="HTML")

    is_valid, _err = await ai_manager.validate_key(_PROVIDER, raw)
    if not is_valid:
        log.info("ai_key_rejected: added_by=%s reason=%r (not saved)", message.from_user.id, _err)
        await verifying.edit_text(_gemini_err_to_arabic(_err), parse_mode="HTML", reply_markup=ai_setup_cancel_kb())
        return  # stay in the same state — let them try another key

    key_row = await repo.add_ai_key(session, provider=_PROVIDER, api_key=raw, added_by=message.from_user.id)
    key_manager.invalidate(_PROVIDER)
    await state.clear()
    log.info("ai_key_added: key_id=%s added_by=%s via inline wizard (verified)", key_row.id, message.from_user.id)

    await verifying.edit_text(S.ai_key_verified_ok, parse_mode="HTML")
    await _render_manager_screen(verifying, session)


@router.callback_query(F.data == "aisetup:delmenu", IsBotOwner())
async def cb_ai_delmenu(cb: CallbackQuery, session: AsyncSession) -> None:
    await _answer(cb)
    if not cb.message:
        return
    keys = await repo.list_ai_keys(session, provider=_PROVIDER)
    if not keys:
        await cb.message.edit_text(S.ai_setup_delmenu_empty, parse_mode="HTML", reply_markup=ai_setup_wizard_kb())
        return
    await cb.message.edit_text(S.ai_setup_delmenu_title, parse_mode="HTML", reply_markup=ai_key_delete_menu_kb(keys))


@router.callback_query(F.data.startswith("aisetup:delconfirm:"), IsBotOwner())
async def cb_ai_delconfirm(cb: CallbackQuery) -> None:
    await _answer(cb)
    if not cb.message:
        return
    key_id = int(cb.data.split(":")[2])
    await cb.message.edit_text(
        S.ai_setup_delconfirm_title.format(key_id=key_id),
        parse_mode="HTML",
        reply_markup=ai_key_delete_confirm_kb(key_id),
    )


@router.callback_query(F.data.startswith("aisetup:del:"), IsBotOwner())
async def cb_ai_del(cb: CallbackQuery, session: AsyncSession) -> None:
    await _answer(cb)
    if not cb.message:
        return
    key_id = int(cb.data.split(":")[2])
    row = await repo.get_ai_key(session, key_id)
    provider = row.provider if row else _PROVIDER
    await repo.delete_ai_key(session, key_id)
    key_manager.invalidate(provider)
    log.info("ai_key_deleted: key_id=%s deleted_by=%s", key_id, cb.from_user.id)

    await cb.message.edit_text(S.ai_setup_key_deleted, parse_mode="HTML")
    await _render_manager_screen(cb.message, session)


@router.callback_query(F.data == "aisetup:count", IsBotOwner())
async def cb_ai_count(cb: CallbackQuery, session: AsyncSession) -> None:
    await _answer(cb)
    if not cb.message:
        return
    counts = await repo.count_ai_keys(session, _PROVIDER)
    await cb.message.edit_text(
        S.ai_setup_count_only.format(total=counts["total"], enabled=counts["enabled"]),
        parse_mode="HTML",
        reply_markup=ai_key_manager_kb([]),
    )
