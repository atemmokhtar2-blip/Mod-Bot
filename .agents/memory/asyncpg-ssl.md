---
name: Replit asyncpg SSL quirk
description: How to connect asyncpg to Replit's internal PostgreSQL without SSL errors
---

## Rule

Never pass `ssl="require"` or rely on `sslmode=require` in the URL when connecting asyncpg to Replit's internal PostgreSQL. Use `connect_args={"ssl": None}` on the SQLAlchemy engine.

**Why:** Replit's internal Postgres (hostname `helium`) does not support SSL from within the same environment — it rejects the upgrade handshake. Additionally, asyncpg does not accept the standard `?sslmode=...` URL parameter and raises `TypeError: connect() got an unexpected keyword argument 'sslmode'`.

**How to apply:**
1. In `_adapt_db_url()` (config.py), strip `?sslmode=...` from the URL with `re.sub(r"[?&]sslmode=[^&]*", "", url)`.
2. In `create_async_engine(...)`, pass `connect_args={"ssl": None}` explicitly.
3. This applies to all asyncpg/SQLAlchemy async projects on Replit, not just this bot.
