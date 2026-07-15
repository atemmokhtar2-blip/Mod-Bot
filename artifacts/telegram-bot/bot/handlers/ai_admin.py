"""
Global Gemini API Key Manager — bot-owner-only commands — V6.

These commands manage a bot-wide resource (the AI API key pool), not a
per-group setting, so they are gated by IsBotOwner (config.BOT_OWNER_IDS)
rather than the per-group owner/admin checks used everywhere else.

Commands
--------
/addaikey <key> [label]  — register a new Gemini API key (message is deleted
                            immediately after processing so the raw key never
                            lingers in chat history)
/listaikeys               — list all registered keys (masked) with usage stats
/togglekey <id>           — enable/disable a key
/delkey <id>              — permanently delete a key
/aistatus                 — quick global AI health summary
"""

from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.ai.key_manager import key_manager
from bot.ai.manager import ai_manager
from bot.filters.admin_filter import IsBotOwner
from bot.strings.ar import S
from database import repository as repo
from utils.logger import get_logger

log = get_logger(__name__)
router = Router(name="ai_admin")

# All commands here are gated to bot owners only (global resource management).
router.message.filter(IsBotOwner())

_PROVIDER = "gemini"


@router.message(Command("addaikey"))
async def cmd_addaikey(message: Message, session: AsyncSession) -> None:
    args = (message.text or "").split(maxsplit=2)
    # args[0] = /addaikey, args[1] = key, args[2] = optional label
    if len(args) < 2 or not args[1].strip():
        await message.reply(S.ai_admin_addkey_usage, parse_mode="HTML")
        return

    api_key = args[1].strip()
    label = args[2].strip() if len(args) > 2 else None

    # Delete the user's message immediately regardless of outcome — it
    # contains the raw key and must never linger in chat history.
    try:
        await message.delete()
    except Exception as exc:
        log.warning("Could not delete /addaikey message: %s", exc)

    verifying = await message.answer(S.ai_setup_verifying, parse_mode="HTML")

    is_valid, _err = await ai_manager.validate_key(_PROVIDER, api_key)
    if not is_valid:
        log.info("ai_key_rejected: added_by=%s reason=invalid_key (not saved)", message.from_user.id)
        await verifying.edit_text(S.ai_key_invalid_gemini, parse_mode="HTML")
        return

    key_row = await repo.add_ai_key(
        session, provider=_PROVIDER, api_key=api_key, label=label, added_by=message.from_user.id,
    )
    key_manager.invalidate(_PROVIDER)
    log.info("ai_key_added: key_id=%s added_by=%s via /addaikey (verified)", key_row.id, message.from_user.id)

    await verifying.edit_text(
        f"{S.ai_key_verified_ok}\n{S.ai_admin_key_added.format(key_id=key_row.id)}", parse_mode="HTML",
    )


@router.message(Command("listaikeys"))
async def cmd_listaikeys(message: Message, session: AsyncSession) -> None:
    keys = await repo.list_ai_keys(session, provider=_PROVIDER)
    if not keys:
        await message.reply(S.ai_admin_no_keys, parse_mode="HTML")
        return

    lines = [S.ai_admin_keys_list_header]
    for k in keys:
        status = S.ai_admin_key_status_enabled if k.enabled else S.ai_admin_key_status_disabled
        lines.append(S.ai_admin_key_row.format(
            id=k.id,
            status=status,
            health=k.health_status(),
            label=k.label or "—",
            masked=k.masked_key(),
            usage=k.usage_count,
            success=k.success_count,
            failure=k.failure_count,
        ))
    await message.reply("".join(lines), parse_mode="HTML")


@router.message(Command("togglekey"))
async def cmd_togglekey(message: Message, session: AsyncSession) -> None:
    args = (message.text or "").split()
    if len(args) < 2 or not args[1].isdigit():
        await message.reply(S.ai_admin_togglekey_usage, parse_mode="HTML")
        return

    key_id = int(args[1])
    row = await repo.get_ai_key(session, key_id)
    if not row:
        await message.reply(S.ai_admin_key_not_found, parse_mode="HTML")
        return

    new_state = not row.enabled
    await repo.toggle_ai_key(session, key_id, new_state)
    key_manager.invalidate(row.provider)

    text = S.ai_admin_key_enabled if new_state else S.ai_admin_key_disabled
    await message.reply(text.format(key_id=key_id), parse_mode="HTML")


@router.message(Command("delkey"))
async def cmd_delkey(message: Message, session: AsyncSession) -> None:
    args = (message.text or "").split()
    if len(args) < 2 or not args[1].isdigit():
        await message.reply(S.ai_admin_delkey_usage, parse_mode="HTML")
        return

    key_id = int(args[1])
    row = await repo.get_ai_key(session, key_id)
    if not row:
        await message.reply(S.ai_admin_key_not_found, parse_mode="HTML")
        return

    await repo.delete_ai_key(session, key_id)
    key_manager.invalidate(row.provider)
    await message.reply(S.ai_admin_key_deleted.format(key_id=key_id), parse_mode="HTML")


@router.message(Command("aistatus"))
async def cmd_aistatus(message: Message, session: AsyncSession) -> None:
    counts = await repo.count_ai_keys(session, _PROVIDER)
    await message.reply(
        S.ai_admin_aistatus.format(total=counts["total"], enabled=counts["enabled"]),
        parse_mode="HTML",
    )
