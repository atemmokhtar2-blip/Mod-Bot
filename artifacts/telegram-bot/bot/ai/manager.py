"""
AI Protection Manager — the single entrypoint the rest of the bot calls.

    from bot.ai.manager import ai_manager
    verdict = await ai_manager.analyze_text(session, text)
    verdict = await ai_manager.analyze_image(session, image_bytes, mime_type)

Both return an AIVerdict or None. None means "AI unavailable" (no configured
keys, or every key attempt failed) — callers MUST treat that as "skip the AI
check for this message"; it is never treated as a violation and never blocks
the rest of the filter pipeline. This is what makes the bot resilient to a
single bad/expired/rate-limited key.
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from bot.ai.base import AIProvider, AIVerdict
from bot.ai.gemini_provider import GeminiProvider
from bot.ai.key_manager import key_manager
from database import repository as repo
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
                verdict = await call(engine, key_row.api_key)
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


ai_manager = AIProtectionManager()
