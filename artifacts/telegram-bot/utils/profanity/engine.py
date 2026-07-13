"""
Profanity matching engine — V4.1.

Architecture
------------
Built-in dictionary
    Loaded once at module import, normalized, and compiled into a single
    regex alternation pattern.  Pattern is reused across all groups and
    all messages — zero per-message allocation after startup.

Custom words (per group)
    Stored in the database (custom_words table).  The engine maintains an
    in-process LRU-style cache keyed by group_id.  Cache entries expire
    after CUSTOM_CACHE_TTL seconds or are explicitly invalidated when
    a word is added/removed.

Matching
    Both the incoming text and every word in the dictionary are normalized
    via normalizer.normalize() before comparison.  This means the engine
    compiles normalized(word) patterns and searches normalized(text) — so
    the per-message cost is:
        1. normalize(text)          → one pass through the text
        2. builtin_pattern.search() → single regex scan (compiled FA)
        3. custom_pattern.search()  → single regex scan (or None if empty)

    Total: O(len(text) * constant).  Fast for any realistic group message.

Usage
-----
    from utils.profanity.engine import ProfanityEngine

    engine = ProfanityEngine()
    word = engine.check("يا كلب اسكت", custom_words=["بنات", "سكس"])
    if word:
        # word is the first matched normalized pattern
        ...
"""

from __future__ import annotations

import re
import time
from threading import Lock
from typing import Optional

from utils.profanity.dictionary import ALL_WORDS
from utils.profanity.normalizer import normalize

# Cache TTL for per-group custom word patterns (seconds)
CUSTOM_CACHE_TTL: float = 120.0

# Minimum normalized word length — shorter words cause too many false positives
MIN_WORD_LEN: int = 2


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _build_pattern(words: list[str]) -> Optional[re.Pattern]:
    """
    Normalize each word, deduplicate, filter short entries, then compile a
    single alternation regex.  Returns None when no words survive filtering.
    """
    normalized: list[str] = []
    seen: set[str] = set()
    for w in words:
        nw = normalize(w)
        if len(nw) >= MIN_WORD_LEN and nw not in seen:
            seen.add(nw)
            normalized.append(nw)

    if not normalized:
        return None

    # Sort longest-first so more-specific matches are preferred
    normalized.sort(key=len, reverse=True)

    # Escape every entry before joining (handles any residual regex chars)
    escaped = [re.escape(nw) for nw in normalized]
    pattern_str = "(?:" + "|".join(escaped) + ")"
    return re.compile(pattern_str, re.UNICODE)


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class ProfanityEngine:
    """
    Thread-safe profanity detection engine.

    Instantiate once and share across all handlers.
    The builtin pattern is compiled in __init__; custom patterns are
    lazy-compiled per group with TTL-based invalidation.
    """

    def __init__(self) -> None:
        # --- Built-in pattern (compiled once, shared forever) ---
        self._builtin_pattern: Optional[re.Pattern] = _build_pattern(ALL_WORDS)
        self._builtin_word_count: int = len(ALL_WORDS)

        # --- Per-group custom word cache ---
        # Structure: { group_id: (expiry_timestamp, pattern | None) }
        self._cache: dict[int, tuple[float, Optional[re.Pattern]]] = {}
        self._lock = Lock()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def check(
        self,
        text: str,
        custom_words: Optional[list[str]] = None,
        group_id: Optional[int] = None,
    ) -> Optional[str]:
        """
        Scan *text* for profanity.

        Parameters
        ----------
        text         : raw incoming message text (not pre-normalized)
        custom_words : optional list of raw custom words for this group
                       (pass the list from the DB, not pre-normalized)
        group_id     : used as cache key when custom_words is given

        Returns
        -------
        The matched normalized pattern string if a hit is found, else None.
        """
        if not text:
            return None

        normalized_text = normalize(text)
        if not normalized_text:
            return None

        # 1. Check built-in dictionary
        if self._builtin_pattern:
            m = self._builtin_pattern.search(normalized_text)
            if m:
                return m.group(0)

        # 2. Check custom words
        if custom_words:
            custom_pat = self._get_custom_pattern(group_id, custom_words)
            if custom_pat:
                m = custom_pat.search(normalized_text)
                if m:
                    return m.group(0)

        return None

    def check_custom_only(
        self,
        text: str,
        custom_words: list[str],
        group_id: Optional[int] = None,
    ) -> Optional[str]:
        """Like check() but only tests custom words (skips built-in dictionary)."""
        if not text or not custom_words:
            return None
        normalized_text = normalize(text)
        if not normalized_text:
            return None
        custom_pat = self._get_custom_pattern(group_id, custom_words)
        if custom_pat:
            m = custom_pat.search(normalized_text)
            if m:
                return m.group(0)
        return None

    def invalidate(self, group_id: int) -> None:
        """Call this whenever a group's custom word list changes."""
        with self._lock:
            self._cache.pop(group_id, None)

    @property
    def builtin_word_count(self) -> int:
        return self._builtin_word_count

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_custom_pattern(
        self,
        group_id: Optional[int],
        custom_words: list[str],
    ) -> Optional[re.Pattern]:
        """
        Return a compiled pattern for *custom_words*, using the cache when
        group_id is provided.
        """
        if group_id is None:
            return _build_pattern(custom_words)

        now = time.monotonic()
        with self._lock:
            cached = self._cache.get(group_id)
            if cached and cached[0] > now:
                return cached[1]

            pattern = _build_pattern(custom_words)
            self._cache[group_id] = (now + CUSTOM_CACHE_TTL, pattern)
            return pattern


# ---------------------------------------------------------------------------
# Module-level singleton — import and reuse, do not instantiate per-message
# ---------------------------------------------------------------------------
engine = ProfanityEngine()
