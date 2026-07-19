"""
Group & channel registration service.
Called when the bot is added to / removed from a chat.
Future: add onboarding wizard, group-tier system.
"""

from __future__ import annotations

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest
from sqlalchemy.ext.asyncio import AsyncSession

from database import repository as repo
from utils.logger import get_logger

log = get_logger(__name__)


async def register_group(
    session: AsyncSession,
    bot: Bot,
    chat_id: int,
    added_by_user_id: int | None = None,
) -> None:
    """
    Fetch live chat info and upsert the group row with all defaults.

    This is the single source of truth for "the bot is in this group" — it
    MUST always persist group id / title / owner / registration timestamp
    even if secondary steps (admin sync, filter seeding) fail, so that the
    private control panel can always find the group afterwards.

    owner_id resolution order:
      1. Telegram "creator" of the chat (authoritative).
      2. `added_by_user_id` — whoever performed the action that added/promoted
         the bot (from the ChatMemberUpdated event). This ensures the person
         who actually set the bot up is never locked out of the panel even if
         they aren't the chat's literal "creator".
    """
    log.info("bot_added: chat_id=%s added_by=%s — starting registration", chat_id, added_by_user_id)

    try:
        chat = await bot.get_chat(chat_id)
    except TelegramBadRequest as exc:
        log.error("bot_added: could not fetch chat %s: %s", chat_id, exc)
        return

    # ------------------------------------------------------------------
    # Resolve owner + collect all admins so we can sync every one of them,
    # not just the "creator". AI settings/filters are handled separately
    # below and must never block this critical path.
    # ------------------------------------------------------------------
    owner_id: int | None = None
    admin_users: list = []
    try:
        admins = await bot.get_chat_administrators(chat_id)
        for a in admins:
            if a.status in ("creator", "administrator"):
                admin_users.append(a)
                await repo.upsert_user(
                    session,
                    user_id=a.user.id,
                    first_name=a.user.first_name,
                    last_name=a.user.last_name,
                    username=a.user.username,
                )
            if a.status == "creator":
                owner_id = a.user.id
        log.info(
            "admin_lookup: chat_id=%s found %d admin(s) (creator=%s)",
            chat_id, len(admin_users), owner_id,
        )
    except TelegramBadRequest as exc:
        log.warning("admin_lookup: could not fetch admins for %s: %s", chat_id, exc)

    if owner_id is None and added_by_user_id is not None:
        owner_id = added_by_user_id
        log.info(
            "owner_assigned: chat_id=%s no Telegram 'creator' found — falling back to inviter %s",
            chat_id, owner_id,
        )

    # ------------------------------------------------------------------
    # Critical path: save group id / title / owner / registration timestamp.
    # created_at/updated_at are stamped automatically by the Group model.
    # ------------------------------------------------------------------
    await repo.upsert_group(
        session,
        group_id=chat_id,
        title=chat.title or str(chat_id),
        owner_id=owner_id,
        username=chat.username,
    )
    log.info("group_saved: chat_id=%s title=%r owner=%s", chat_id, chat.title, owner_id)

    await repo.add_log(
        session,
        group_id=chat_id,
        event_type="bot_added",
        actor_id=added_by_user_id,
        details=f"Bot added to group '{chat.title}'",
    )

    # ------------------------------------------------------------------
    # Sync every known Telegram admin (creator + administrators) into the
    # `admins` table so the panel recognises ALL of them immediately, not
    # only the Telegram "creator". Never fatal — logged and skipped on error.
    # ------------------------------------------------------------------
    for a in admin_users:
        try:
            await repo.add_admin(
                session,
                group_id=chat_id,
                user_id=a.user.id,
                added_by=added_by_user_id,
            )
            log.info("admin_synced: chat_id=%s user_id=%s status=%s", chat_id, a.user.id, a.status)
        except Exception as exc:
            log.warning("admin_synced: failed for chat_id=%s user_id=%s: %s", chat_id, a.user.id, exc)

    if added_by_user_id and added_by_user_id != owner_id:
        # Whoever performed the add/promote action can always manage the
        # group too, even if Telegram doesn't list them as an admin yet
        # (e.g. they added the bot then a different admin promoted it).
        try:
            await repo.add_admin(session, group_id=chat_id, user_id=added_by_user_id, added_by=added_by_user_id)
            log.info("admin_synced: chat_id=%s user_id=%s (inviter fallback)", chat_id, added_by_user_id)
        except Exception as exc:
            log.warning("admin_synced: inviter fallback failed for chat_id=%s user_id=%s: %s",
                       chat_id, added_by_user_id, exc)

    log.info("group_registered: chat_id=%s title=%r owner=%s admins_synced=%d",
             chat_id, chat.title, owner_id, len(admin_users))


async def deregister_group(session: AsyncSession, chat_id: int) -> None:
    """Mark the group inactive when the bot is removed."""
    await repo.deactivate_group(session, chat_id)
    log.info("Group deactivated: %s", chat_id)


async def register_channel(session: AsyncSession, bot: Bot, channel_id: int) -> None:
    """Upsert a channel record when the bot gains admin access."""
    try:
        chat = await bot.get_chat(channel_id)
    except TelegramBadRequest as exc:
        log.error("Could not fetch channel %s: %s", channel_id, exc)
        return

    owner_id: int | None = None
    try:
        admins = await bot.get_chat_administrators(channel_id)
        for a in admins:
            if a.status == "creator":
                owner_id = a.user.id
                break
    except TelegramBadRequest:
        pass

    await repo.upsert_channel(
        session,
        channel_id=channel_id,
        title=chat.title or str(channel_id),
        username=chat.username,
        owner_id=owner_id,
    )
    log.info("Channel registered: %s (%s)", chat.title, channel_id)
