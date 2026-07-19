"""
Vercel serverless webhook handler for the Telegram Moderation Bot.

Architecture
------------
- Vercel Python runtime invokes handler.do_POST() for every Telegram update.
- A persistent asyncio event loop is kept at module level so SQLAlchemy's
  async engine and aiogram's Bot remain valid across warm invocations of the
  same container (avoids the overhead of re-creating DB connections per request).
- DB migrations (init_db) and Bot/Dispatcher construction run once per cold
  start, then are cached for the container's lifetime.
- The handler always returns HTTP 200 (even on processing errors) so Telegram
  never retries the same update and causes a flood.

Environment variables required on Vercel
-----------------------------------------
  TELEGRAM_BOT_TOKEN   — from @BotFather
  DATABASE_URL         — external PostgreSQL (Neon / Supabase / etc.)
  WEBHOOK_SECRET       — (recommended) secret token set via setWebhook
  LOG_LEVEL            — optional, default INFO
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys
from http.server import BaseHTTPRequestHandler

# ── Make the telegram-bot package importable from Vercel's function sandbox ──
_BOT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "artifacts", "telegram-bot")
)
if _BOT_ROOT not in sys.path:
    sys.path.insert(0, _BOT_ROOT)

# ── Persistent event loop ─────────────────────────────────────────────────────
# asyncio.run() creates and *closes* a new loop each call, which invalidates
# SQLAlchemy's async engine.  Using a long-lived loop avoids that.
_loop: asyncio.AbstractEventLoop = asyncio.new_event_loop()
asyncio.set_event_loop(_loop)

# ── Module-level singletons (populated on first request) ─────────────────────
_ready: bool = False
_bot = None   # aiogram.Bot
_dp  = None   # aiogram.Dispatcher

log = logging.getLogger("webhook")


# ─────────────────────────────────────────────────────────────────────────────
# Initialisation (cold-start only)
# ─────────────────────────────────────────────────────────────────────────────

async def _bootstrap() -> None:
    """
    Run once per container cold-start:
      1. Configure logging
      2. Run DB migrations
      3. Build Bot + Dispatcher (using the shared factory in bot/setup.py)
    """
    global _ready, _bot, _dp

    if _ready:
        return

    from config import load_config
    from database.connection import init_db
    from bot.setup import create_bot, create_dispatcher

    cfg = load_config()

    logging.basicConfig(
        level=getattr(logging, cfg.log_level, logging.INFO),
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    )

    log.info("Cold start — running DB migrations…")
    await init_db()

    _bot = create_bot(cfg)
    _dp  = create_dispatcher()

    me = await _bot.get_me()
    log.info("Bot @%s (id=%s) ready (webhook mode).", me.username, me.id)
    _ready = True


# ─────────────────────────────────────────────────────────────────────────────
# Update processing
# ─────────────────────────────────────────────────────────────────────────────

async def _handle(body: bytes) -> None:
    from aiogram.types import Update

    await _bootstrap()
    update = Update.model_validate_json(body)
    await _dp.feed_update(_bot, update)


# ─────────────────────────────────────────────────────────────────────────────
# Vercel handler class
# ─────────────────────────────────────────────────────────────────────────────

class handler(BaseHTTPRequestHandler):
    """
    Vercel Python serverless entry point.
    The class MUST be named `handler` (Vercel convention).
    """

    # Silence the default access-log noise in Vercel's log stream
    def log_message(self, *args, **kwargs) -> None:  # type: ignore[override]
        pass

    # ── POST — receive Telegram updates ──────────────────────────────────────
    def do_POST(self) -> None:
        # 1. Verify the shared secret so only Telegram can POST here
        expected = os.environ.get("WEBHOOK_SECRET", "")
        received = self.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
        if expected and received != expected:
            log.warning("Rejected request: invalid secret token.")
            return self._send(403, b"Forbidden")

        # 2. Read body
        try:
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length)
            if not body:
                return self._send(400, b"Empty body")
        except Exception as exc:
            log.error("Failed to read request body: %s", exc)
            return self._send(400, b"Bad Request")

        # 3. Process update — always return 200 so Telegram never retries
        try:
            _loop.run_until_complete(_handle(body))
        except Exception as exc:
            log.exception("Unhandled error while processing update: %s", exc)

        return self._send(200, b"OK")

    # ── GET — health / liveness probe ────────────────────────────────────────
    def do_GET(self) -> None:
        return self._send(200, b"Telegram Bot Webhook endpoint is active.")

    # ── Helper ────────────────────────────────────────────────────────────────
    def _send(self, code: int, body: bytes) -> None:
        self.send_response(code)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
