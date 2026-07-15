"""
Symmetric encryption for sensitive values at rest — V7.1.

Used exclusively by the Gemini API key manager so raw provider keys are never
stored in plaintext in the database. Uses Fernet (AES-128-CBC + HMAC) from
the `cryptography` package, keyed by the `AI_KEY_ENCRYPTION_KEY` environment
variable (a 32-byte urlsafe-base64 key, generated once per deployment).

Never log or display decrypted values — decrypt only at the point of use
(calling the provider's API), never for UI display. Masking for display is
computed once from the plaintext at insertion time and stored separately
(see AIProviderKey.key_mask), so normal operation never needs to decrypt.
"""

from __future__ import annotations

import os
from functools import lru_cache

from cryptography.fernet import Fernet, InvalidToken

from utils.logger import get_logger

log = get_logger(__name__)


class EncryptionNotConfigured(RuntimeError):
    """Raised when AI_KEY_ENCRYPTION_KEY is missing — never fall back to plaintext."""


@lru_cache(maxsize=1)
def _fernet() -> Fernet:
    key = os.environ.get("AI_KEY_ENCRYPTION_KEY")
    if not key:
        raise EncryptionNotConfigured(
            "AI_KEY_ENCRYPTION_KEY is not set — cannot encrypt/decrypt Gemini API keys."
        )
    try:
        return Fernet(key.encode() if isinstance(key, str) else key)
    except Exception as exc:  # invalid key format
        raise EncryptionNotConfigured(f"AI_KEY_ENCRYPTION_KEY is invalid: {exc}") from exc


def encrypt_secret(plaintext: str) -> str:
    """Encrypt a value for storage. Returns a urlsafe token string."""
    return _fernet().encrypt(plaintext.encode()).decode()


def decrypt_secret(token: str) -> str:
    """Decrypt a value stored via `encrypt_secret`. Never log the result."""
    try:
        return _fernet().decrypt(token.encode()).decode()
    except InvalidToken as exc:
        log.error("Failed to decrypt a stored secret (invalid token or wrong key).")
        raise ValueError("Stored value could not be decrypted.") from exc


def is_encrypted(value: str) -> bool:
    """Best-effort check: does `value` look like a Fernet token we produced?"""
    try:
        _fernet().decrypt(value.encode())
        return True
    except Exception:
        return False


def mask(plaintext: str) -> str:
    """Human-readable masked form for display, e.g. 'AIza**************AB12'."""
    if len(plaintext) <= 8:
        return "•" * max(len(plaintext), 4)
    middle = "*" * max(len(plaintext) - 8, 4)
    return f"{plaintext[:4]}{middle}{plaintext[-4:]}"
