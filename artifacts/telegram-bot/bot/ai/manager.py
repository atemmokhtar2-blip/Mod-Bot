"""
AI Protection Manager — the single entrypoint the rest of the bot calls — V7.

    from bot.ai.manager import ai_manager
    verdict = await ai_manager.analyze_text(session, text)
    verdict = await ai_manager.analyze_image(session, image_bytes, mime_type)
    verdict = await ai_manager.analyze_links(session, url_string)   # V7

All three return an AIVerdict or None. None means "AI unavailable" (no
configured keys, or every key attempt failed) — callers MUST treat that as
"skip the AI check for this message"; it is never treated as a violation and
never blocks the rest of the filter pipeline.

Architecture: PROVIDER_REGISTRY maps provider names → AIProvider instances.
Adding a new provider (Grok, OpenAI, Claude…) means:
  1. Create a module implementing AIProvider.
  2. Add an entry to PROVIDER_REGISTRY.
  No other file needs to change.
"""

from __future__ import annotations

import hashlib
import time

from sqlalchemy.ext.asyncio import AsyncSession

from bot.ai.base import AIProvider, AIVerdict
from bot.ai.gemini_provider import GeminiProvider
from bot.ai.key_manager import key_manager
from database import repository as repo
from utils.crypto import decrypt_secret, EncryptionNotConfigured
from utils.logger import get_logger

log = get_logger(__name__)

_MAX_KEY_ATTEMPTS = 3

# ---------------------------------------------------------------------------
# V7.2: Result cache — avoids re-calling Gemini for identical/repeated content
# (e.g. flood/spam of the same message, the same image re-sent, the same URL
# posted repeatedly). Keyed by (kind, sha256(payload)); short TTL so a
# legitimately-edited follow-up is still re-checked.
# ---------------------------------------------------------------------------
_CACHE_TTL = 120.0
_verdict_cache: dict[str, tuple[float, AIVerdict]] = {}


def _cache_key(kind: str, payload: bytes | str) -> str:
    data = payload.encode("utf-8") if isinstance(payload, str) else payload
    return f"{kind}:{hashlib.sha256(data).hexdigest()}"


def _cache_get(key: str) -> AIVerdict | None:
    entry = _verdict_cache.get(key)
    if not entry:
        return None
    expiry, verdict = entry
    if expiry < time.monotonic():
        _verdict_cache.pop(key, None)
        return None
    return verdict


def _cache_set(key: str, verdict: AIVerdict) -> None:
    _verdict_cache[key] = (time.monotonic() + _CACHE_TTL, verdict)

# Registering a new provider here (plus one new module implementing
# AIProvider) is the entire integration surface — no other file changes.
PROVIDER_REGISTRY: dict[str, AIProvider] = {
    "gemini": GeminiProvider(),
}
DEFAULT_PROVIDER = "gemini"


