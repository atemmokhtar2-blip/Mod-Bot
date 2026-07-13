"""
SQLAlchemy ORM models — Version 2.

Tables
------
users           – Telegram users the bot has encountered
groups          – Registered Telegram groups/supergroups
channels        – Registered Telegram channels
admins          – Per-group admin grants
group_settings  – Per-group configuration knobs
filters         – Per-group moderation filter configuration
warnings        – Accumulated warning counters per member per group
warning_history – Individual warning events (V2: full history)
logs            – Audit log of moderation events
statistics      – Daily counters per group

Future: plugin_data (JSONB), premium_subscriptions, scheduled_posts,
        ai_moderation_decisions.
"""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


# ---------------------------------------------------------------------------
# users
# ---------------------------------------------------------------------------

class User(Base):
    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    username: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    first_name: Mapped[str] = mapped_column(String(128))
    last_name: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    is_bot: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow
    )

    def display_name(self) -> str:
        parts = [self.first_name]
        if self.last_name:
            parts.append(self.last_name)
        return " ".join(parts)


# ---------------------------------------------------------------------------
# groups
# ---------------------------------------------------------------------------

class Group(Base):
    __tablename__ = "groups"

    group_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    title: Mapped[str] = mapped_column(String(256))
    owner_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    username: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow
    )

    settings: Mapped[Optional["GroupSettings"]] = relationship(
        "GroupSettings", back_populates="group", uselist=False, cascade="all, delete-orphan"
    )
    filters: Mapped[list["Filter"]] = relationship(
        "Filter", back_populates="group", cascade="all, delete-orphan"
    )
    admins: Mapped[list["Admin"]] = relationship(
        "Admin", back_populates="group", cascade="all, delete-orphan"
    )
    logs: Mapped[list["Log"]] = relationship(
        "Log", back_populates="group", cascade="all, delete-orphan"
    )


# ---------------------------------------------------------------------------
# channels
# ---------------------------------------------------------------------------

class Channel(Base):
    __tablename__ = "channels"

    channel_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    title: Mapped[str] = mapped_column(String(256))
    username: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    owner_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow
    )


# ---------------------------------------------------------------------------
# admins (per-group grants stored by the bot)
# ---------------------------------------------------------------------------

class Admin(Base):
    __tablename__ = "admins"
    __table_args__ = (
        UniqueConstraint("group_id", "user_id"),
        Index("ix_admins_group_user", "group_id", "user_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    group_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("groups.group_id", ondelete="CASCADE")
    )
    user_id: Mapped[int] = mapped_column(BigInteger)
    can_ban: Mapped[bool] = mapped_column(Boolean, default=True)
    can_mute: Mapped[bool] = mapped_column(Boolean, default=True)
    can_delete: Mapped[bool] = mapped_column(Boolean, default=True)
    can_change_settings: Mapped[bool] = mapped_column(Boolean, default=False)
    added_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    added_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow
    )

    group: Mapped["Group"] = relationship("Group", back_populates="admins")


# ---------------------------------------------------------------------------
# group_settings
# ---------------------------------------------------------------------------

class GroupSettings(Base):
    __tablename__ = "group_settings"

    group_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("groups.group_id", ondelete="CASCADE"), primary_key=True
    )
    welcome_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    welcome_text: Mapped[str] = mapped_column(
        Text,
        default="أهلاً وسهلاً {first_name}! 👋 يرجى قراءة قواعد المجموعة.",
    )
    warning_limit: Mapped[int] = mapped_column(Integer, default=3)
    # Action after warning_limit reached: mute | kick | ban
    auto_punishment: Mapped[str] = mapped_column(String(16), default="mute")
    mute_duration: Mapped[int] = mapped_column(Integer, default=3600)
    log_events: Mapped[bool] = mapped_column(Boolean, default=True)
    language: Mapped[str] = mapped_column(String(8), default="ar")

    group: Mapped["Group"] = relationship("Group", back_populates="settings")


