---
name: Telegram Stars donations (aiogram 3)
description: How real Telegram Stars (XTR) payments are wired into an aiogram 3 bot without a payment provider.
---

For real Telegram Stars donations (currency `XTR`), `provider_token` must be an empty string in `bot.send_invoice` — Stars payments don't go through a third-party provider, unlike normal Telegram Payments.

**Why:** Passing a provider token (or omitting the currency check) causes `send_invoice` to fail or misroute the payment; Stars is a Telegram-native currency with `total_amount` already in whole Star units (no `/100` conversion like fiat).

**How to apply:** `pre_checkout_query` must always be answered (`ok=True` unless you have a real reason to reject) within Telegram's timeout, and the actual donation should only be persisted/thanked in the `message` handler that matches `F.successful_payment` — that's the only proof of payment. There is no native Telegram "payment cancelled" callback; the only cancel point a bot can offer is its own inline "cancel" button shown before the invoice is sent.
