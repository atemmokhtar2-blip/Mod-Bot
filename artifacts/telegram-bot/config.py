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
    """Read and validate all required environment variables."""
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        raise EnvironmentError("TELEGRAM_BOT_TOKEN is not set.")

    db_url = os.environ.get("DATABASE_URL", "")
    if not db_url:
        raise EnvironmentError("DATABASE_URL is not set.")

    return Config(
        bot_token=token,
        database_url=_adapt_db_url(db_url),
        log_level=os.environ.get("LOG_LEVEL", "INFO"),
        bot_owner_ids=_parse_owner_ids(os.environ.get("BOT_OWNER_IDS", "")),
    )
