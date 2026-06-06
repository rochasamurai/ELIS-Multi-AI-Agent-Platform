# DISCORD_ROUTING_REPAIR_PROPOSAL_V1

**Date:** 2026-06-04
**Author:** ELIS Supervisor
**Classification:** `DISCORD_CONNECTOR_DOWN` / `DISCORD_APPLICATION_ID_RESOLUTION_FAILURE` / `PM_THREAD_NOT_IN_CHANNEL_ALLOWLIST`

---

## 1. Config Files and Paths

| Concern | Config Path | File |
|---|---|---|
| Discord bot token | `channels.discord.token` | `/home/samurai/.openclaw/openclaw.json` |
| Discord application ID | `channels.discord.applicationId` (not set — auto-resolved) | `/home/samurai/.openclaw/openclaw.json` |
| Guild allowlist | `channels.discord.guilds.1485030291813830898.channels` | `/home/samurai/.openclaw/openclaw.json` |
| Thread bindings | `channels.discord.threadBindings.spawnSubagentSessions` | `/home/samurai/.openclaw/openclaw.json` |
| Gateway env | `DISCORD_BOT_TOKEN` / `DISCORD_TOKEN` | `/home/samurai/.openclaw/.env` |

## 2. Current Values (Redacted)

### Discord Token
- **Config:** `"${DISC...KEN}"` (env var reference)
- **Env vars present:** `DISCORD_BOT_TOKEN=yes`, `DISCORD_TOKEN=yes`
- **Status:** Returned `401: Unauthorized` from Discord API `/users/@me/guilds`

### Application ID
- **Config:** **Not set** — OpenClaw auto-resolves via Discord API call to `/users/@me`
- **Failure:** Auto-resolution fails because the token returns 401 on all API calls, including the application ID lookup

### Guild Allowlist (`1485030291813830898`)
| Channel ID | Name | Users |
|---|---|---|
| `1485030292690309132` | #elis-pm | `1485180911619408014` (Carlos) |
| `1496871804864565339` | (unnamed) | `1485180911619408014` |
| `1494725349261709343` | Home | `1485180911619408014` |

