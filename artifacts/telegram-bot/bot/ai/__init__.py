"""
AI moderation layer — V6.

This package is intentionally provider-agnostic: `bot/ai/base.py` defines the
contract every provider must satisfy, and `bot/ai/manager.py` is the single
entrypoint the rest of the bot calls. Adding a new provider (Grok, OpenAI,
Claude, ...) means adding one new module here and registering it — no changes
to `message_filter.py`, the settings panel, or the key manager are needed.
"""
