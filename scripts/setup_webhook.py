"""
Register (or delete) the Telegram webhook URL.

Run this once after every Vercel deployment to point Telegram at your new URL.

Usage
-----
Set the webhook:
  TELEGRAM_BOT_TOKEN=xxx  \\
  python scripts/setup_webhook.py --url https://YOUR-APP.vercel.app/api/webhook [--secret YOUR_SECRET]

Delete the webhook (switch back to polling mode):
  TELEGRAM_BOT_TOKEN=xxx  \\
  python scripts/setup_webhook.py --delete

Environment variables (alternative to flags):
  BOT_WEBHOOK_URL   — the full webhook URL
  WEBHOOK_SECRET    — the secret token (optional but recommended)
  TELEGRAM_BOT_TOKEN
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request


def tg_request(token: str, method: str, params: dict) -> dict:
    url  = f"https://api.telegram.org/bot{token}/{method}"
    data = urllib.parse.urlencode(params).encode()
    req  = urllib.request.Request(url, data=data, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        body = exc.read()
        try:
            return json.loads(body)
        except Exception:
            print(f"HTTP {exc.code}: {body}", file=sys.stderr)
            sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Register or delete the Telegram bot webhook."
    )
    parser.add_argument(
        "--url",
        default=os.environ.get("BOT_WEBHOOK_URL", ""),
        help="Full webhook URL (e.g. https://your-app.vercel.app/api/webhook)",
    )
    parser.add_argument(
        "--secret",
        default=os.environ.get("WEBHOOK_SECRET", ""),
        help="Secret token set in WEBHOOK_SECRET (optional but recommended)",
    )
    parser.add_argument(
        "--delete",
        action="store_true",
        help="Delete the webhook and revert to long-polling mode",
    )
    args = parser.parse_args()

    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        print("Error: TELEGRAM_BOT_TOKEN is not set.", file=sys.stderr)
        sys.exit(1)

    # ── Delete webhook ────────────────────────────────────────────────────────
    if args.delete:
        result = tg_request(token, "deleteWebhook", {"drop_pending_updates": "true"})
        if result.get("ok"):
            print("✅  Webhook deleted — bot will now use long-polling.")
        else:
            print(f"❌  Failed to delete webhook: {result}", file=sys.stderr)
            sys.exit(1)
        return

    # ── Set webhook ───────────────────────────────────────────────────────────
    if not args.url:
        print(
            "Error: provide --url or set BOT_WEBHOOK_URL.",
            file=sys.stderr,
        )
        sys.exit(1)

    params: dict = {
        "url": args.url,
        "drop_pending_updates": "true",
        "allowed_updates": json.dumps([
            "message",
            "edited_message",
            "callback_query",
            "chat_member",
            "my_chat_member",
        ]),
        "max_connections": "40",
    }
    if args.secret:
        params["secret_token"] = args.secret

    result = tg_request(token, "setWebhook", params)
    if result.get("ok"):
        print(f"✅  Webhook registered: {args.url}")
        if args.secret:
            print("🔒  Secret token is active — only Telegram can reach your endpoint.")
    else:
        print(f"❌  Failed: {result}", file=sys.stderr)
        sys.exit(1)

    # Print current webhook info
    info = tg_request(token, "getWebhookInfo", {})
    wh   = info.get("result", {})
    print(f"\nWebhook info:")
    print(f"  URL           : {wh.get('url')}")
    print(f"  Pending updates: {wh.get('pending_update_count', 0)}")
    print(f"  Last error    : {wh.get('last_error_message', 'none')}")
    print(f"  Max connections: {wh.get('max_connections')}")


if __name__ == "__main__":
    main()
