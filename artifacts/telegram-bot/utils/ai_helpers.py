"""
Shared AI / Gemini helper utilities.
Centralises error-message mapping so ai_setup.py and v4_settings.py
stay in sync automatically.
"""

from __future__ import annotations

from bot.strings.ar import S


def gemini_err_to_arabic(err: str | None) -> str:
    """Map a raw Gemini error string to a specific Arabic user message."""
    if not err:
        return S.ai_key_invalid_gemini
    e = err.lower()
    if any(k in e for k in ("api_key_invalid", "invalid api key", "api key not valid", "invalid_api_key")):
        return S.ai_key_err_api_invalid
    if any(k in e for k in ("quota", "resource_exhausted", "429", "rate limit", "ratelimitexceeded")):
        return S.ai_key_err_quota
    if any(k in e for k in ("permission_denied", "403", "forbidden")):
        return S.ai_key_err_permission
    if any(k in e for k in ("model not found", "not found", "404", "model_not_found", "unsupported")):
        return S.ai_key_err_model
    if any(k in e for k in ("network", "connection", "timeout", "timed out")):
        return S.ai_key_err_network
    return S.ai_key_err_unknown.format(detail=err[:120].strip())
