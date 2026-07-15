---
name: RC1 AI dual-gate bug
description: Why the ai_text/ai_image filter rows must NOT gate the AI check functions, and what the correct gates are.
---

`_run_ai_text_check`, `_run_ai_image_check`, and `_run_ai_links_check` in
`message_filter.py` each had TWO gates that both had to be True:

1. `settings.ai_enabled = True` — set via the AI settings panel
2. The `ai_text` / `ai_image` Filter row `enabled = True` — set via the protection filters panel

These rows default to `False` and `_ensure_group_filters` keeps them `False`.
The AI settings panel (`cb_v4_ai_toggle`) only sets `settings.ai_enabled` — it never
touches the filter rows. Result: AI never fires even when the owner enables it.

**Why:** The filter-row enabled flag was designed for deterministic filters. AI moderation
is controlled entirely via `GroupSettings` (ai_enabled, ai_analyze_messages/images/links)
and the multi-action flags (ai_action_delete/warn/mute/ban). The filter rows for ai_text
and ai_image serve no additional purpose — their action column is also not used by the AI
pipeline (which uses ai_action_* instead).

**How to apply:** Remove the filter-row check from all three AI check functions. The correct
and sufficient gates are:
- `settings.ai_enabled` — master AI switch
- `settings.ai_analyze_messages` / `settings.ai_analyze_images` / `settings.ai_analyze_links` — per-type switch
Do NOT add filter-row gates for AI checks in future code.
