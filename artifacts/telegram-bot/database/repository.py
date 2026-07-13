"""
Data-access layer (repository pattern) — Version 2.
All DB reads and writes go through these functions.
Handlers and services must NOT build ORM queries directly.

Future: caching layer (Redis), pagination helpers, bulk-insert optimisations.
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Optional

from sqlalchemy import select, update, delete
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import (
    Admin,
    Channel,
    Filter,
    FILTER_TYPES,
    Group,
    GroupSettings,
    Log,
    Statistic,
    User,
    Warning,
    WarningHistory,
)
from utils.logger import get_logger

log = get_logger(__name__)


# ============================================================
# Users
# ============================================================

async def upsert_user(session: AsyncSession, *, user_id: int, first_name: str,
                      last_name: str | None = None, username: str | None = None,
                      is_bot: bool = False) -> User:
    stmt = pg_insert(User).values(
        user_id=user_id,
        first_name=first_name,
        last_name=last_name,
        username=username,
        is_bot=is_bot,
    ).on_conflict_do_update(
        index_elements=["user_id"],
        set_=dict(first_name=first_name, last_name=last_name,
                  username=username, updated_at=datetime.now(timezone.utc)),
    )
    await session.execute(stmt)
    await session.commit()
    return await session.get(User, user_id)


async def get_user(session: AsyncSession, user_id: int) -> User | None:
    return await session.get(User, user_id)


# ============================================================
# Groups
# ============================================================

async def upsert_group(session: AsyncSession, *, group_id: int, title: str,
                       owner_id: int | None = None,
                       username: str | None = None) -> Group:
    stmt = pg_insert(Group).values(
        group_id=group_id,
        title=title,
        owner_id=owner_id,
        username=username,
        is_active=True,
    ).on_conflict_do_update(
        index_elements=["group_id"],
        set_=dict(title=title, owner_id=owner_id, username=username,
                  is_active=True, updated_at=datetime.now(timezone.utc)),
    )
    await session.execute(stmt)
    await session.commit()
    group = await session.get(Group, group_id)

    await _ensure_group_settings(session, group_id)
    await _ensure_group_filters(session, group_id)
    return group


async def get_group(session: AsyncSession, group_id: int) -> Group | None:
    return await session.get(Group, group_id)


async def get_groups_for_user(session: AsyncSession, user_id: int) -> list[Group]:
    """Return all active groups where user_id is owner or a registered admin."""
    owned = (await session.execute(
        select(Group).where(Group.owner_id == user_id, Group.is_active == True)
    )).scalars().all()

    admin_group_ids = (await session.execute(
        select(Admin.group_id).where(Admin.user_id == user_id)
    )).scalars().all()

    admin_groups: list[Group] = []
    if admin_group_ids:
        admin_groups = (await session.execute(
            select(Group).where(Group.group_id.in_(admin_group_ids),
                                Group.is_active == True)
        )).scalars().all()

    seen = {g.group_id for g in owned}
    result = list(owned)
    for g in admin_groups:
        if g.group_id not in seen:
            result.append(g)
            seen.add(g.group_id)
    return result


async def deactivate_group(session: AsyncSession, group_id: int) -> None:
    await session.execute(
        update(Group).where(Group.group_id == group_id).values(is_active=False)
    )
    await session.commit()


# ============================================================
# Channels
# ============================================================

async def upsert_channel(session: AsyncSession, *, channel_id: int, title: str,
                          username: str | None = None,
                          owner_id: int | None = None) -> Channel:
    stmt = pg_insert(Channel).values(
        channel_id=channel_id,
        title=title,
        username=username,
        owner_id=owner_id,
        is_active=True,
    ).on_conflict_do_update(
        index_elements=["channel_id"],
        set_=dict(title=title, username=username, owner_id=owner_id, is_active=True),
    )
    await session.execute(stmt)
    await session.commit()
    return await session.get(Channel, channel_id)


async def get_channel(session: AsyncSession, channel_id: int) -> Channel | None:
    return await session.get(Channel, channel_id)


async def get_all_channels(session: AsyncSession) -> list[Channel]:
    result = await session.execute(
        select(Channel).where(Channel.is_active == True)
    )
    return result.scalars().all()


# ============================================================
# Group Settings
# ============================================================

async def _ensure_group_settings(session: AsyncSession, group_id: int) -> None:
    existing = await session.get(GroupSettings, group_id)
    if not existing:
        session.add(GroupSettings(group_id=group_id))
        await session.commit()


async def get_settings(session: AsyncSession, group_id: int) -> GroupSettings | None:
    return await session.get(GroupSettings, group_id)


async def update_settings(session: AsyncSession, group_id: int, **kwargs) -> None:
    await session.execute(
        update(GroupSettings).where(GroupSettings.group_id == group_id).values(**kwargs)
    )
    await session.commit()


# ============================================================
# Filters
# ============================================================

async def _ensure_group_filters(session: AsyncSession, group_id: int) -> None:
    """Insert default (disabled) filter rows for any missing filter types."""
    existing_types = (await session.execute(
        select(Filter.filter_type).where(Filter.group_id == group_id)
    )).scalars().all()

    missing = [ft for ft in FILTER_TYPES if ft not in existing_types]
    for ft in missing:
        session.add(Filter(group_id=group_id, filter_type=ft, enabled=False, action="delete"))
    if missing:
        await session.commit()


async def get_filters(session: AsyncSession, group_id: int) -> list[Filter]:
    result = await session.execute(
        select(Filter).where(Filter.group_id == group_id).order_by(Filter.filter_type)
    )
    return result.scalars().all()


async def get_filter(session: AsyncSession, group_id: int, filter_type: str) -> Filter | None:
    result = await session.execute(
        select(Filter).where(Filter.group_id == group_id, Filter.filter_type == filter_type)
    )
    return result.scalar_one_or_none()


async def update_filter(session: AsyncSession, group_id: int, filter_type: str, **kwargs) -> None:
    await session.execute(
        update(Filter)
        .where(Filter.group_id == group_id, Filter.filter_type == filter_type)
        .values(**kwargs)
    )
    await session.commit()


# ============================================================
# Admins
# ============================================================

async def add_admin(session: AsyncSession, *, group_id: int, user_id: int,
                    added_by: int | None = None, **perms) -> Admin:
    stmt = pg_insert(Admin).values(
        group_id=group_id,
        user_id=user_id,
        added_by=added_by,
        **perms,
    ).on_conflict_do_update(
        index_elements=["group_id", "user_id"],
        set_=dict(added_by=added_by, **perms),
    )
    await session.execute(stmt)
    await session.commit()
    result = await session.execute(
        select(Admin).where(Admin.group_id == group_id, Admin.user_id == user_id)
    )
    return result.scalar_one()


async def remove_admin(session: AsyncSession, group_id: int, user_id: int) -> None:
    await session.execute(
        delete(Admin).where(Admin.group_id == group_id, Admin.user_id == user_id)
    )
    await session.commit()


async def get_admins(session: AsyncSession, group_id: int) -> list[Admin]:
    result = await session.execute(
        select(Admin).where(Admin.group_id == group_id)
    )
    return result.scalars().all()


async def is_admin_in_db(session: AsyncSession, group_id: int, user_id: int) -> bool:
    result = await session.execute(
        select(Admin.id).where(Admin.group_id == group_id, Admin.user_id == user_id)
    )
    return result.scalar_one_or_none() is not None


# ============================================================
# Warnings  (counter row)
# ============================================================

async def get_warnings(session: AsyncSession, group_id: int, user_id: int) -> Warning | None:
    result = await session.execute(
        select(Warning).where(Warning.group_id == group_id, Warning.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def add_warning(session: AsyncSession, group_id: int, user_id: int,
                      reason: str | None = None,
                      actor_id: int | None = None) -> int:
    """Increment warning counter, record history, return the new count."""
    existing = await get_warnings(session, group_id, user_id)
    now = datetime.now(timezone.utc)

    if existing:
        new_count = existing.count + 1
        await session.execute(
            update(Warning)
            .where(Warning.group_id == group_id, Warning.user_id == user_id)
            .values(count=new_count, last_reason=reason, last_warned_at=now)
        )
    else:
        new_count = 1
        session.add(Warning(group_id=group_id, user_id=user_id, count=1,
                            last_reason=reason, last_warned_at=now))

    # V2: always record an individual history entry
    session.add(WarningHistory(
        group_id=group_id,
        user_id=user_id,
        actor_id=actor_id,
        reason=reason,
        count_at_time=new_count,
        created_at=now,
    ))

    await session.commit()
    return new_count


async def reset_warnings(session: AsyncSession, group_id: int, user_id: int) -> None:
    await session.execute(
        update(Warning)
        .where(Warning.group_id == group_id, Warning.user_id == user_id)
        .values(count=0, last_reason=None, last_warned_at=None)
    )
    await session.commit()


async def get_warning_history(session: AsyncSession, group_id: int, user_id: int,
                               limit: int = 10) -> list[WarningHistory]:
    """Return the most recent warning history entries for a user in a group."""
    result = await session.execute(
        select(WarningHistory)
        .where(WarningHistory.group_id == group_id, WarningHistory.user_id == user_id)
        .order_by(WarningHistory.created_at.desc())
        .limit(limit)
    )
    return result.scalars().all()


# ============================================================
# Logs
# ============================================================

async def add_log(session: AsyncSession, *, group_id: int, event_type: str,
                  actor_id: int | None = None, target_id: int | None = None,
                  details: str | None = None) -> Log:
    log_entry = Log(group_id=group_id, event_type=event_type,
                    actor_id=actor_id, target_id=target_id, details=details)
    session.add(log_entry)
    await session.commit()
    return log_entry


async def get_recent_logs(session: AsyncSession, group_id: int, limit: int = 20) -> list[Log]:
    result = await session.execute(
        select(Log)
        .where(Log.group_id == group_id)
        .order_by(Log.created_at.desc())
        .limit(limit)
    )
    return result.scalars().all()


# ============================================================
# Statistics
# ============================================================

def _today_str() -> str:
    return date.today().isoformat()


async def increment_stat(session: AsyncSession, group_id: int, field: str,
                          amount: int = 1) -> None:
    today = _today_str()
    stmt = pg_insert(Statistic).values(
        group_id=group_id, date=today
    ).on_conflict_do_nothing()
    await session.execute(stmt)

    await session.execute(
        update(Statistic)
        .where(Statistic.group_id == group_id, Statistic.date == today)
        .values(**{field: getattr(Statistic, field) + amount})
    )
    await session.commit()


async def get_stats(session: AsyncSession, group_id: int, days: int = 7) -> list[Statistic]:
    result = await session.execute(
        select(Statistic)
        .where(Statistic.group_id == group_id)
        .order_by(Statistic.date.desc())
        .limit(days)
    )
    return result.scalars().all()


async def set_total_members(session: AsyncSession, group_id: int, count: int) -> None:
    today = _today_str()
    stmt = pg_insert(Statistic).values(
        group_id=group_id, date=today, total_members=count
    ).on_conflict_do_update(
        index_elements=["group_id", "date"],
        set_=dict(total_members=count),
    )
    await session.execute(stmt)
    await session.commit()
