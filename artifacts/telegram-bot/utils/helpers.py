"""
Utility helpers used across the bot.
Future: i18n translations, template rendering, rate-limit decorators.
"""

import re
import unicodedata
from datetime import datetime, timedelta, timezone

import pytz

# ---------------------------------------------------------------------------
# Text helpers
# ---------------------------------------------------------------------------

# Simple emoji detection via unicode category
_EMOJI_RE = re.compile(
    "[\U0001F600-\U0001F64F"
    "\U0001F300-\U0001F5FF"
    "\U0001F680-\U0001F6FF"
    "\U0001F1E0-\U0001F1FF"
    "\U00002702-\U000027B0"
    "\U000024C2-\U0001F251"
    "]+",
    flags=re.UNICODE,
)

_TELEGRAM_LINK_RE = re.compile(
    r"(https?://)?(t\.me|telegram\.me|telegram\.dog)/\S+",
    flags=re.IGNORECASE,
)

_EXTERNAL_LINK_RE = re.compile(
    r"https?://[^\s]+",
    flags=re.IGNORECASE,
)

_REPEATED_CHARS_RE = re.compile(r"(.)\1{7,}")  # 8+ same character in a row


def count_emojis(text: str) -> int:
    """Count individual emoji characters in *text*."""
    matches = _EMOJI_RE.findall(text)
    return sum(len(m) for m in matches)


def has_telegram_link(text: str) -> bool:
    return bool(_TELEGRAM_LINK_RE.search(text))


def has_external_link(text: str) -> bool:
    return bool(_EXTERNAL_LINK_RE.search(text))


def has_repeated_chars(text: str) -> bool:
    return bool(_REPEATED_CHARS_RE.search(text))


def has_advertisement(text: str) -> bool:
    """Heuristic: inline username mentions that look promotional."""
    return bool(re.search(r"@[A-Za-z0-9_]{5,}", text))


# ---------------------------------------------------------------------------
# Time helpers
# ---------------------------------------------------------------------------

def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def format_duration(seconds: int) -> str:
    """Return a human-readable duration string."""
    if seconds < 60:
        return f"{seconds}s"
    if seconds < 3600:
        return f"{seconds // 60}m"
    if seconds < 86400:
        return f"{seconds // 3600}h"
    return f"{seconds // 86400}d"


def parse_duration(text: str) -> int | None:
    """
    Parse strings like '30m', '2h', '1d', '60s' into seconds.
    Returns None if unparseable.
    """
    m = re.fullmatch(r"(\d+)([smhd]?)", text.strip().lower())
    if not m:
        return None
    value, unit = int(m.group(1)), m.group(2) or "s"
    multipliers = {"s": 1, "m": 60, "h": 3600, "d": 86400}
    return value * multipliers[unit]


# ---------------------------------------------------------------------------
# Telegram-specific helpers
# ---------------------------------------------------------------------------

def mention_html(user_id: int, name: str) -> str:
    """Return an HTML mention link for a user."""
    safe = name.replace("<", "&lt;").replace(">", "&gt;").replace("&", "&amp;")
    return f'<a href="tg://user?id={user_id}">{safe}</a>'


def escape_html(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def format_welcome(template: str, *, first_name: str, username: str | None, group_name: str) -> str:
    """Substitute placeholders in a welcome message template."""
    uname = f"@{username}" if username else first_name
    return (
        template
        .replace("{first_name}", escape_html(first_name))
        .replace("{username}", escape_html(uname))
        .replace("{group_name}", escape_html(group_name))
    )
