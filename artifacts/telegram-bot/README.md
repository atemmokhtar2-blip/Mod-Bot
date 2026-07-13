# Telegram Moderation Bot — Version 1

A professional, modular Telegram moderation and management bot built with Python, aiogram 3, and PostgreSQL.

## Quick Start

1. Set `TELEGRAM_BOT_TOKEN` in Replit Secrets
2. The workflow starts the bot automatically

## Architecture

```
artifacts/telegram-bot/
├── main.py                  # Entry point, wires everything together
├── config.py                # Environment variable configuration
├── database/
│   ├── models.py            # SQLAlchemy ORM models (9 tables)
│   ├── connection.py        # Async engine + session factory
│   └── repository.py       # All DB reads/writes (repository pattern)
├── bot/
│   ├── handlers/
│   │   ├── start.py         # /start command → private dashboard
│   │   ├── group_events.py  # Bot added/removed, join/leave events
│   │   ├── message_filter.py# Auto-moderation (all group messages)
│   │   ├── admin_commands.py# /ban /mute /warn /del /pin etc.
│   │   └── callbacks.py     # All inline keyboard callbacks
│   ├── keyboards/
│   │   └── builder.py       # Every keyboard in the bot
│   ├── middlewares/
│   │   └── db_middleware.py # DB session injection
│   ├── filters/
│   │   └── admin_filter.py  # IsGroupOwner, IsGroupAdmin, IsBotAdmin
│   └── services/
│       ├── group_service.py    # Group/channel registration
│       ├── moderation_service.py # ban/unban/mute/unmute/kick/delete/pin
│       ├── warning_service.py  # Warning counter + auto-punishment
│       └── stats_service.py    # Statistics helpers
└── utils/
    ├── logger.py            # Structured logging setup
    └── helpers.py           # Text, time, and Telegram helpers
```

## Features

- **Automatic group registration** when bot is added
- **11 moderation filters** (flood, spam, links, emojis, bad words, …)
- **Configurable actions** per filter: ignore / delete / warn / mute / kick / ban
- **Warning system** with auto-punishment at configurable limit
- **Admin commands**: /ban, /unban, /mute, /unmute, /warn, /resetwarns, /del, /pin, /unpin, /info
- **Welcome messages** with {first_name} {username} {group_name} placeholders
- **Per-group settings** via inline keyboard dashboard
- **Statistics** (members, messages, deletions, bans)
- **Audit log** of all moderation events

## Database Tables

| Table | Purpose |
|-------|---------|
| users | All known Telegram users |
| groups | Registered groups/supergroups |
| channels | Registered channels |
| admins | Per-group bot admin grants |
| group_settings | Per-group configuration |
| filters | Per-group filter enable/action |
| warnings | Warning counters per user per group |
| logs | Audit trail of all events |
| statistics | Daily counters per group |

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| TELEGRAM_BOT_TOKEN | ✅ | From @BotFather |
| DATABASE_URL | ✅ | Auto-provided by Replit |
| LOG_LEVEL | ❌ | INFO (default) |

## Adding the Bot to a Group

1. Add `@YourBot` to your group
2. Make it **Administrator** with: Delete Messages, Ban Users, Restrict Members, Pin Messages
3. Open a private chat with the bot and send `/start`
4. Select your group from the dashboard