**NOT in allowlist:** `1512187256578769097` (#pe-ops-github-skills-01)

### Thread Bindings
- `spawnSubagentSessions: true` — threads auto-spawn subagent sessions
- `groupPolicy: allowlist` — only channels in the guild allowlist are routed to agents

### Gateway Log Evidence (last 5 minutes)
```
[discord] channel resolve failed; using config entries
  → Discord API /users/@me/guilds failed (401): 401: Unauthorized
[discord] channel exited: Failed to resolve Discord application id
[discord] auto-restart attempt N/10 in Xs
```
Discord is in an **auto-restart loop** — failing every attempt with the same 401 error.

## 3. Proposed Minimal Repair

### Step A — Fix Discord Token (PRIMARY)
The root cause is the bot token returning `401: Unauthorized`. This must be resolved first — without a valid token, no Discord messages reach any agent.

**Action:** Verify/refresh the Discord bot token in the Discord Developer Portal.
- Go to https://discord.com/developers/applications
- Select the ELIS bot application
- Navigate to Bot → Token → Reset Token (if needed) or verify current token
- Update `DISCORD_BOT_TOKEN` in `/home/samurai/.openclaw/.env`
- **Owner:** Carlos (Discord Developer Portal access required)

### Step B — Set Explicit Application ID (RECOMMENDED)
To prevent future `Failed to resolve Discord application id` errors (which block the entire Discord connector even when the token is valid but the API is slow), set the application ID explicitly.

**Action:** Add `channels.discord.applicationId` to config:
```
openclaw config set channels.discord.applicationId "<DISCORD_APPLICATION_ID>"
```
The application ID can be found in the Discord Developer Portal under General Information → Application ID.

### Step C — Add Thread to Allowlist
Add `#pe-ops-github-skills-01` thread ID `1512187256578769097` to the guild channel allowlist.

**Proposed config patch:**
```json
{
  "channels": {
    "discord": {
      "guilds": {
        "1485030291813830898": {
          "channels": {
            "1512187256578769097": {
              "users": ["1485180911619408014"]
            }
          }
        }
      }
    }
  }
}
```
Applied via: `openclaw config patch --stdin` (merge mode — preserves existing channels)

### Step D — Restart Gateway
After token fix and config changes:
```bash
openclaw gateway restart
```

### Summary of Changes

| # | Path | Action | Before | After |
|---|---|---|---|---|
| A | `DISCORD_BOT_TOKEN` env | Refresh token | 401 invalid | Valid token |
| B | `channels.discord.applicationId` | Set explicitly | (auto-resolve, fails) | `<app_id>` |
| C | `channels.discord.guilds.1485030291813830898.channels.1512187256578769097` | Add entry | absent | `{users: ["1485180911619408014"]}` |
| D | Gateway | Restart | — | — |

## 4. Validation Plan

1. **Config validation:** `openclaw config validate` — must pass
2. **Channel status:** `openclaw channels status` — Discord must show `running, connected`
3. **Gateway logs:** `journalctl --user -u openclaw-gateway.service -f` — no 401 or application ID errors
4. **PM receives test message:** Carlos sends `@ELIS PM /status` in `#pe-ops-github-skills-01`
5. **PM responds:** Within 30s, PM should acknowledge and respond
6. **No access expansion:** Verify only Carlos (`1485180911619408014`) can trigger PM in this thread; other users blocked by `users` field

## 5. Rollback Plan

### Backup
```bash
cp /home/samurai/.openclaw/openclaw.json /home/samurai/.openclaw/openclaw.json.bak.$(date +%Y%m%d-%H%M%S)-pre-discord-repair
```

### Rollback Actions
1. Restore config: `cp <backup> /home/samurai/.openclaw/openclaw.json`
2. Revert `.env` token if changed: restore previous token value
3. Restart: `openclaw gateway restart`
4. Health check: `openclaw channels status`, verify gateway reachable

### Rollback Health Checks
- `openclaw config validate` — must pass
- `openclaw status --json` — gateway reachable, PM heartbeat active
- Discord channel may remain disconnected if token is the cause (expected after rollback)

## 6. Risks

### Risk 1 — Token Is the Root Cause
**Probability:** HIGH. The `401: Unauthorized` on `/users/@me/guilds` is a definitive token rejection. The application ID resolution failure is a **symptom**, not the cause.

**Mitigation:** Step A is the primary fix. Steps B and C are hardening and routing fixes that depend on A working first.

### Risk 2 — Thread ID in Channel Allowlist
**Probability:** LOW-MEDIUM. The schema accepts arbitrary string keys under `guilds.<guildId>.channels`. Discord treats thread IDs as channel-like entities. However, OpenClaw's Discord plugin may have thread-specific routing logic that differs from channel routing.

**Mitigation:** If adding the thread ID directly doesn't work, the parent channel of `#pe-ops-github-skills-01` must be identified and added instead. The PM session metadata shows the thread was previously reachable (the session was created), suggesting the parent channel IS in the allowlist or was previously configured differently.

**Note:** The thread `1512187256578769097` was created under a parent channel. The parent channel ID is NOT in the current allowlist. This means either:
- The allowlist was tightened after the thread was created
- The thread was created via a different mechanism (e.g., before `groupPolicy: allowlist` was enabled)
- The parent channel was previously in the allowlist and was removed

### Risk 3 — Gateway Restart Affects Active Agents
**Probability:** MEDIUM. All agents (PM and 18 PEs) will briefly lose connectivity during restart. Sessions are preserved.

**Mitigation:** Restart takes < 10 seconds. Heartbeats resume automatically. No data loss. Schedule during a quiet period.

### Risk 4 — Token Refresh Requires Discord Developer Portal
**Probability:** CERTAIN. The bot token can only be managed through the Discord Developer Portal. This requires Carlos's Discord account with application ownership.

**Mitigation:** Carlos must perform this step. Supervisor cannot automate it.

### Risk 5 — Application ID Changes on Token Reset
**Probability:** LOW. The application ID is a stable identifier tied to the Discord application, not the bot token. It does not change when the token is reset.

**Mitigation:** Step B can be deferred until the application ID is confirmed from the Developer Portal.

---

## Recommended Execution Order

1. **Carlos verifies/refreshes Discord bot token** in Developer Portal and updates `.env`
2. **Carlos provides Discord Application ID** from Developer Portal → General Information
3. **Supervisor applies Steps B, C, D** (config changes + restart)
4. **Validation** as per Section 4
5. If validation fails, **rollback** as per Section 5

---

**Hard boundaries observed:**
- No secrets exposed
- No config mutated
- No agents dispatched
- No GitHub actions
- No runtime config changes beyond proposal scope
- Read-only proposal only