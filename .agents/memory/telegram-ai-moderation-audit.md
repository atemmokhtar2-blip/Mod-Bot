---
name: Telegram AI moderation audit patterns
description: Design choices for the AI-moderation Telegram bot's key validation, health status, dedup cache, and profile/edited-message coverage — useful before extending AI protection features there again.
---

- Live Gemini key validation: call a minimal real `generate_content` request with the candidate key *before* persisting it (both `/addaikey` and the inline wizard). Never save on failure. A genuinely invalid key returns HTTP 400 `API key not valid` — safe to surface directly as the rejection reason.
  **Why:** the bot previously saved keys unconditionally and only discovered they were bad on the next real moderation call, silently degrading protection.

- Per-key 🟢/🟡/🔴 health status is *derived*, not stored — no new DB column needed. Logic: disabled → 🔴; last event was a failure whose `last_error` mentions quota/429/resource_exhausted → 🟡; last event was any other failure → 🔴; otherwise (success or never used) → 🟢.
  **How to apply:** reuse `AIProviderKey.health_status()` rather than adding a status column if this needs to be re-derived elsewhere.

- aiogram's `Router.edited_message` decorator exists and behaves like `.message` — routing an edited message through the exact same filter handler function closes the "post something clean, edit in the violation" bypass with minimal code (just an extra thin wrapper handler that calls the same function).

- Duplicate/repeated AI calls (flood of identical text, same image re-sent) are deduplicated with a short-TTL (2 min) in-process cache keyed by `sha256(payload)`, scoped per analysis kind (text/image/links/profile/description). Keeps behavior correct for edits (new content = new key) while avoiding wasted Gemini calls on spam floods.

- Username/display-name and group-description screening needed *new* trigger points — Telegram never pushes per-message profile data. Hooked into: chat_member join event (username+display name) and my_chat_member "bot added to group" event (fetches `bot.get_chat().description` once). A bot cannot edit a group's description via Bot API, so a description violation is logged only, not auto-acted.
