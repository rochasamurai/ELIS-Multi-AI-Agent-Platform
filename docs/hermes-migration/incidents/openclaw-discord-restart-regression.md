# OPENCLAW_DISCORD_POST_RESTART_REGRESSION_REPORT_V1

**Date:** 2026-06-04 23:16 UTC
**Author:** ELIS Supervisor
**Classification:** `OPENCLAW_CONFIG_SERIALIZATION_MANGLED_DISCORD_TOKEN` (primary) / `OPENCLAW_DISCORD_REGRESSION_AFTER_GATEWAY_RESTART` / `OPENCLAW_DISCORD_CONNECTOR_DOWN`

---

## Executive Summary

**The Discord outage was caused by the Supervisor's `openclaw config set` command, which silently mangled the Discord bot token reference during config serialization.** This is a confirmed config-write regression, not an independent token expiry or env-loading failure.

## Root Cause Chain

```
Supervisor runs: openclaw config set agents.defaults.timeoutSeconds 300
  → OpenClaw writes config to disk
  → Secret-handling code redacts channels.discord.token value
  → "${DISCORD_BOT_TOKEN}"  →  "${DISC...KEN}"  (TRUNCATED)
  → Hot reload detects TWO changes: timeoutSeconds + channels.discord.token
  → Gateway restarts Discord channel with mangled token "${DISC...KEN}"
  → OpenClaw tries to resolve env var "DISC...KEN" — does not exist
  → Discord API call fails: 401 Unauthorized
  → applicationId auto-resolution fails (same 401)
  → Discord enters auto-restart loop (still ongoing)
```

## 1. Config Diff — The Smoking Gun

**Backup** (`openclaw.json.bak`):
```
channels.discord.token: "${DISCORD_BOT_TOKEN}"
```

**Current** (`openclaw.json`):
```
channels.discord.token: "${DISC...KEN}"
```

### Only TWO keys changed across the entire config:

| Key | Backup | Current | Caused by |
|---|---|---|---|
| `agents.defaults.timeoutSeconds` | `240` | `300` | ✅ Intentional |
| `channels.discord.token` | `${DISCORD_BOT_TOKEN}` | `${DISC...KEN}` | ❌ **Unintentional mangling** |

The `channels.discord.token` change was NOT in the Supervisor's authorised scope. It was a side effect of OpenClaw's config serialization.

## 2. Timeline — Exact Sequence

| Time (UTC) | Event | Process |
|---|---|---|
| 22:10 — 22:39 | PM session `agent:pm:discord:channel:1512187256578769097` stalled but **Discord was connected** | PID 142942 |
| **22:40** | Supervisor runs `openclaw config set agents.defaults.timeoutSeconds 300` | Supervisor |
| 22:40 | Config written: token mangled `${DISCORD_BOT_TOKEN}` → `${DISC...KEN}` | OpenClaw CLI |
| **22:45:27** | `[reload] config change detected (agents.defaults.timeoutSeconds, channels.discord.token)` | PID 142942 |
| **22:45:28** | `[gateway/channels] restarting discord channel` | PID 142942 |
| **22:45:28** | `Config last-known-good promotion skipped: redacted secret placeholder at channels.discord.token` | PID 142942 |
| **22:45:28** | `Discord API /users/@me/guilds failed (401): 401: Unauthorized` | PID 142942 |
| **22:45:28** | `[discord] channel exited: Failed to resolve Discord application id` | PID 142942 |
| 22:45:28+ | Discord auto-restart loop (1/10, 2/10, ...) — all 401 | PID 142942 |
| 22:45:46 | Gateway fully restarted with mangled config | PID 205665 |
| 22:45:51 | Same `last-known-good skipped: redacted secret placeholder` | PID 205665 |
| 22:45:51+ | Same Discord 401 loop — still ongoing | PID 205665 |

### Discord was working BEFORE 22:45:27

- Zero Discord disconnect/401 errors in logs between 18:00 and 22:45:27
- PM was actively processing in channel `1512187256578769097`
- The only Discord-related log line was a bootstrap truncation warning (normal operation)

## 3. Service Environment — All Correct

| Check | Result |
|---|---|
| Process | PID 205665, user `samurai` |
| Env file | `/home/samurai/.openclaw/gateway.systemd.env` (878 bytes, Apr 25) |
| `DISCORD_BOT_TOKEN` in env file | ✅ Present |
| `DISCORD_BOT_TOKEN` in PID env | ✅ Present (confirmed via `/proc/205665/environ`) |
| Env var name match | ✅ Both `.env` and `gateway.systemd.env` use `DISCORD_BOT_TOKEN` |
| Working directory | `/home/samurai` |

**The environment is healthy.** The `DISCORD_BOT_TOKEN` env var exists and is loaded by both systemd and the running process. The problem is purely in the config file: the reference was mangled from `${DISCORD_BOT_TOKEN}` to `${DISC...KEN}`.

## 4. Token Validity

