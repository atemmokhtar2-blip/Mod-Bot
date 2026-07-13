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

# Arabic diacritics (tashkeel)
_ARABIC_DIACRITICS_RE = re.compile(
    r"[\u0610-\u061A\u064B-\u065F\u06D6-\u06DC\u06DF-\u06E4\u06E7\u06E8\u06EA-\u06ED]"
)

# Arabic letter normalization map: variant forms → canonical form
_ARABIC_NORM_MAP = str.maketrans({
    "أ": "ا", "إ": "ا", "آ": "ا", "ٱ": "ا",  # alef variants → alef
    "ة": "ه",                                    # taa marbuta → haa
    "ى": "ي",                                    # alef maqsura → yaa
    "ؤ": "و",                                    # waw with hamza
    "ئ": "ي",                                    # yaa with hamza
})

# Symbols and punctuation to strip during normalization
_SYMBOL_RE = re.compile(r"[^\w\s\u0600-\u06FF]", re.UNICODE)

# Repeated Arabic/any letters: match 3+ identical letters in a row
_REPEATED_LETTERS_RE = re.compile(r"(.)\1{2,}", re.UNICODE)


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
# Smart bad-word normalization
# Collapses bypass tricks like spaces, symbols, repeated letters,
# mixed Arabic/English, diacritics, and common substitutions.
# ---------------------------------------------------------------------------

def normalize_for_filter(text: str) -> str:
    """
    Return a simplified version of *text* that collapses common bypass tricks:
      - Arabic diacritics stripped
      - Alef/taa-marbuta/alef-maqsura normalization
      - All non-alphanumeric symbols stripped (ك@لب → كلب)
      - Spaces removed (ك ل ب → كلب)
      - Repeated consecutive letters collapsed to 1 (كلببببب → كلب)
      - Lowercased (for Latin characters)
    """
    t = text

    # 1. Strip Arabic diacritics
    t = _ARABIC_DIACRITICS_RE.sub("", t)

    # 2. Normalize Arabic letter variants
    t = t.translate(_ARABIC_NORM_MAP)

    # 3. Strip symbols (keep letters, digits, spaces)
    t = _SYMBOL_RE.sub("", t)

    # 4. Remove all spaces (catches letter-spaced evasion)
    t = t.replace(" ", "")

    # 5. Collapse repeated letters (3+ in a row → 1)
    t = _REPEATED_LETTERS_RE.sub(r"\1", t)

    # 6. Lowercase
    t = t.lower()

    return t


def normalize_bad_word(word: str) -> str:
    """Apply the same normalization to a single bad word."""
    return normalize_for_filter(word)


def contains_bad_word(text: str, bad_words: list[str]) -> str | None:
    """
    Return the first matched bad word if *text* contains any entry in
    *bad_words* after normalization. Returns None if no match.
    """
    normalized_text = normalize_for_filter(text)
    for word in bad_words:
        nw = normalize_bad_word(word)
        if not nw:
            continue
        if nw in normalized_text:
            return word
    return None


# ---------------------------------------------------------------------------
# Time helpers
# ---------------------------------------------------------------------------

def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def format_duration(seconds: int) -> str:
    """Return a human-readable duration string in Arabic."""
    if seconds < 60:
        return f"{seconds} ثانية"
    if seconds < 3600:
        m = seconds // 60
        return f"{m} دقيقة"
    if seconds < 86400:
        h = seconds // 3600
        return f"{h} ساعة"
    d = seconds // 86400
    return f"{d} يوم"


def format_duration_short(seconds: int) -> str:
    """Short English form used internally (e.g. 1h, 30m)."""
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


def format_datetime_ar(dt: datetime) -> str:
    """Format a UTC datetime to a readable Arabic-locale string."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.strftime("%Y-%m-%d %H:%M")
