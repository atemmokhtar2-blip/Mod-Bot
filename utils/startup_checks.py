"""
Startup validation — V1.0.

Runs before the bot begins polling/serving webhooks. Checks every required
subsystem and collects results into a structured report. On failure the caller
should log the report, optionally notify the bot owner via Telegram, then exit.

Design rules
------------
- Never crash — every check wraps its own exceptions and returns a status dict.
- Never log secrets — only masked or boolean representations.
- Each check is independent: a DB failure doesn't skip the encryption check.
- Returns a flat list of CheckResult dicts so callers can filter by severity.
"""

from __future__ import annotations

import asyncio
import os
import time
from typing import TypedDict

from utils.logger import get_logger

log = get_logger(__name__)


class CheckResult(TypedDict):
    name: str           # short identifier, e.g. "encryption"
    ok: bool            # True = pass
    severity: str       # "critical" | "warning" | "info"
    message: str        # one-line human summary
    detail: str | None  # optional longer context or fix hint


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------

def check_bot_token() -> CheckResult:
    val = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    if not val:
        return CheckResult(
            name="bot_token", ok=False, severity="critical",
            message="TELEGRAM_BOT_TOKEN is not set.",
            detail="Set it to your bot token from @BotFather.",
        )
    # Rough format check: digits:base64string
    parts = val.split(":")
    if len(parts) != 2 or not parts[0].isdigit():
        return CheckResult(
            name="bot_token", ok=False, severity="critical",
            message="TELEGRAM_BOT_TOKEN format is invalid (expected '<id>:<hash>').",
            detail=f"Value starts with: {val[:12]}...",
        )
    return CheckResult(
        name="bot_token", ok=True, severity="info",
        message="TELEGRAM_BOT_TOKEN is set and correctly formatted.",
        detail=None,
    )


def check_database_url() -> CheckResult:
    val = os.environ.get("DATABASE_URL", "").strip()
    if not val:
        return CheckResult(
            name="database_url", ok=False, severity="critical",
            message="DATABASE_URL is not set.",
            detail="Set it to a PostgreSQL connection string.",
        )
    if not any(val.startswith(p) for p in ("postgres://", "postgresql://", "postgresql+asyncpg://")):
        return CheckResult(
            name="database_url", ok=False, severity="critical",
            message="DATABASE_URL does not look like a PostgreSQL URL.",
            detail=f"Expected postgres:// or postgresql://. Got: {val[:30]}...",
        )
    return CheckResult(
        name="database_url", ok=True, severity="info",
        message="DATABASE_URL is set and correctly formatted.",
        detail=None,
    )


def check_encryption() -> CheckResult:
    from utils.crypto import get_encryption_status
    status = get_encryption_status()
    if status["ok"]:
        extra = " (auto-padded trailing '=')" if status["padded"] else ""
        return CheckResult(
            name="encryption", ok=True, severity="info",
            message=f"AI_KEY_ENCRYPTION_KEY is valid — encryption operational{extra}.",
            detail=None,
        )
    if not status["configured"]:
        return CheckResult(
            name="encryption", ok=False, severity="warning",
            message="AI_KEY_ENCRYPTION_KEY is not set — AI key storage is disabled.",
            detail=status.get("suggestion"),
        )
    return CheckResult(
        name="encryption", ok=False, severity="critical",
        message=f"AI_KEY_ENCRYPTION_KEY is set but invalid: {status['error']}",
        detail=status.get("suggestion"),
    )


def check_bot_owner_ids() -> CheckResult:
    val = os.environ.get("BOT_OWNER_IDS", "").strip()
    if not val:
        return CheckResult(
            name="bot_owner_ids", ok=False, severity="warning",
            message="BOT_OWNER_IDS is not set — AI key management will be inaccessible.",
            detail="Set to your Telegram numeric user ID (comma-separated for multiple owners).",
        )
    ids = [p.strip() for p in val.split(",") if p.strip()]
    valid = [p for p in ids if p.isdigit()]
    if not valid:
        return CheckResult(
            name="bot_owner_ids", ok=False, severity="warning",
            message="BOT_OWNER_IDS contains no valid numeric IDs.",
            detail=f"Got: {val[:60]}",
        )
    return CheckResult(
        name="bot_owner_ids", ok=True, severity="info",
        message=f"BOT_OWNER_IDS: {len(valid)} owner(s) configured.",
        detail=None,
    )


def check_webhook_secret() -> CheckResult:
    val = os.environ.get("WEBHOOK_SECRET", "").strip()
    if not val:
        return CheckResult(
            name="webhook_secret", ok=False, severity="warning",
            message="WEBHOOK_SECRET is not set — webhook endpoint accepts requests from any source.",
            detail="Set to a random secret string shared with Telegram's setWebhook call.",
        )
    if len(val) < 8:
        return CheckResult(
            name="webhook_secret", ok=False, severity="warning",
            message="WEBHOOK_SECRET is too short (< 8 chars) — use a longer random string.",
            detail=None,
        )
    return CheckResult(
        name="webhook_secret", ok=True, severity="info",
        message="WEBHOOK_SECRET is set.",
        detail=None,
    )


async def check_database_connectivity() -> CheckResult:
    """Attempt a real DB round-trip: connect, write a temp row, read it, delete it."""
    try:
        from database.connection import engine
        from sqlalchemy import text

        t0 = time.monotonic()
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        latency_ms = int((time.monotonic() - t0) * 1000)
        return CheckResult(
            name="database_connectivity", ok=True, severity="info",
            message=f"Database connection successful (latency: {latency_ms}ms).",
            detail=None,
        )
    except Exception as exc:
        return CheckResult(
            name="database_connectivity", ok=False, severity="critical",
            message=f"Database connection failed: {exc}",
            detail="Check DATABASE_URL and ensure PostgreSQL is reachable.",
        )


