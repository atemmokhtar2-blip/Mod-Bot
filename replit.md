# Telegram Moderation Bot (Arabic) — بوت الإشراف العربي v3

A professional Arabic Telegram group moderation bot built with Python, aiogram 3, SQLAlchemy, and PostgreSQL.

## Stack

- **Language:** Python 3
- **Telegram:** aiogram 3.13.1
- **Database:** SQLAlchemy 2 (async) + asyncpg + Replit's built-in PostgreSQL
- **Entry point:** `artifacts/telegram-bot/main.py`

## How to Run

The workflow **Telegram Moderation Bot** runs the bot:

```
cd artifacts/telegram-bot && python main.py
```

## Required Secrets

Store these as Replit Secrets (never in source control):

| Secret | Required | Description |
|--------|----------|-------------|
| `TELEGRAM_BOT_TOKEN` | ✅ | Bot token from @BotFather |
| `BOT_OWNER_IDS` | ✅ | Your Telegram numeric user ID(s), comma-separated — grants access to `/addaikey`, `/listaikeys`, and the AI wizard |
| `AI_KEY_ENCRYPTION_KEY` | ✅* | Fernet key for encrypting stored Gemini API keys. Generate: `python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`. Required only if using AI/Gemini features. |
| `WEBHOOK_SECRET` | ❌ | Random 32+ char string shared with Telegram's `setWebhook` call — only needed when deploying to Vercel/webhook mode, not for long-polling on Replit. Generate: `python3 -c "import secrets; print(secrets.token_hex(32))"` |

`DATABASE_URL` is auto-provided by Replit's built-in PostgreSQL — no configuration needed.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_SSL` | `false` | Set `true` for external PostgreSQL (Supabase, Neon, etc.) |
| `LOG_LEVEL` | `INFO` | Logging verbosity |

## Bot Features

- `/ban`, `/unban`, `/mute`, `/unmute`, `/warn`, `/resetwarns`, `/del`, `/pin`, `/unpin`, `/info`
- Auto-moderation: flood detection, duplicate detection, emoji/length filtering
- Per-group settings with inline keyboard dashboard
- Full Arabic UI (`bot/strings/ar.py`)
- 9-table PostgreSQL schema auto-created on startup

## Project Structure

```
artifacts/telegram-bot/
├── main.py              # Entry point
├── config.py            # Environment variable loading
├── requirements.txt     # Python dependencies
├── database/            # SQLAlchemy models, engine, repository
├── bot/
│   ├── handlers/        # Command and event handlers
│   ├── keyboards/       # Inline keyboard builders
│   ├── middlewares/     # DB session injection
│   ├── filters/         # Permission filters
│   ├── services/        # Business logic
│   └── strings/ar.py   # All Arabic UI strings
└── utils/               # Logger, helpers
```

## User Preferences

- Keep the project's existing structure and stack.
