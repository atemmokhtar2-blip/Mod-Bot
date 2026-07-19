"""
Configuration module.
Loads all settings from environment variables.
Future: add per-environment config, feature flags, plugin system config.
"""

import os
import re
from dataclasses import dataclass, field


@dataclass
class Config:
    """Central configuration object."""

    # --- Telegram ---
    bot_token: str

    # --- Database ---
    database_url: str  # asyncpg-compatible URL

    # --- Logging ---
    log_level: str = "INFO"

    # --- Moderation defaults ---
    default_warning_limit: int = 3
    default_mute_duration: int = 3600  # seconds (1 hour)

    # --- Flood detection ---
    flood_message_count: int = 5       # messages
    flood_time_window: int = 10        # seconds

    # --- Duplicate detection ---
    duplicate_time_window: int = 30    # seconds

    # --- Filter thresholds ---
    max_emoji_count: int = 10
    max_repeated_chars: int = 8
    max_message_length: int = 2000

    # --- Rate limiting ---
    max_warnings_per_hour: int = 10    # per bot globally (anti-spam guard)

    # --- V6: Bot-owner IDs (global resource management, e.g. AI API keys) ---
    bot_owner_ids: frozenset[int] = field(default_factory=frozenset)


def _parse_owner_ids(raw: str) -> frozenset[int]:
    ids: set[int] = set()
    for part in raw.split(","):
        part = part.strip()
        if part.isdigit():
            ids.add(int(part))
    return frozenset(ids)


def _adapt_db_url(url: str) -> str:
    """
    Convert postgresql:// → postgresql+asyncpg:// for async SQLAlchemy.
    Also strips ?sslmode=... because asyncpg does not accept that query param;
    SSL is configured separately via connect_args in the engine.
    """
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+asyncpg://", 1)

    # Remove sslmode param (asyncpg rejects it as an unknown keyword)
    url = re.sub(r"[?&]sslmode=[^&]*", "", url)
    # Clean up dangling ? or &
    url = re.sub(r"\?$", "", url)
    url = re.sub(r"&$", "", url)
    return url


def load_config() -> Config:
    """Read and validate all required environment variables.

    Raises EnvironmentError immediately on any missing required variable so
    the operator sees a precise, actionable message at startup rather than a
    cryptic AttributeError later.
    """
    missing: list[str] = []

    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        missing.append("TELEGRAM_BOT_TOKEN")

    db_url = os.environ.get("DATABASE_URL", "").strip()
    if not db_url:
        missing.append("DATABASE_URL")

    if missing:
        raise EnvironmentError(
            "Required environment variable(s) not set: "
            + ", ".join(missing)
            + ". Set them and restart the bot."
        )

    return Config(
        bot_token=token,
        database_url=_adapt_db_url(db_url),
        log_level=os.environ.get("LOG_LEVEL", "INFO"),
        bot_owner_ids=_parse_owner_ids(os.environ.get("BOT_OWNER_IDS", "")),
    )


def check_optional_env() -> None:
    """Log warnings for important-but-optional environment variables.

    Call this once after setup_logging() is initialised so the warnings
    appear in the structured log rather than on bare stderr.
    """
    import logging
    _log = logging.getLogger(__name__)

    _GEN_CMD = (
        'python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"'
    )

    enc_key = os.environ.get("AI_KEY_ENCRYPTION_KEY", "").strip()
    if not enc_key:
        _log.warning(
            "AI_KEY_ENCRYPTION_KEY is not set — Gemini key encryption is disabled. "
            "Generate a key with: %s "
            "and add it as a secret before storing any API keys.",
            _GEN_CMD,
        )
    else:
        # Validate format without importing the full crypto module (avoid lru_cache side-effects)
        key_len = len(enc_key)
        if key_len == 43:
            _log.info(
                "AI_KEY_ENCRYPTION_KEY: 43-char key detected — auto-padding trailing '=' "
                "to form a valid 44-char Fernet key. Encryption is operational."
            )
        elif key_len != 44:
            _log.error(
                "AI_KEY_ENCRYPTION_KEY is %d characters — expected 44 (32 urlsafe-base64 bytes). "
                "This key is INVALID and will prevent Gemini key storage from working. "
                "Generate a correct key with: %s",
                key_len, _GEN_CMD,
            )
        else:
            _log.info("AI_KEY_ENCRYPTION_KEY is set and correctly sized (44 chars).")

    if not os.environ.get("WEBHOOK_SECRET"):
        _log.warning(
            "WEBHOOK_SECRET is not set — the webhook endpoint will accept requests from any source. "
            "Set this to a random string (shared between Telegram's setWebhook call and Vercel) "
            "before going to production."
        )

    if not os.environ.get("BOT_OWNER_IDS"):
        _log.warning(
            "BOT_OWNER_IDS is not set — no bot owner is configured. "
            "AI key management (/addaikey, /listaikeys, the inline wizard) will be inaccessible. "
            "Set this to your Telegram numeric user ID (comma-separated for multiple owners)."
        )
