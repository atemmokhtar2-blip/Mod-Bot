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

from sqlalchemy.ext.asyncio import AsyncSession

from bot.ai.base import AIProvider, AIVerdict
from bot.ai.gemini_provider import GeminiProvider
from bot.ai.key_manager import key_manager
from database import repository as repo
from utils.crypto import decrypt_secret
from utils.logger import get_logger

log = get_logger(__name__)

_MAX_KEY_ATTEMPTS = 3

# Registering a new provider here (plus one new module implementing
# AIProvider) is the entire integration surface — no other file changes.
PROVIDER_REGISTRY: dict[str, AIProvider] = {
    "gemini": GeminiProvider(),
}
DEFAULT_PROVIDER = "gemini"


class AIProtectionManager:
    async def _run(self, session: AsyncSession, provider: str, call) -> AIVerdict | None:
        engine = PROVIDER_REGISTRY.get(provider)
        if not engine:
            return None

        for _ in range(_MAX_KEY_ATTEMPTS):
            key_row = await key_manager.acquire(session, provider)
            if not key_row:
                return None
            try:
                plaintext_key = decrypt_secret(key_row.api_key)
            except ValueError:
                # Corrupt/undecryptable row (e.g. wrong AI_KEY_ENCRYPTION_KEY) —
                # never crash moderation for this; cool it down and try the next key.
                log.error("AI provider=%s key_id=%s could not be decrypted — skipping.", provider, key_row.id)
                key_manager.mark_cooldown(key_row.id)
                continue
            try:
                verdict = await call(engine, plaintext_key)
                await repo.record_ai_key_success(session, key_row.id)
                return verdict
            except Exception as exc:
                log.warning("AI provider=%s key_id=%s failed: %s", provider, key_row.id, exc)
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
        return await self._run(
            session, provider, lambda engine, api_key: engine.analyze_text(api_key, text)
        )

    async def analyze_image(
        self, session: AsyncSession, image_bytes: bytes, mime_type: str,
        provider: str = DEFAULT_PROVIDER,
    ) -> AIVerdict | None:
        return await self._run(
            session, provider,
            lambda engine, api_key: engine.analyze_image(api_key, image_bytes, mime_type),
        )

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
        return await self._run(
            session, provider,
            lambda engine, api_key: engine.analyze_links(api_key, url_string),
        )


ai_manager = AIProtectionManager()
