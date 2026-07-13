# Telegram Moderation Bot

A professional, modular Telegram moderation and management bot built with Python, aiogram 3, and PostgreSQL.

## Run & Operate

- **Telegram Moderation Bot** workflow — runs `cd artifacts/telegram-bot && python main.py`
- `pnpm --filter @workspace/api-server run dev` — run the Node API server (unused by bot, port 5000)
- Required env: `TELEGRAM_BOT_TOKEN` (Replit Secret), `DATABASE_URL` (auto-managed by Replit)

## Stack

- Python 3.11, aiogram 3.13
- PostgreSQL + SQLAlchemy (async) + asyncpg
- No SSL on internal Replit Postgres — `connect_args={"ssl": None}` in engine

## Where things live

```
artifacts/telegram-bot/
├── main.py                  # Entry point
├── config.py                # Env-var config (_adapt_db_url strips sslmode for asyncpg)
├── database/
│   ├── models.py            # 9 ORM tables
│   ├── connection.py        # Async engine (ssl=None required for Replit internal PG)
│   └── repository.py       # All DB access
├── bot/
│   ├── handlers/            # start, group_events, message_filter, admin_commands, callbacks
│   ├── keyboards/builder.py # All inline keyboards
│   ├── middlewares/         # DbSessionMiddleware
│   ├── filters/             # IsGroupAdmin, IsGroupOwner, IsBotAdmin
│   └── services/            # group, moderation, warning, stats services
└── utils/                   # logger, helpers
```

## Architecture decisions

- **Repository pattern** — all DB reads/writes go through `database/repository.py`; handlers never build raw ORM queries
- **asyncpg + SQLAlchemy async** — `postgresql+asyncpg://` URL, `ssl=None` for Replit's local Postgres
- **Long-polling** for V1 simplicity; swap to webhook in production
- **MemoryStorage** for FSM (settings editing wizard) — resets on restart, intentional for V1
- **In-memory flood/duplicate state** — fast but resets on restart; move to Redis for multi-worker

## Product

- Add bot to any Telegram group, grant admin rights, use /start in private chat to get the dashboard
- 11 auto-moderation filters with configurable per-filter actions (delete/warn/mute/kick/ban)
- Warning system with configurable limit and auto-punishment
- Admin commands: /ban /unban /mute /unmute /warn /resetwarns /del /pin /unpin /info
- Welcome messages, per-group settings, audit logs, daily statistics
- Channel registration and basic management

## User preferences

_Populate as you build — explicit user instructions worth remembering across sessions._

## Gotchas

- Replit internal PostgreSQL rejects SSL — always use `connect_args={"ssl": None}` with asyncpg
- DATABASE_URL may contain `?sslmode=require` — strip it in `_adapt_db_url()` before passing to asyncpg
- Bot must be Telegram Administrator with Delete/Ban/Restrict/Pin permissions to function
- `pnpm run typecheck` only covers Node.js packages — Python bot has no TS typecheck step

## Pointers

- See `artifacts/telegram-bot/README.md` for full feature and architecture docs