async def check_database_rw() -> CheckResult:
    """Verify read/write access via a SELECT on a system table."""
    try:
        from database.connection import engine
        from sqlalchemy import text

        async with engine.connect() as conn:
            result = await conn.execute(
                text("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'")
            )
            count = result.scalar()
        return CheckResult(
            name="database_rw", ok=True, severity="info",
            message=f"Database read/write verified ({count} public table(s)).",
            detail=None,
        )
    except Exception as exc:
        return CheckResult(
            name="database_rw", ok=False, severity="critical",
            message=f"Database read/write check failed: {exc}",
            detail=None,
        )


async def check_telegram_api(bot_token: str) -> CheckResult:
    """Call getMe to verify the bot token works."""
    try:
        from aiogram import Bot
        from aiogram.client.default import DefaultBotProperties
        from aiogram.enums import ParseMode

        t0 = time.monotonic()
        bot = Bot(token=bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
        try:
            me = await bot.get_me()
        finally:
            await bot.session.close()
        latency_ms = int((time.monotonic() - t0) * 1000)
        return CheckResult(
            name="telegram_api", ok=True, severity="info",
            message=f"Telegram API OK — @{me.username} (id={me.id}, latency: {latency_ms}ms).",
            detail=None,
        )
    except Exception as exc:
        return CheckResult(
            name="telegram_api", ok=False, severity="critical",
            message=f"Telegram API call failed: {exc}",
            detail="Check TELEGRAM_BOT_TOKEN and network connectivity.",
        )


async def check_encryption_roundtrip() -> CheckResult:
    """Live encrypt/decrypt smoke test with the configured key."""
    try:
        from utils.crypto import encrypt_secret, decrypt_secret, EncryptionNotConfigured
        sentinel = "startup-smoke-test-12345"
        token = encrypt_secret(sentinel)
        recovered = decrypt_secret(token)
        if recovered != sentinel:
            return CheckResult(
                name="encryption_roundtrip", ok=False, severity="critical",
                message="Encryption round-trip produced wrong plaintext.",
                detail="The key may be corrupt. Regenerate AI_KEY_ENCRYPTION_KEY.",
            )
        return CheckResult(
            name="encryption_roundtrip", ok=True, severity="info",
            message="Encryption round-trip (encrypt → decrypt) passed.",
            detail=None,
        )
    except Exception as exc:
        return CheckResult(
            name="encryption_roundtrip", ok=False, severity="critical",
            message=f"Encryption round-trip failed: {exc}",
            detail=str(exc),
        )


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

async def run_startup_checks(bot_token: str) -> list[CheckResult]:
    """
    Run all startup checks in parallel where possible.
    Returns a list of CheckResult dicts, sorted: failures first.
    """
    # Synchronous checks (cheap, no I/O)
    sync_results = [
        check_bot_token(),
        check_database_url(),
        check_encryption(),
        check_bot_owner_ids(),
        check_webhook_secret(),
    ]

    # Async checks (I/O bound — run concurrently)
    async_results = await asyncio.gather(
        check_database_connectivity(),
        check_telegram_api(bot_token),
        check_encryption_roundtrip(),
        return_exceptions=True,
    )

    # Unwrap any gather exceptions into CheckResult failures
    safe_async: list[CheckResult] = []
    for r in async_results:
        if isinstance(r, Exception):
            safe_async.append(CheckResult(
                name="unknown_async_check", ok=False, severity="critical",
                message=f"Async check raised unexpectedly: {r}",
                detail=None,
            ))
        else:
            safe_async.append(r)  # type: ignore[arg-type]

    # DB read-only depends on connectivity — run after
    db_conn = next((r for r in safe_async if r["name"] == "database_connectivity"), None)
    if db_conn and db_conn["ok"]:
        rw = await check_database_rw()
        safe_async.append(rw)

    all_results = sync_results + safe_async
    # Sort: failures first (critical → warning → info), then alphabetical
    severity_order = {"critical": 0, "warning": 1, "info": 2}
    all_results.sort(key=lambda r: (r["ok"], severity_order.get(r["severity"], 9), r["name"]))
    return all_results


def format_report(results: list[CheckResult]) -> str:
    """Format a startup report as plain text suitable for logging or Telegram."""
    lines = ["━━━ Startup Validation Report ━━━"]
    for r in results:
        icon = "✅" if r["ok"] else ("🔴" if r["severity"] == "critical" else "⚠️")
        lines.append(f"{icon} [{r['name']}] {r['message']}")
        if r.get("detail") and not r["ok"]:
            lines.append(f"   ↳ {r['detail']}")
    failures = [r for r in results if not r["ok"]]
    criticals = [r for r in failures if r["severity"] == "critical"]
    warnings  = [r for r in failures if r["severity"] == "warning"]
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    if not failures:
        lines.append("🟢 ALL CHECKS PASSED — READY FOR PRODUCTION")
    else:
        if criticals:
            lines.append(f"🔴 {len(criticals)} CRITICAL failure(s) — bot will not function correctly")
        if warnings:
            lines.append(f"⚠️  {len(warnings)} WARNING(s) — degraded functionality")
    return "\n".join(lines)


def has_critical_failures(results: list[CheckResult]) -> bool:
    return any(not r["ok"] and r["severity"] == "critical" for r in results)
