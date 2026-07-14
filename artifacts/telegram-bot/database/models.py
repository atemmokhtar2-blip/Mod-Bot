"""
SQLAlchemy ORM models — Version 4 (Advanced Settings & Administration).

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

V4 additions
------------
GroupSettings: goodbye_enabled/text, media locks (9), admin permissions (10)
FILTER_TYPES: forwarded, mass_mention, hashtag (3 new)
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
# group_settings  — V4 expanded
# ---------------------------------------------------------------------------

class GroupSettings(Base):
    __tablename__ = "group_settings"

    group_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("groups.group_id", ondelete="CASCADE"), primary_key=True
    )

    # ── Welcome / Goodbye ────────────────────────────────────────────────────
    welcome_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    welcome_text: Mapped[str] = mapped_column(
        Text,
        default="أهلاً وسهلاً {first_name}! 👋 يرجى قراءة قواعد المجموعة.",
    )
    # V4
    goodbye_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    goodbye_text: Mapped[str] = mapped_column(
        Text,
        default="وداعاً {first_name}! 👋 نتمنى لك التوفيق.",
    )

    # ── Warnings / Punishment ────────────────────────────────────────────────
    warning_limit: Mapped[int] = mapped_column(Integer, default=3)
    # Action after warning_limit reached: mute | kick | ban
    auto_punishment: Mapped[str] = mapped_column(String(16), default="mute")
    mute_duration: Mapped[int] = mapped_column(Integer, default=3600)

    # ── Logging / Language ───────────────────────────────────────────────────
    log_events: Mapped[bool] = mapped_column(Boolean, default=True)
    language: Mapped[str] = mapped_column(String(8), default="ar")

    # ── Auto-protection master switch (V3) ───────────────────────────────────
    auto_protect_enabled: Mapped[bool] = mapped_column(Boolean, default=False)

    # ── Media locks (V4) — each locks that media type in the group ───────────
    lock_photos: Mapped[bool] = mapped_column(Boolean, default=False)
    lock_video: Mapped[bool] = mapped_column(Boolean, default=False)
    lock_audio: Mapped[bool] = mapped_column(Boolean, default=False)
    lock_documents: Mapped[bool] = mapped_column(Boolean, default=False)
    lock_stickers: Mapped[bool] = mapped_column(Boolean, default=False)
    lock_gifs: Mapped[bool] = mapped_column(Boolean, default=False)
    lock_polls: Mapped[bool] = mapped_column(Boolean, default=False)
    lock_locations: Mapped[bool] = mapped_column(Boolean, default=False)
    lock_voice: Mapped[bool] = mapped_column(Boolean, default=False)

    # ── Admin permission defaults (V4) — what bot-admins may do ─────────────
    perm_delete: Mapped[bool] = mapped_column(Boolean, default=True)
    perm_ban: Mapped[bool] = mapped_column(Boolean, default=True)
    perm_unban: Mapped[bool] = mapped_column(Boolean, default=True)
    perm_mute: Mapped[bool] = mapped_column(Boolean, default=True)
    perm_unmute: Mapped[bool] = mapped_column(Boolean, default=True)
    perm_pin: Mapped[bool] = mapped_column(Boolean, default=True)
    perm_unpin: Mapped[bool] = mapped_column(Boolean, default=True)
    perm_warn: Mapped[bool] = mapped_column(Boolean, default=True)
    perm_edit_settings: Mapped[bool] = mapped_column(Boolean, default=False)
    perm_manage_admins: Mapped[bool] = mapped_column(Boolean, default=False)

    # ── AI Protection (V6) — Gemini-powered moderation ──────────────────────
    ai_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    ai_analyze_messages: Mapped[bool] = mapped_column(Boolean, default=True)
    ai_analyze_images: Mapped[bool] = mapped_column(Boolean, default=True)
    # low | medium | high — maps to a confidence threshold in bot/ai/manager.py
    ai_sensitivity: Mapped[str] = mapped_column(String(8), default="medium")

    group: Mapped["Group"] = relationship("Group", back_populates="settings")


# ---------------------------------------------------------------------------
# filters  — V4 adds forwarded, mass_mention, hashtag
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
    # V4
    "forwarded",
    "mass_mention",
    "hashtag",
    # V6 — AI Protection (Gemini text/image classification)
    "ai_text",
    "ai_image",
]

AI_SENSITIVITIES = ["low", "medium", "high"]
# Confidence threshold (0-100) an AI verdict must reach before an action fires.
AI_SENSITIVITY_THRESHOLDS = {"low": 85, "medium": 65, "high": 45}

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
    count_at_time: Mapped[int] = mapped_column(Integer, default=1)
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
# ai_provider_keys — V6: Gemini API Key Manager (multi-provider ready)
# ---------------------------------------------------------------------------

AI_PROVIDERS = ["gemini"]  # extend when adding grok/openai/claude — no other schema change needed


class AIProviderKey(Base):
    """
    One row per API key registered by a bot owner. The key manager
    (bot/ai/key_manager.py) round-robins across enabled keys for a provider
    and silently skips/cools down keys that start failing.
    """
    __tablename__ = "ai_provider_keys"
    __table_args__ = (
        Index("ix_ai_keys_provider_enabled", "provider", "enabled"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    provider: Mapped[str] = mapped_column(String(32), default="gemini")
    label: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    api_key: Mapped[str] = mapped_column(Text)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    added_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    added_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    usage_count: Mapped[int] = mapped_column(Integer, default=0)
    success_count: Mapped[int] = mapped_column(Integer, default=0)
    failure_count: Mapped[int] = mapped_column(Integer, default=0)
    last_used_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_success_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_failure_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    def masked_key(self) -> str:
        k = self.api_key
        if len(k) <= 8:
            return "•" * max(len(k), 4)
        return f"{k[:4]}...{k[-4:]}"


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
    warned_members: Mapped[int] = mapped_column(Integer, default=0)


# ---------------------------------------------------------------------------
# custom_words  — V4.1: per-group custom profanity list
# ---------------------------------------------------------------------------

class CustomWord(Base):
    """
    One row per custom blocked word/phrase for a specific group.
    The engine stores both the raw original (for display) and the normalized
    form (for dedup checks so the same word added twice is caught early).
    """
    __tablename__ = "custom_words"
    __table_args__ = (
        UniqueConstraint("group_id", "word_normalized"),
        Index("ix_custom_words_group", "group_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    group_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("groups.group_id", ondelete="CASCADE")
    )
    word_original: Mapped[str] = mapped_column(String(256))
    word_normalized: Mapped[str] = mapped_column(String(256))
    added_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    added_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow
    )


# ---------------------------------------------------------------------------
# donations  — V5: Telegram Stars donations
# ---------------------------------------------------------------------------

DONATION_STATUSES = ["pending", "paid", "failed"]


class Donation(Base):
    """One row per Telegram Stars donation attempt/payment."""
    __tablename__ = "donations"
    __table_args__ = (
        Index("ix_donations_user", "user_id"),
        Index("ix_donations_created", "created_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger)
    amount: Mapped[int] = mapped_column(Integer)  # amount in Telegram Stars (XTR)
    currency: Mapped[str] = mapped_column(String(8), default="XTR")
    payload: Mapped[str] = mapped_column(String(128))
    status: Mapped[str] = mapped_column(String(16), default="pending")
    telegram_charge_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    provider_charge_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow
    )
