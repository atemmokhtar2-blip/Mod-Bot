---
name: Encrypt-at-rest secrets with a precomputed display mask
description: Pattern for storing user-supplied API keys encrypted while still showing a masked preview, without ever decrypting for display.
---

When a bot/app owner supplies a third-party API key that must be stored
encrypted (e.g. Fernet) but the UI still needs to show a masked preview like
`AIza**************AB12`:

Compute the mask from the plaintext once, at insertion time, and store it in
its own plain column (e.g. `key_mask`) alongside the encrypted value.

**Why:** if masking is derived by decrypting on every display/list request,
every read path becomes a place that touches plaintext — more surface for
accidental logging/exposure, and it couples display code to the decryption
key's availability. Precomputing the mask means normal list/status/UI code
never needs to decrypt at all; decryption happens only at the single point
where the plaintext key is actually sent to the third-party API.

**How to apply:** on insert — `mask = compute_mask(plaintext); ciphertext =
encrypt(plaintext); store(ciphertext, mask)`. On any legacy-data migration
that starts encrypting previously-plaintext rows, do the same masking step
before encrypting, and make the migration idempotent by checking whether a
row already looks encrypted (e.g. "does decrypt succeed with the current
key") rather than relying on a boolean flag that could drift.
