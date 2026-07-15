"""
Symmetric encryption for sensitive values at rest — V7.2.

Used exclusively by the Gemini API key manager so raw provider keys are never
stored in plaintext in the database. Uses Fernet (AES-128-CBC + HMAC) from
the `cryptography` package, keyed by the `AI_KEY_ENCRYPTION_KEY` environment
variable (a 32-byte urlsafe-base64 key, generated once per deployment).

Never log or display decrypted values — decrypt only at the point of use
(calling the provider's API), never for UI display. Masking for display is
computed once from the plaintext at insertion time and stored separately
(see AIProviderKey.key_mask), so normal operation never needs to decrypt.

Key format:
  A valid Fernet key is 32 bytes encoded as urlsafe-base64, which produces
  exactly 44 characters (including the trailing `=` padding character).
  Some tools omit the trailing `=`; this module auto-pads 43-char keys so
  they still work without requiring the user to regenerate.
"""

from __future__ import annotations

import os
from functools import lru_cache

from cryptography.fernet import Fernet, InvalidToken

from utils.logger import get_logger

log = get_logger(__name__)


class EncryptionNotConfigured(RuntimeError):
    """Raised when AI_KEY_ENCRYPTION_KEY is missing or invalid — never fall back to plaintext."""


def _normalise_key(raw: str) -> bytes:
    """
    Normalise a raw key string into bytes accepted by Fernet.

    Accepts:
      - 44-char urlsafe-base64 string (standard Fernet key)
      - 43-char urlsafe-base64 string missing its trailing `=` (auto-padded)

    Raises ValueError for anything else.
    """
    s = raw.strip()
    if len(s) == 43:
        s = s + "="          # add missing padding — common copy-paste artefact
    if len(s) != 44:
        raise ValueError(
            f"Key is {len(s)} characters; expected 44 (32 urlsafe-base64 bytes). "
            "Generate one with: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
        )
    return s.encode()


@lru_cache(maxsize=1)
def _fernet() -> Fernet:
    raw = os.environ.get("AI_KEY_ENCRYPTION_KEY", "")
    if not raw:
        raise EncryptionNotConfigured(
            "AI_KEY_ENCRYPTION_KEY is not set — cannot encrypt/decrypt Gemini API keys. "
            "Generate one with: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
        )
    try:
        key_bytes = _normalise_key(raw)
        return Fernet(key_bytes)
    except ValueError as exc:
        raise EncryptionNotConfigured(f"AI_KEY_ENCRYPTION_KEY is invalid: {exc}") from exc
    except Exception as exc:
        raise EncryptionNotConfigured(f"AI_KEY_ENCRYPTION_KEY could not be loaded: {exc}") from exc


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


def get_encryption_status() -> dict:
    """
    Return a structured status dict for startup reporting.

    Keys:
      ok          bool   — True if encryption is fully operational
      configured  bool   — True if AI_KEY_ENCRYPTION_KEY is present
      valid       bool   — True if the key can be loaded into Fernet
      padded      bool   — True if a 43-char key was auto-padded to 44
      error       str|None — human-readable problem description
      suggestion  str|None — generate-key command when key is missing/invalid
    """
    _GEN_CMD = (
        'python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"'
    )
    raw = os.environ.get("AI_KEY_ENCRYPTION_KEY", "")
    if not raw:
        return {
            "ok": False, "configured": False, "valid": False, "padded": False,
            "error": "AI_KEY_ENCRYPTION_KEY is not set.",
            "suggestion": f"Generate a key and set it as a secret:\n  {_GEN_CMD}",
        }

    padded = len(raw.strip()) == 43
    try:
        key_bytes = _normalise_key(raw)
        f = Fernet(key_bytes)
        # Round-trip smoke test
        token = f.encrypt(b"smoke-test")
        f.decrypt(token)
        return {
            "ok": True, "configured": True, "valid": True, "padded": padded,
            "error": None, "suggestion": None,
        }
    except EncryptionNotConfigured as exc:
        return {
            "ok": False, "configured": True, "valid": False, "padded": False,
            "error": str(exc),
            "suggestion": f"Generate a new key:\n  {_GEN_CMD}",
        }
    except Exception as exc:
        return {
            "ok": False, "configured": True, "valid": False, "padded": False,
            "error": f"Unexpected error loading key: {exc}",
            "suggestion": f"Generate a new key:\n  {_GEN_CMD}",
        }
