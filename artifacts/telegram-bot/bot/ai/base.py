"""
Provider-agnostic contract for AI moderation engines.

Every provider (Gemini today; Grok/OpenAI/Claude later) implements
`AIProvider` and returns an `AIVerdict`. The rest of the bot (settings panel,
filter pipeline, key manager) only ever talks to this interface, never to a
provider's SDK directly.
"""

from __future__ import annotations

from dataclasses import dataclass

CLASSIFICATIONS = ("SAFE", "SUSPICIOUS", "VIOLATION")
RECOMMENDED_ACTIONS = ("ignore", "delete", "warn", "mute", "ban")


@dataclass
class AIVerdict:
    """Structured moderation verdict — never free-form chat output."""

    classification: str        # SAFE | SUSPICIOUS | VIOLATION
    confidence: int             # 0-100
    reason: str                 # short explanation, for logs/admins only
    recommended_action: str     # ignore | delete | warn | mute | ban

    @property
    def is_violation(self) -> bool:
        return self.classification == "VIOLATION"

    @property
    def is_suspicious(self) -> bool:
        return self.classification == "SUSPICIOUS"


class AIProvider:
    """
    Base interface every AI moderation provider must implement.

    A provider must NEVER be used as a chatbot — it only classifies content
    and returns structured verdicts (see AIVerdict). To add a new provider:
    1. Subclass this, implement analyze_text/analyze_image.
    2. Register it in bot/ai/manager.py's PROVIDER_REGISTRY.
    3. Add its keys via the existing /addaikey command with a new provider name.
    No other file needs to change.
    """

    name: str = "base"

    async def analyze_text(self, api_key: str, text: str) -> AIVerdict:
        raise NotImplementedError

    async def analyze_image(self, api_key: str, image_bytes: bytes, mime_type: str) -> AIVerdict:
        raise NotImplementedError

    async def analyze_links(self, api_key: str, url_string: str) -> AIVerdict:
        """V7: Classify extracted URLs for safety threats. Override in each provider."""
        raise NotImplementedError

    async def analyze_profile(self, api_key: str, profile_text: str) -> AIVerdict:
        """V7.2: Classify a username/display-name or group description. Override in each provider."""
        raise NotImplementedError

    async def validate_key(self, api_key: str) -> None:
        """
        V7.2: Perform a minimal REAL request against the provider to confirm the
        key is valid. Must raise on any failure (auth error, network error,
        quota exhausted, etc). Must NOT raise on success.
        """
        raise NotImplementedError
