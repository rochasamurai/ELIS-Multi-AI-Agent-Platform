# Token Overload Mitigation — Hermes/ELIS Operational Record

**PE:** PE-OPS-HERMES-TOKEN-OVERLOAD-01  
**Status:** Implemented and validated  
**Date:** 2026-06-05

---

## Problem

Fresh `/reset` sessions on the Hermes ELIS Supervisor (Discord-bound) were consuming 54k–66k input tokens. Target for routine operational calls is 5k–18k.

Root causes identified:

1. **Discord history backfill** — `history_backfill_limit: 50` re-injected up to 50 prior messages after `/reset`, recreating token overload
2. **Full tool schemas** — 36 tools with ~61KB of JSON schemas loaded into every prompt context
3. **Memory ceiling** — MEMORY.md at 99% capacity (1,195/1,200 chars) added marginal pressure

## Mitigations Applied

### 1. Discord history backfill limit

```yaml
# In ~/.hermes/config.yaml
discord:
  history_backfill_limit: 3   # reduced from 50
```

**Impact:** Largest single saving. Reduces post-reset context from 15–30k tokens of backfill to under 1k.

### 2. Tool search threshold

```yaml
# In ~/.hermes/config.yaml
tools:
  tool_search:
    threshold_pct: 2   # reduced from 10 (default)
```

**Impact:** When context window exceeds 2% (20k tokens for 1M context model), full tool schemas are replaced with a searchable index. Saves ~15k tokens of schema overhead on operational sessions.

### 3. Memory at healthy level

Memory consolidated from 1,195/1,200 chars (99%) to ~893/1,200 chars (74%) by merging redundant entries and removing re-discoverable facts to skills.

**Impact:** Modest (~200–300 tokens). More important as hygiene than raw savings.

## Results

| Before | After | Saving |
|---|---|---|
| 54k–66k input tokens | 5k–18k input tokens | ~48k tokens |

Fresh `/reset` sessions on the Supervisor now routinely land under 18k tokens. The `hermes prompt-size` tool confirms fixed costs at ~23k chars for the system prompt + skills index + tool schemas (with tool_search active).

## Hard Constraints (Not Performed)

- **No memory trim** — entries were consolidated, not deleted en masse
- **No `hermes doctor --fix`** — not run during this PE per PO directive

## Routine Token Ceiling

| Metric | Value |
|---|---|
| Ceiling (stop and classify TOKEN_OVERLOAD) | >25k input tokens |
| Target range | 5k–18k input tokens |
| Measurement tool | `hermes prompt-size --json` |

## Operational Monitoring

Run `hermes prompt-size --json` periodically to verify fixed costs remain stable. If token counts drift above 18k on routine calls, investigate before they reach 25k.

```bash
hermes prompt-size --json | python3 -c "
import json, sys
d = json.load(sys.stdin)
print(f'System: {d[\"system_prompt\"][\"chars\"]} chars')
print(f'Skills: {d[\"skills_index\"][\"chars\"]} chars')
print(f'Memory: {d[\"memory\"][\"chars\"]} chars')
print(f'Tools: {d[\"tools\"][\"count\"]} tools, {d[\"tools\"][\"json_bytes\"]} bytes')
"
```
