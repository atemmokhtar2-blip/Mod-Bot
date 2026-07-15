---
name: Vercel serverless + aiogram webhook
description: Why the Bot/Dispatcher must be rebuilt per-request in a Vercel Python serverless function, not reused across invocations.
---

When wiring an aiogram Telegram bot to a Vercel Python serverless function
(`api/*.py`, `BaseHTTPRequestHandler`-based `handler` class), do not build a
single module-level `Bot` instance and reuse it across requests via repeated
`asyncio.run(...)` calls.

**Why:** aiogram's `Bot` lazily opens an aiohttp `ClientSession` bound to
whichever asyncio event loop is running when it's first used. Vercel's Python
runtime does not guarantee the same event loop — or even the same warm
process — across invocations. Reusing a `Bot` built under a previous
`asyncio.run()` call binds its session to an already-closed loop, which
breaks outbound Telegram API calls in ways that can be silent/hard to
diagnose (works on first request, fails or hangs on the next).

**How to apply:** build a fresh `Bot` + `Dispatcher` inside the async handler
for every request (cheap — Dispatcher construction is just router
registration), and always `await bot.session.close()` in a `finally` block
before the response returns. Reserve process-level caching for things that
are genuinely safe to share across loops, like a "DB already initialised"
boolean guarding an idempotent `init_db()` call.
