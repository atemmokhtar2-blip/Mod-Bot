"""
Database connection and session management.
Uses SQLAlchemy 2.x async engine + session factory.
V4: Extended migrations for new GroupSettings columns.
"""

import os

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from config import load_config
from utils.logger import get_logger

log = get_logger(__name__)

_config = load_config()

# SSL control:
#   DATABASE_SSL=false  → disable SSL (Replit internal Postgres, local dev)
#   DATABASE_SSL=true   → enable SSL  (Zeabur, Supabase, Railway, etc.)
#   unset               → disable SSL (safe default for most VPS/internal DBs)
_ssl_env = os.environ.get("DATABASE_SSL", "false").strip().lower()
_ssl = True if _ssl_env == "true" else None

engine: AsyncEngine = create_async_engine(
    _config.database_url,
    echo=False,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    connect_args={"ssl": _ssl},
)

async_session: async_sessionmaker[AsyncSession] = async_sessionmaker(
    engine,
    expire_on_commit=False,
    class_=AsyncSession,
)


async def init_db() -> None:
    """Create all tables that do not yet exist, then apply safe column migrations."""
    from database.models import Base  # avoid circular import at module level

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # All migrations use ADD COLUMN IF NOT EXISTS — idempotent on every restart.
    migrations = [
        # V3 migrations
        "ALTER TABLE group_settings ADD COLUMN IF NOT EXISTS auto_protect_enabled BOOLEAN DEFAULT FALSE",
        "ALTER TABLE statistics ADD COLUMN IF NOT EXISTS warned_members INTEGER DEFAULT 0",

        # V4: Goodbye message
        "ALTER TABLE group_settings ADD COLUMN IF NOT EXISTS goodbye_enabled BOOLEAN DEFAULT FALSE",
        "ALTER TABLE group_settings ADD COLUMN IF NOT EXISTS goodbye_text TEXT DEFAULT 'وداعاً {first_name}! 👋 نتمنى لك التوفيق.'",

        # V4: Media locks
        "ALTER TABLE group_settings ADD COLUMN IF NOT EXISTS lock_photos BOOLEAN DEFAULT FALSE",
        "ALTER TABLE group_settings ADD COLUMN IF NOT EXISTS lock_video BOOLEAN DEFAULT FALSE",
        "ALTER TABLE group_settings ADD COLUMN IF NOT EXISTS lock_audio BOOLEAN DEFAULT FALSE",
        "ALTER TABLE group_settings ADD COLUMN IF NOT EXISTS lock_documents BOOLEAN DEFAULT FALSE",
        "ALTER TABLE group_settings ADD COLUMN IF NOT EXISTS lock_stickers BOOLEAN DEFAULT FALSE",
        "ALTER TABLE group_settings ADD COLUMN IF NOT EXISTS lock_gifs BOOLEAN DEFAULT FALSE",
        "ALTER TABLE group_settings ADD COLUMN IF NOT EXISTS lock_polls BOOLEAN DEFAULT FALSE",
        "ALTER TABLE group_settings ADD COLUMN IF NOT EXISTS lock_locations BOOLEAN DEFAULT FALSE",
        "ALTER TABLE group_settings ADD COLUMN IF NOT EXISTS lock_voice BOOLEAN DEFAULT FALSE",

        # V4: Admin permission defaults
        "ALTER TABLE group_settings ADD COLUMN IF NOT EXISTS perm_delete BOOLEAN DEFAULT TRUE",
        "ALTER TABLE group_settings ADD COLUMN IF NOT EXISTS perm_ban BOOLEAN DEFAULT TRUE",
        "ALTER TABLE group_settings ADD COLUMN IF NOT EXISTS perm_unban BOOLEAN DEFAULT TRUE",
        "ALTER TABLE group_settings ADD COLUMN IF NOT EXISTS perm_mute BOOLEAN DEFAULT TRUE",
        "ALTER TABLE group_settings ADD COLUMN IF NOT EXISTS perm_unmute BOOLEAN DEFAULT TRUE",
        "ALTER TABLE group_settings ADD COLUMN IF NOT EXISTS perm_pin BOOLEAN DEFAULT TRUE",
        "ALTER TABLE group_settings ADD COLUMN IF NOT EXISTS perm_unpin BOOLEAN DEFAULT TRUE",
        "ALTER TABLE group_settings ADD COLUMN IF NOT EXISTS perm_warn BOOLEAN DEFAULT TRUE",
        "ALTER TABLE group_settings ADD COLUMN IF NOT EXISTS perm_edit_settings BOOLEAN DEFAULT FALSE",
        "ALTER TABLE group_settings ADD COLUMN IF NOT EXISTS perm_manage_admins BOOLEAN DEFAULT FALSE",

        # V4.1: Custom profanity word list
        """
        CREATE TABLE IF NOT EXISTS custom_words (
            id               SERIAL PRIMARY KEY,
            group_id         BIGINT NOT NULL REFERENCES groups(group_id) ON DELETE CASCADE,
            word_original    VARCHAR(256) NOT NULL,
            word_normalized  VARCHAR(256) NOT NULL,
            added_by         BIGINT,
            added_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            CONSTRAINT uq_custom_words_group_norm UNIQUE (group_id, word_normalized)
        )
        """,
        "CREATE INDEX IF NOT EXISTS ix_custom_words_group ON custom_words (group_id)",

        # V5: Telegram Stars donations
        """
        CREATE TABLE IF NOT EXISTS donations (
            id                   SERIAL PRIMARY KEY,
            user_id              BIGINT NOT NULL,
            amount               INTEGER NOT NULL,
            currency             VARCHAR(8) NOT NULL DEFAULT 'XTR',
            payload              VARCHAR(128) NOT NULL,
            status               VARCHAR(16) NOT NULL DEFAULT 'pending',
            telegram_charge_id   VARCHAR(128),
            provider_charge_id   VARCHAR(128),
            created_at           TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """,
        "CREATE INDEX IF NOT EXISTS ix_donations_user ON donations (user_id)",
        "CREATE INDEX IF NOT EXISTS ix_donations_created ON donations (created_at)",

        # V6: AI Protection settings (per-group)
        "ALTER TABLE group_settings ADD COLUMN IF NOT EXISTS ai_enabled BOOLEAN DEFAULT FALSE",
        "ALTER TABLE group_settings ADD COLUMN IF NOT EXISTS ai_analyze_messages BOOLEAN DEFAULT TRUE",
        "ALTER TABLE group_settings ADD COLUMN IF NOT EXISTS ai_analyze_images BOOLEAN DEFAULT TRUE",
        "ALTER TABLE group_settings ADD COLUMN IF NOT EXISTS ai_sensitivity VARCHAR(8) DEFAULT 'medium'",

        # V6: Gemini AI provider key manager (global, bot-owner managed)
        """
        CREATE TABLE IF NOT EXISTS ai_provider_keys (
            id               SERIAL PRIMARY KEY,
            provider         VARCHAR(32) NOT NULL DEFAULT 'gemini',
            label            VARCHAR(64),
            api_key          TEXT NOT NULL,
            enabled          BOOLEAN NOT NULL DEFAULT TRUE,
            added_by         BIGINT,
            added_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            usage_count      INTEGER NOT NULL DEFAULT 0,
            success_count    INTEGER NOT NULL DEFAULT 0,
            failure_count    INTEGER NOT NULL DEFAULT 0,
            last_used_at     TIMESTAMPTZ,
            last_success_at  TIMESTAMPTZ,
            last_failure_at  TIMESTAMPTZ,
            last_error       TEXT
        )
        """,
        "CREATE INDEX IF NOT EXISTS ix_ai_keys_provider_enabled ON ai_provider_keys (provider, enabled)",

        # V7: AI link analysis + multi-action support
        "ALTER TABLE group_settings ADD COLUMN IF NOT EXISTS ai_analyze_links BOOLEAN DEFAULT FALSE",
        "ALTER TABLE group_settings ADD COLUMN IF NOT EXISTS ai_action_delete BOOLEAN DEFAULT TRUE",
        "ALTER TABLE group_settings ADD COLUMN IF NOT EXISTS ai_action_warn BOOLEAN DEFAULT FALSE",
        "ALTER TABLE group_settings ADD COLUMN IF NOT EXISTS ai_action_mute BOOLEAN DEFAULT FALSE",
        "ALTER TABLE group_settings ADD COLUMN IF NOT EXISTS ai_action_ban BOOLEAN DEFAULT FALSE",

        # V7.1: encrypted Gemini keys — masked display value stored separately
        # so normal reads never need to decrypt the key.
        "ALTER TABLE ai_provider_keys ADD COLUMN IF NOT EXISTS key_mask VARCHAR(64)",
    ]

    async with engine.begin() as conn:
        for sql in migrations:
            try:
                await conn.execute(__import__("sqlalchemy").text(sql))
            except Exception as exc:
                log.warning("Migration skipped: %s", exc)

    await _encrypt_legacy_plaintext_keys()

    log.info("Database tables initialised (V7.1).")


