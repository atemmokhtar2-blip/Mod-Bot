# Deployment Guide — Vercel

This guide walks you through deploying the Arabic Telegram Moderation Bot and its API server to **Vercel**.

---

## Architecture on Vercel

| URL path            | Handler                     | Runtime      |
|---------------------|-----------------------------|--------------|
| `POST /api/webhook` | `api/webhook.py`            | Python 3.12  |
| `GET  /api/webhook` | `api/webhook.py`            | Python 3.12  |
| `/api/*`            | `api/[...slug].ts`          | Node.js      |
| `/telegram/webhook` | rewrite → `/api/webhook`    | —            |

- **Telegram bot** runs as a serverless Python function, invoked per-update via webhook.
- **Express API** runs as a serverless Node.js function, invoked per-request.
- No long-running processes — Vercel's serverless model handles everything.

---

## Prerequisites

| Requirement | Notes |
|---|---|
| **Vercel account** | vercel.com — free Hobby tier is sufficient |
| **Vercel CLI** | `npm i -g vercel` (optional — can use the dashboard instead) |
| **External PostgreSQL** | Replit's internal DB is not reachable from Vercel. Use [Neon](https://neon.tech) (recommended, free tier) or [Supabase](https://supabase.com) |
| **Telegram Bot Token** | From [@BotFather](https://t.me/BotFather) |

---

## Step 1 — Set up an External PostgreSQL Database

### Option A: Neon (recommended)

1. Sign up at [neon.tech](https://neon.tech).
2. Create a project → copy the **Connection string** (pooled, `postgresql://...`).
3. That string is your `DATABASE_URL`.

### Option B: Supabase

1. Sign up at [supabase.com](https://supabase.com).
2. Create a project → Settings → Database → **Connection string (URI)**.
3. Use the **Transaction** pooler URI for serverless.

---

## Step 2 — Deploy to Vercel

### Using the Vercel Dashboard

1. Go to [vercel.com/new](https://vercel.com/new) and import this Git repository.
2. Vercel detects the `vercel.json` automatically.
3. In **Environment Variables**, add:

| Variable | Value |
|---|---|
| `TELEGRAM_BOT_TOKEN` | Your bot token from @BotFather |
| `DATABASE_URL` | Your external PostgreSQL connection string |
| `WEBHOOK_SECRET` | Random secret (see below) |
| `NODE_ENV` | `production` |
| `LOG_LEVEL` | `INFO` |

4. Click **Deploy**.

### Generate a WEBHOOK_SECRET

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

Copy the output and set it as `WEBHOOK_SECRET` on Vercel **and** keep it for Step 3.

### Using the Vercel CLI

```bash
# Login
vercel login

# Deploy (follow the prompts)
vercel --prod

# Set secrets
vercel env add TELEGRAM_BOT_TOKEN production
vercel env add DATABASE_URL production
vercel env add WEBHOOK_SECRET production
vercel env add NODE_ENV production
```

---

## Step 3 — Register the Telegram Webhook

After Vercel deploys, run this **once** to tell Telegram where to send updates:

```bash
TELEGRAM_BOT_TOKEN="your-token" \
WEBHOOK_SECRET="your-secret" \
python scripts/setup_webhook.py \
  --url https://YOUR-APP.vercel.app/api/webhook \
  --secret your-secret
```

Replace `YOUR-APP` with your actual Vercel project URL.

You should see:
```
✅  Webhook registered: https://YOUR-APP.vercel.app/api/webhook
🔒  Secret token is active — only Telegram can reach your endpoint.
```

---

## Step 4 — Verify

Test the API health endpoint:
```bash
curl https://YOUR-APP.vercel.app/api/healthz
# → {"status":"ok"}
```

Send a message to your bot in Telegram and confirm it responds.

Check webhook status:
```bash
curl "https://api.telegram.org/botYOUR-TOKEN/getWebhookInfo"
```

---

## Switching Back to Polling (Replit)

If you want the Replit bot to handle updates instead:

```bash
# Delete the Vercel webhook so Telegram stops sending to Vercel
TELEGRAM_BOT_TOKEN="your-token" python scripts/setup_webhook.py --delete

# Then start polling on Replit
# The `Telegram Moderation Bot` workflow handles this automatically.
```

> ⚠️ Only one mode can be active at a time — polling and webhook are mutually exclusive.

---

## Environment Variables Reference

| Variable | Required | Description |
|---|---|---|
| `TELEGRAM_BOT_TOKEN` | ✅ | Bot token from @BotFather |
| `DATABASE_URL` | ✅ | External PostgreSQL connection string |
| `WEBHOOK_SECRET` | Recommended | Secret token for request verification |
| `NODE_ENV` | ✅ | Set to `production` |
| `LOG_LEVEL` | Optional | `DEBUG` / `INFO` / `WARNING` (default: `INFO`) |

---

## Database Migrations

Migrations run automatically on **every cold start** of the webhook function via `init_db()`. All migrations are idempotent (`IF NOT EXISTS`, `ON CONFLICT DO NOTHING`), so re-running them is safe.

For the API server's Drizzle ORM schema, run migrations manually:
```bash
# (from project root, targeting your production DATABASE_URL)
pnpm --filter @workspace/api-server drizzle-kit push
```

---

## Troubleshooting

| Problem | Solution |
|---|---|
| Bot doesn't respond | Check `getWebhookInfo` for `last_error_message`; verify `WEBHOOK_SECRET` matches |
| 403 on webhook POST | `WEBHOOK_SECRET` mismatch — re-run `setup_webhook.py` with the correct value |
| DB connection error | Verify `DATABASE_URL` points to an external (non-Replit) PostgreSQL |
| Cold start timeout | Neon's free tier may hibernate — first request may take 2–3 s; subsequent ones are fast |
| Python import error | Ensure `requirements.txt` at root lists all bot dependencies |

---

## Project Layout (Vercel-relevant files)

```
vercel.json                ← Vercel configuration (routing, runtimes, functions)
requirements.txt           ← Python deps for api/webhook.py
.env.example               ← All required environment variables
api/
  webhook.py               ← Bot webhook serverless function (Python 3.12)
  [...slug].ts             ← Express API serverless catch-all (Node.js)
artifacts/
  telegram-bot/
    bot/setup.py           ← Shared Bot + Dispatcher factory
    ...
  api-server/
    src/app.ts             ← Express app (imported by api/[...slug].ts)
    ...
scripts/
  setup_webhook.py         ← One-time webhook registration helper
```
