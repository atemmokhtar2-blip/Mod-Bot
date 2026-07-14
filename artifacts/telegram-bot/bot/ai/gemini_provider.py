"""
Gemini implementation of the AIProvider interface.

Uses the `google-genai` SDK directly with a raw, user-supplied API key (no
Replit-managed connector) since the key manager owns key lifecycle. Always
requests `response_mime_type="application/json"` and still defensively
parses the response — a model can occasionally wrap JSON in prose despite
instructions, so we extract the first `{...}` block rather than trusting
`response.text` to be pure JSON.
"""

from __future__ import annotations

import json
import re

from bot.ai.base import AIProvider, AIVerdict, CLASSIFICATIONS, RECOMMENDED_ACTIONS
from bot.ai.prompts import IMAGE_SYSTEM_PROMPT, TEXT_SYSTEM_PROMPT
from utils.logger import get_logger

log = get_logger(__name__)

_MODEL = "gemini-2.5-flash"
_JSON_RE = re.compile(r"\{.*\}", re.DOTALL)


def _parse_verdict(raw_text: str | None) -> AIVerdict:
    match = _JSON_RE.search(raw_text or "")
    if not match:
        raise ValueError(f"No JSON object found in Gemini response: {(raw_text or '')[:200]!r}")

    data = json.loads(match.group(0))

    classification = str(data.get("classification", "SAFE")).upper()
    if classification not in CLASSIFICATIONS:
        classification = "SAFE"

    try:
        confidence = int(data.get("confidence", 0))
    except (TypeError, ValueError):
        confidence = 0
    confidence = max(0, min(100, confidence))

    reason = str(data.get("reason", ""))[:500]

    action = str(data.get("recommended_action", "ignore")).lower()
    if action not in RECOMMENDED_ACTIONS:
        action = "ignore"

    return AIVerdict(
        classification=classification,
        confidence=confidence,
        reason=reason,
        recommended_action=action,
    )


class GeminiProvider(AIProvider):
    name = "gemini"

    async def analyze_text(self, api_key: str, text: str) -> AIVerdict:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=api_key)
        response = await client.aio.models.generate_content(
            model=_MODEL,
            contents=text[:4000],
            config=types.GenerateContentConfig(
                system_instruction=TEXT_SYSTEM_PROMPT,
                response_mime_type="application/json",
                temperature=0,
                max_output_tokens=300,
            ),
        )
        return _parse_verdict(response.text)

    async def analyze_image(self, api_key: str, image_bytes: bytes, mime_type: str) -> AIVerdict:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=api_key)
        response = await client.aio.models.generate_content(
            model=_MODEL,
            contents=[types.Part.from_bytes(data=image_bytes, mime_type=mime_type)],
            config=types.GenerateContentConfig(
                system_instruction=IMAGE_SYSTEM_PROMPT,
                response_mime_type="application/json",
                temperature=0,
                max_output_tokens=300,
            ),
        )
        return _parse_verdict(response.text)