class AIProtectionManager:
    async def _run(self, session: AsyncSession, provider: str, call, request_label: str = "request") -> AIVerdict | None:
        engine = PROVIDER_REGISTRY.get(provider)
        if not engine:
            return None

        previous_key_id: int | None = None
        for attempt in range(_MAX_KEY_ATTEMPTS):
            key_row = await key_manager.acquire(session, provider)
            if not key_row:
                return None

            if previous_key_id is not None and previous_key_id != key_row.id:
                # V7.2: explicit, dedicated log line for automatic key rotation —
                # never surfaced to end users, but always traceable in the logs.
                log.info(
                    "api_key_switch: provider=%s from_key_id=%s to_key_id=%s attempt=%s",
                    provider, previous_key_id, key_row.id, attempt + 1,
                )
            previous_key_id = key_row.id

            try:
                plaintext_key = decrypt_secret(key_row.api_key)
            except (ValueError, EncryptionNotConfigured) as exc:
                # Corrupt/undecryptable row (e.g. wrong AI_KEY_ENCRYPTION_KEY) or
                # encryption not configured — never crash moderation; skip AI entirely.
                log.error(
                    "AI provider=%s key_id=%s could not be decrypted (%s: %s) — skipping.",
                    provider, key_row.id, type(exc).__name__, exc,
                )
                key_manager.mark_cooldown(key_row.id)
                continue

            log.debug("ai_request: provider=%s key_id=%s kind=%s", provider, key_row.id, request_label)
            try:
                verdict = await call(engine, plaintext_key)
                await repo.record_ai_key_success(session, key_row.id)
                log.debug(
                    "ai_response: provider=%s key_id=%s kind=%s classification=%s confidence=%s",
                    provider, key_row.id, request_label, verdict.classification, verdict.confidence,
                )
                return verdict
            except Exception as exc:
                log.warning("api_failure: provider=%s key_id=%s kind=%s error=%s", provider, key_row.id, request_label, exc)
                key_manager.mark_cooldown(key_row.id)
                await repo.record_ai_key_failure(session, key_row.id, str(exc))
                continue

        log.warning("All %s API keys failed or are unavailable — skipping AI check.", provider)
        return None

    async def analyze_text(
        self, session: AsyncSession, text: str, provider: str = DEFAULT_PROVIDER
    ) -> AIVerdict | None:
        if not text or not text.strip():
            return None
        cache_key = _cache_key(f"text:{provider}", text)
        cached = _cache_get(cache_key)
        if cached is not None:
            return cached
        verdict = await self._run(
            session, provider, lambda engine, api_key: engine.analyze_text(api_key, text),
            request_label="text",
        )
        if verdict is not None:
            _cache_set(cache_key, verdict)
        return verdict

    async def analyze_image(
        self, session: AsyncSession, image_bytes: bytes, mime_type: str,
        provider: str = DEFAULT_PROVIDER,
    ) -> AIVerdict | None:
        cache_key = _cache_key(f"image:{provider}:{mime_type}", image_bytes)
        cached = _cache_get(cache_key)
        if cached is not None:
            return cached
        verdict = await self._run(
            session, provider,
            lambda engine, api_key: engine.analyze_image(api_key, image_bytes, mime_type),
            request_label="image",
        )
        if verdict is not None:
            _cache_set(cache_key, verdict)
        return verdict

    async def analyze_links(
        self, session: AsyncSession, url_string: str, provider: str = DEFAULT_PROVIDER
    ) -> AIVerdict | None:
        """
        V7: Classify a string of extracted URLs for safety.
        Uses a dedicated link-safety prompt so the model focuses on URL patterns
        rather than the broader message context.
        """
        if not url_string or not url_string.strip():
            return None
        cache_key = _cache_key(f"links:{provider}", url_string)
        cached = _cache_get(cache_key)
        if cached is not None:
            return cached
        verdict = await self._run(
            session, provider,
            lambda engine, api_key: engine.analyze_links(api_key, url_string),
            request_label="links",
        )
        if verdict is not None:
            _cache_set(cache_key, verdict)
        return verdict

    async def analyze_profile(
        self, session: AsyncSession, profile_text: str, provider: str = DEFAULT_PROVIDER
    ) -> AIVerdict | None:
        """V7.2: Classify a username/display-name string."""
        if not profile_text or not profile_text.strip():
            return None
        cache_key = _cache_key(f"profile:{provider}", profile_text)
        cached = _cache_get(cache_key)
        if cached is not None:
            return cached
        verdict = await self._run(
            session, provider,
            lambda engine, api_key: engine.analyze_profile(api_key, profile_text),
            request_label="profile",
        )
        if verdict is not None:
            _cache_set(cache_key, verdict)
        return verdict

    async def analyze_description(
        self, session: AsyncSession, description_text: str, provider: str = DEFAULT_PROVIDER
    ) -> AIVerdict | None:
        """V7.2: Classify a group description/bio string."""
        if not description_text or not description_text.strip():
            return None
        cache_key = _cache_key(f"description:{provider}", description_text)
        cached = _cache_get(cache_key)
        if cached is not None:
            return cached
        verdict = await self._run(
            session, provider,
            lambda engine, api_key: engine.analyze_description(api_key, description_text),
            request_label="description",
        )
        if verdict is not None:
            _cache_set(cache_key, verdict)
        return verdict

    async def test_connection(
        self, session: AsyncSession, provider: str = DEFAULT_PROVIDER
    ) -> dict:
        """
        RC1: Live connectivity test for the 🧪 owner panel button.

        Acquires the current active key from the pool and sends a minimal real
        request to the provider, measuring latency. Returns a structured dict:
          {"ok": True,  "model": str, "latency_ms": int, "key_id": int, "key_mask": str}
          {"ok": False, "error": str}   — error is the raw exception string
        Never re-raises — callers always receive a dict.
        """
        engine = PROVIDER_REGISTRY.get(provider)
        if not engine:
            return {"ok": False, "error": "unknown_provider"}

        key_row = await key_manager.acquire(session, provider)
        if not key_row:
            return {"ok": False, "error": "no_keys"}

        try:
            plaintext_key = decrypt_secret(key_row.api_key)
        except ValueError as exc:
            return {"ok": False, "error": f"key_decrypt_error: {exc}"}

        try:
            result = await engine.test_connection(plaintext_key)
            log.info(
                "ai_test_ok: provider=%s key_id=%s latency_ms=%s model=%s",
                provider, key_row.id, result.get("latency_ms"), result.get("model"),
            )
            return {
                "ok": True,
                "model":      result.get("model", provider),
                "latency_ms": result.get("latency_ms", 0),
                "key_id":     key_row.id,
                "key_mask":   key_row.key_mask or "••••••••",
            }
        except Exception as exc:
            log.info(
                "ai_test_failed: provider=%s key_id=%s error=%s",
                provider, key_row.id, exc,
            )
            return {"ok": False, "error": str(exc)[:300]}

    async def validate_key(self, provider: str, api_key: str) -> tuple[bool, str | None]:
        """
        V7.2: Perform a REAL live request against *provider* with the raw
        *api_key* to confirm it actually works, BEFORE it is ever saved.
        Returns (is_valid, error_message). Never touches the key manager /
        stored keys — this is a one-off check on a candidate key.
        """
        engine = PROVIDER_REGISTRY.get(provider)
        if not engine:
            return False, "unknown_provider"
        try:
            await engine.validate_key(api_key)
            return True, None
        except Exception as exc:
            log.info("ai_key_validation_failed: provider=%s error=%s", provider, exc)
            return False, str(exc)[:300]


ai_manager = AIProtectionManager()