async def _encrypt_legacy_plaintext_keys() -> None:
    """
    V7.1 one-time data migration: any Gemini key stored before encryption was
    introduced is still plaintext in `api_key`. Detect those rows (not a valid
    Fernet token) and encrypt them in place, backfilling `key_mask` too.
    Idempotent — rows that are already encrypted (and already have a mask)
    are left untouched, so this is safe to run on every boot.
    """
    from sqlalchemy import select, update
    from database.models import AIProviderKey
    from utils.crypto import EncryptionNotConfigured, encrypt_secret, is_encrypted, mask

    try:
        async with async_session() as session:
            rows = (await session.execute(select(AIProviderKey))).scalars().all()
            migrated = 0
            for row in rows:
                if row.key_mask and is_encrypted(row.api_key):
                    continue  # already migrated
                try:
                    plaintext = row.api_key
                    if is_encrypted(plaintext):
                        # Encrypted already but missing its mask (shouldn't
                        # normally happen) — we cannot recover the plaintext
                        # to mask it without the original value, so use a
                        # generic placeholder rather than ever decrypting
                        # just for display purposes.
                        new_mask = row.key_mask or "••••••••"
                        await session.execute(
                            update(AIProviderKey).where(AIProviderKey.id == row.id)
                            .values(key_mask=new_mask)
                        )
                    else:
                        new_mask = mask(plaintext)
                        encrypted = encrypt_secret(plaintext)
                        await session.execute(
                            update(AIProviderKey).where(AIProviderKey.id == row.id)
                            .values(api_key=encrypted, key_mask=new_mask)
                        )
                    migrated += 1
                except Exception as exc:
                    log.warning("Could not migrate legacy AI key id=%s: %s", row.id, exc)
            if migrated:
                await session.commit()
                log.info("Encrypted %d legacy Gemini key row(s) in place.", migrated)
    except EncryptionNotConfigured as exc:
        log.warning("Skipping legacy AI key encryption migration: %s", exc)
    except Exception as exc:
        log.warning("Legacy AI key encryption migration failed: %s", exc)