# ---------------------------------------------------------------------------
# filters
# ---------------------------------------------------------------------------

FILTER_TYPES = [
    "bad_words",
    "insults",
    "spam",
    "flood",
    "duplicate_messages",
    "advertisement",
    "telegram_links",
    "external_links",
    "excessive_emojis",
    "repeated_chars",
    "long_messages",
]

FILTER_ACTIONS = ["ignore", "delete", "warn", "mute", "kick", "ban"]


class Filter(Base):
    __tablename__ = "filters"
    __table_args__ = (
        UniqueConstraint("group_id", "filter_type"),
        Index("ix_filters_group_type", "group_id", "filter_type"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    group_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("groups.group_id", ondelete="CASCADE")
    )
    filter_type: Mapped[str] = mapped_column(String(32))
    enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    # Action to take when this filter triggers
    action: Mapped[str] = mapped_column(String(16), default="delete")
    # Optional extra config (e.g. comma-separated bad words)
    extra: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    group: Mapped["Group"] = relationship("Group", back_populates="filters")


# ---------------------------------------------------------------------------
# warnings  (counter row per member per group)
# ---------------------------------------------------------------------------

class Warning(Base):
    __tablename__ = "warnings"
    __table_args__ = (
        UniqueConstraint("group_id", "user_id"),
        Index("ix_warnings_group_user", "group_id", "user_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    group_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("groups.group_id", ondelete="CASCADE")
    )
    user_id: Mapped[int] = mapped_column(BigInteger)
    count: Mapped[int] = mapped_column(Integer, default=0)
    last_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    last_warned_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


# ---------------------------------------------------------------------------
# warning_history  (V2: full per-event log for the warning system)
# ---------------------------------------------------------------------------

class WarningHistory(Base):
    """Each row is one warning event — allows showing full history."""
    __tablename__ = "warning_history"
    __table_args__ = (
        Index("ix_warn_hist_group_user", "group_id", "user_id"),
        Index("ix_warn_hist_created", "created_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    group_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("groups.group_id", ondelete="CASCADE")
    )
    user_id: Mapped[int] = mapped_column(BigInteger)
    actor_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    count_at_time: Mapped[int] = mapped_column(Integer, default=1)  # counter value when issued
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow
    )


# ---------------------------------------------------------------------------
# logs
# ---------------------------------------------------------------------------

LOG_EVENTS = [
    "user_joined",
    "user_left",
    "user_banned",
    "user_unbanned",
    "user_muted",
    "user_unmuted",
    "user_warned",
    "message_deleted",
    "message_pinned",
    "message_unpinned",
    "settings_changed",
    "filter_triggered",
    "bot_added",
    "bot_removed",
]


class Log(Base):
    __tablename__ = "logs"
    __table_args__ = (
        Index("ix_logs_group_created", "group_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    group_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("groups.group_id", ondelete="CASCADE")
    )
    event_type: Mapped[str] = mapped_column(String(32))
    actor_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    target_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow
    )

    group: Mapped["Group"] = relationship("Group", back_populates="logs")


# ---------------------------------------------------------------------------
# statistics
# ---------------------------------------------------------------------------

class Statistic(Base):
    __tablename__ = "statistics"
    __table_args__ = (
        UniqueConstraint("group_id", "date"),
        Index("ix_statistics_group_date", "group_id", "date"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    group_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("groups.group_id", ondelete="CASCADE")
    )
    date: Mapped[str] = mapped_column(String(10))   # YYYY-MM-DD
    total_members: Mapped[int] = mapped_column(Integer, default=0)
    messages_today: Mapped[int] = mapped_column(Integer, default=0)
    deleted_messages: Mapped[int] = mapped_column(Integer, default=0)
    muted_members: Mapped[int] = mapped_column(Integer, default=0)
    banned_members: Mapped[int] = mapped_column(Integer, default=0)
    warned_members: Mapped[int] = mapped_column(Integer, default=0)  # V2: track warnings too