The actual `DISCORD_BOT_TOKEN` value in the env file starts with `MTQ4ND...` — which is a standard Discord bot token prefix (Base64-encoded). The token was NOT tested directly against the Discord API (per hard boundaries), but:

- The 401 error began at the EXACT moment of the hot reload (22:45:28)
- No 401 errors existed before 22:45:27
- The token value in the env files has NOT changed (file mtime: Apr 25)
- The only thing that changed is the config reference from `${DISCORD_BOT_TOKEN}` to `${DISC...KEN}`

**Conclusion:** The token is almost certainly still valid. OpenClaw is simply resolving the wrong env var name (`DISC...KEN` instead of `DISCORD_BOT_TOKEN`).

## 5. Application ID Resolution

The `applicationId` auto-resolution fails because:
1. OpenClaw tries to call Discord API `/users/@me` to get the bot's application ID
2. This call uses the bot token for authentication
3. The token is `${DISC...KEN}` which resolves to nothing useful
4. Discord returns 401 → OpenClaw can't get the application ID
5. `Failed to resolve Discord application id`

This is a **symptom**, not the cause. Fixing the token reference will fix application ID resolution automatically.

## 6. Allowlist Assessment

`#pe-ops-github-skills-01` (channel `1512187256578769097`) is NOT in the guild channel allowlist. However:

- The PM was processing in this channel BEFORE the config mangling (stalled but receiving)
- This means the allowlist was NOT blocking messages before 22:45
- The thread was likely auto-created under a parent channel that IS allowed, or `threadBindings.spawnSubagentSessions` bypasses the channel-level allowlist for threads

**Assessment:** The allowlist is a **secondary concern**, not the primary blocker. Fix the token first, then verify whether messages reach the PM in this channel. If they do, no allowlist change is needed. If they don't, add the thread ID as proposed in `DISCORD_ROUTING_REPAIR_PROPOSAL_V1`.

## 7. Rollback Assessment

### Would rollback fix Discord?

**YES.** Restoring `/home/samurai/.openclaw/openclaw.json.bak` would:
1. Revert `timeoutSeconds` to 240 (acceptable — PE work completed)
2. Restore `${DISCORD_BOT_TOKEN}` → Discord would reconnect
3. No other config differences exist

**However**, a more targeted fix is available (see Section 8).

## 8. Probable Cause (Final)

| Classification | Confidence |
|---|---|
| **`OPENCLAW_CONFIG_SERIALIZATION_MANGLED_DISCORD_TOKEN`** | 🔴 **CONFIRMED** |
| `OPENCLAW_DISCORD_REGRESSION_AFTER_GATEWAY_RESTART` | 🟡 CONFIRMED — triggered by config mangling |
| `OPENCLAW_ENV_LOST_AFTER_RESTART` | ⚪ **RULED OUT** — env vars are present and correct |
| `OPENCLAW_APPLICATION_ID_RESOLUTION_REGRESSION` | 🟡 SYMPTOM — caused by token mangling |
| `PM_NOT_RECEIVING_MESSAGES` | 🟡 CONFIRMED — caused by Discord disconnect |
| Token expiry | ⚪ **RULED OUT** — env value unchanged since Apr 25; 401 started exactly at hot reload |

## 9. Minimal Repair Options

### Option A — Targeted Token Fix (RECOMMENDED)

Single-line patch to restore the token reference:

```bash
# Replace the mangled token reference with the correct env var
python3 -c "
import json
with open('/home/samurai/.openclaw/openclaw.json') as f:
    config = json.load(f)
config['channels']['discord']['token'] = '\${DISCORD_BOT_TOKEN}'
with open('/home/samurai/.openclaw/openclaw.json', 'w') as f:
    json.dump(config, f, indent=2)
    f.write('\n')
"
openclaw gateway restart
```

**Preserves:** `timeoutSeconds = 300`, all other config
**Changes:** Only `channels.discord.token` → back to `${DISCORD_BOT_TOKEN}`

### Option B — Full Rollback

```bash
cp /home/samurai/.openclaw/openclaw.json.bak /home/samurai/.openclaw/openclaw.json
openclaw gateway restart
```

**Preserves:** Nothing — full revert
**Changes:** `timeoutSeconds` back to 240, token back to `${DISCORD_BOT_TOKEN}`
**Downside:** Loses the timeout improvement

## 10. Preventative Recommendation

**Do not use `openclaw config set` on a live config that contains env-var-referenced secrets.** The serialization path may redact secret references. For future timeout adjustments or any config change, use direct JSON manipulation (Python `json.load`/`json.dump`) which preserves values exactly.

## 11. Hard Boundaries Observed

- ✅ No secrets printed
- ✅ No config mutated during diagnosis
- ✅ No gateway restarted
- ✅ No agents dispatched
- ✅ No GitHub actions
- ✅ Read-only diagnosis only

---

**Recommended action:** Authorise Option A (targeted token fix) — one line, preserves timeout improvement, restores Discord immediately.