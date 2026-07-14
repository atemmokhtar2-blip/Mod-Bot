"""
Gemini (and future providers') API Key Manager — silent automatic failover.

Design
------
- Unlimited keys per provider, stored in the ai_provider_keys table.
- `acquire()` returns the next usable enabled key using an in-process
  round-robin cursor per provider; keys that recently failed are skipped for
  a cooldown window (without being disabled — the operator decides whether
  to disable a key from the key-manager commands).
- An in-process TTL cache of "which keys are enabled" avoids a DB hit on
  every single message (mirrors the ProfanityEngine word-list cache pattern
  used elsewhere in this bot).
- If every key is disabled/unusable, `acquire()` returns None. Callers
  (bot/ai/manager.py) MUST treat that as "AI unavailable right now" and
  silently skip the AI check — never raise, crash, or block moderation of
  the rest of the message.
"""

from __future__ import annotations

import time
from threading import Lock

from sqlalchemy.ext.asyncio import AsyncSession

from database import repository as repo
from utils.logger import get_logger

log = get_logger(__name__)

_KEYS_TTL = 30.0            # seconds — cache the enabled-key list per provider
_COOLDOWN_SECONDS = 300.0   # 5 minutes — skip a key after a failure without disabling it


class KeyManager:
    def __init__(self) -> None:
        self._lock = Lock()
        self._cache: dict[str, tuple[float, list[int]]] = {}   # provider -> (expiry, [key_id, ...])
        self._cursor: dict[str, int] = {}
        self._cooldown_until: dict[int, float] = {}            # key_id -> monotonic ts

    def invalidate(self, provider: str) -> None:
        """Call after add/delete/toggle so the next acquire() re-reads the DB."""
        with self._lock:
            self._cache.pop(provider, None)

    async def _enabled_key_rows(self, session: AsyncSession, provider: str):
        now = time.monotonic()
        with self._lock:
            cached = self._cache.get(provider)
        if cached and cached[0] > now:
            return await repo.get_ai_keys_by_ids(session, cached[1])

        rows = await repo.get_enabled_ai_keys(session, provider)
        with self._lock:
            self._cache[provider] = (now + _KEYS_TTL, [r.id for r in rows])
        return rows

    async def acquire(self, session: AsyncSession, provider: str):
        """Return the next usable key row for *provider*, or None if none available."""
        rows = await self._enabled_key_rows(session, provider)
        if not rows:
            return None

        now = time.monotonic()
        usable = [r for r in rows if self._cooldown_until.get(r.id, 0) <= now]
        pool = usable or rows  # if every key is cooling down, try anyway rather than giving up entirely

        with self._lock:
            idx = self._cursor.get(provider, 0) % len(pool)
            self._cursor[provider] = idx + 1
        return pool[idx]

    def mark_cooldown(self, key_id: int) -> None:
        self._cooldown_until[key_id] = time.monotonic() + _COOLDOWN_SECONDS


key_manager = KeyManager()
