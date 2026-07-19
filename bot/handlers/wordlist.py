"""
Custom word-list management commands — V4.1.

Commands (group and private)
-----------------------------
/addword  <word>   — add a word to this group's blocked list
/removeword <word> — remove a word from the blocked list
/listwords         — show all custom blocked words
/clearwords        — clear the entire custom list (owner only)

All commands require the caller to be an authorized bot-admin or the owner.
The /clearwords command is restricted to the group owner.
"""

from __future__ import annotations

from aiogram import Bot, Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.filters.admin_filter import IsGroupAdmin
from bot.strings.ar import S
from database import repository as repo
from utils.helpers import escape_html
from utils.logger import get_logger
from utils.profanity.normalizer import normalize as norm_word
from utils.profanity.engine import engine as profanity_engine

log = get_logger(__name__)
router = Router(name="wordlist")

# Only group admins may use these commands
router.message.filter(IsGroupAdmin())

# ---------------------------------------------------------------------------
# In-process word-list cache — shared with message_filter.py
# Import the shared invalidation function
# ---------------------------------------------------------------------------

from bot.handlers.message_filter import wordlist_cache_invalidate


# ---------------------------------------------------------------------------
# /addword <word>
# ---------------------------------------------------------------------------

@router.message(Command("addword"))
async def cmd_addword(message: Message, session: AsyncSession) -> None:
    group_id = message.chat.id
    args = (message.text or "").split(maxsplit=1)

    if len(args) < 2 or not args[1].strip():
        await message.reply(S.wordlist_addword_usage, parse_mode="HTML")
        return

    raw_word = args[1].strip()
    normalized = norm_word(raw_word)

    if not normalized or len(normalized) < 2:
        await message.reply(S.wordlist_word_too_short, parse_mode="HTML")
        return

    if len(raw_word) > 100:
        await message.reply(S.wordlist_word_too_long, parse_mode="HTML")
        return

    # Check custom word limit per group
    count = await repo.count_custom_words(session, group_id)
    if count >= 500:
        await message.reply(S.wordlist_limit_reached, parse_mode="HTML")
        return

    added, status = await repo.add_custom_word(
        session,
        group_id=group_id,
        word_original=raw_word,
        word_normalized=normalized,
        added_by=message.from_user.id,
    )

    if added:
        # Invalidate caches so next message scan picks up the new word
        wordlist_cache_invalidate(group_id)
        profanity_engine.invalidate(group_id)
        await message.reply(
            S.wordlist_added.format(word=escape_html(raw_word)),
            parse_mode="HTML",
        )
    else:
        await message.reply(
            S.wordlist_already_exists.format(word=escape_html(raw_word)),
            parse_mode="HTML",
        )


# ---------------------------------------------------------------------------
# /removeword <word>
# ---------------------------------------------------------------------------

@router.message(Command("removeword"))
async def cmd_removeword(message: Message, session: AsyncSession) -> None:
    group_id = message.chat.id
    args = (message.text or "").split(maxsplit=1)

    if len(args) < 2 or not args[1].strip():
        await message.reply(S.wordlist_removeword_usage, parse_mode="HTML")
        return

    raw_word = args[1].strip()
    normalized = norm_word(raw_word)

    removed = await repo.remove_custom_word(session, group_id, normalized)
    if removed:
        wordlist_cache_invalidate(group_id)
        profanity_engine.invalidate(group_id)
        await message.reply(
            S.wordlist_removed.format(word=escape_html(raw_word)),
            parse_mode="HTML",
        )
    else:
        await message.reply(
            S.wordlist_not_found.format(word=escape_html(raw_word)),
            parse_mode="HTML",
        )


# ---------------------------------------------------------------------------
# /listwords
# ---------------------------------------------------------------------------

@router.message(Command("listwords"))
async def cmd_listwords(message: Message, session: AsyncSession) -> None:
    group_id = message.chat.id
    words = await repo.get_custom_words(session, group_id)

    if not words:
        await message.reply(S.wordlist_empty, parse_mode="HTML")
        return

    # Build paginated reply (max 50 words per message)
    PAGE = 50
    total = len(words)
    lines: list[str] = [
        S.wordlist_list_header.format(count=total, builtin=profanity_engine.builtin_word_count)
    ]
    for i, cw in enumerate(words[:PAGE], start=1):
        lines.append(f"  {i}. <code>{escape_html(cw.word_original)}</code>")

    if total > PAGE:
        lines.append(S.wordlist_list_truncated.format(shown=PAGE, total=total))

    await message.reply("\n".join(lines), parse_mode="HTML")


# ---------------------------------------------------------------------------
# /clearwords  (owner only)
# ---------------------------------------------------------------------------

@router.message(Command("clearwords"))
async def cmd_clearwords(message: Message, session: AsyncSession) -> None:
    group_id = message.chat.id

    # Restrict to group owner
    if not await repo.is_owner(session, group_id, message.from_user.id):
        await message.reply(S.owner_only_cb, parse_mode="HTML")
        return

    count = await repo.clear_custom_words(session, group_id)
    if count:
        wordlist_cache_invalidate(group_id)
        profanity_engine.invalidate(group_id)
        await message.reply(
            S.wordlist_cleared.format(count=count),
            parse_mode="HTML",
        )
    else:
        await message.reply(S.wordlist_empty, parse_mode="HTML")
