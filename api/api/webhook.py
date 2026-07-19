"""
Vercel serverless webhook entrypoint — V7.1.

Deploy this project to Vercel; Vercel auto-detects any `api/*.py` file as a
serverless function (using `@vercel/python`) as long as `requirements.txt`
exists at the project root — no extra build step needed.

After deploying, point Telegram's webhook at:
    https://<your-app>.vercel.app/api/webhook
using `python scripts/setup_webhook.py --url <that URL>`.

Design notes
------------
- A fresh Bot + Dispatcher is built (via bot/setup.py — the same factory
  main.py uses for long-polling) on EVERY request rather than reused across
  invocations. This is deliberate: aiogram's Bot lazily opens an aiohttp
  session bound to whichever asyncio event loop is running when it's first
  used, and Vercel's Python runtime does not guarantee the same event loop
  (or even the same process) across invocations. Reusing a Bot instance
  across `asyncio.run()` calls can bind its session to an already-closed
  loop and break silently. Creating Dispatcher is cheap (router registration
  only), so the extra cost is negligible next to actual AI/DB calls.
- `init_db()` runs once per warm process (guarded by `_db_ready`), not once
  per request — safe because it's idempotent, but skipping it on every call
  avoids needless DB round-trips.
- Always responds 200 to Telegram even on internal errors: Telegram retries
  aggressively on non-2xx, which would just redeliver the same failing
  update forever instead of moving on.
"""

from __future__ import annotations

import asyncio
import json
import os
from http.server import BaseHTTPRequestHandler

from aiogram.types import Update

from bot.setup import create_bot, create_dispatcher
from config import load_config
from database import init_db
from utils.logger import get_logger, setup_logging

_config = load_config()
setup_logging(_config.log_level)
log = get_logger("webhook")

# Warn immediately at cold-start about missing optional-but-important vars
from config import check_optional_env as _check_env
_check_env()

_db_ready = False


async def _ensure_db() -> None:
    global _db_ready
    if not _db_ready:
        await init_db()
        _db_ready = True
        log.info("Database initialised (webhook cold start).")


async def _process_update(payload: dict) -> None:
    await _ensure_db()
    bot = create_bot(_config)
    dp = create_dispatcher()
    try:
        update = Update.model_validate(payload)
        await dp.feed_webhook_update(bot, update)
    finally:
        await bot.session.close()


class handler(BaseHTTPRequestHandler):
    def do_POST(self) -> None:  # noqa: N802 — Vercel's required method name
        expected_secret = os.environ.get("WEBHOOK_SECRET")
        received_secret = self.headers.get("X-Telegram-Bot-Api-Secret-Token")
        if expected_secret and received_secret != expected_secret:
            log.warning("Rejected webhook request with invalid/missing secret token.")
            self.send_response(401)
            self.end_headers()
            return

        length = int(self.headers.get("Content-Length", 0) or 0)
        body = self.rfile.read(length) if length else b"{}"

        try:
            payload = json.loads(body or b"{}")
            asyncio.run(_process_update(payload))
        except Exception as exc:  # never let Telegram see a 5xx for this
            log.error("Webhook processing failed: %s", exc)

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b'{"ok": true}')

    def do_GET(self) -> None:  # noqa: N802 — health check
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b'{"status": "ok", "mode": "webhook"}')
