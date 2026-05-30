# A2A Production Risk and Rollback Plan — PE-OPS-A2A-PRODUCTION-02

> Gate 1 planning document — read-only discovery pass.
> Implementer: infra-impl-a
> Date: 2026-05-30
> Status: Gate 1 — no implementation has occurred.

---

## 1. Rollback posture

The ELIS A2A production backbone is designed as a **purely additive layer**. The
existing Discord/session routing path remains operational at all times and is the
authoritative fallback. A2A is enabled only after explicit PO approval, and every
production cutover step is independently reversible.

Baseline rollback posture (applies throughout all phases):
- Discord/session routing is the operational fallback for all agent communication.
- A2A routing is disabled by default and gated on explicit PO enablement.
- No destructive migration is performed in any phase.
- The Phase-1 runtime local transport (`/tmp/elis_a2a/`) remains available as a
  further fallback even after the HTTP gateway is deployed.

---

## 2. Risk register

### R-01: Gateway loopback binding failure

| Field | Detail |
|-------|--------|
| Description | `a2a-gateway.js` binds to a non-loopback interface (e.g. `0.0.0.0`) due to misconfiguration or Node.js default |
| Likelihood | Low — spec requires explicit `127.0.0.1` binding with startup rejection on any other interface |
| Impact | High — external exposure of agent messaging bus; classified as security incident |
| Mitigation | Gateway startup check: if `server.address().address !== '127.0.0.1'`, log `[ERROR] Non-loopback binding detected — refusing to start` and `process.exit(1)`. Integration test verifies binding address before any message test. |
| Rollback | Stop gateway process; remove `/opt/elis/a2a/a2a-gateway.js`; revert to file-based transport |
| Rollback blocker? | No — gateway is not a daemon; stopping it restores file-transport-only operation immediately |

### R-02: Port 24001 conflict

| Field | Detail |
|-------|--------|
| Description | Port `24001` on `127.0.0.1` is already in use by another process on elis-server |
| Likelihood | Low — port reserved for ELIS A2A per spec; unlikely to conflict |
| Impact | Medium — gateway fails to start; A2A routing unavailable |
| Mitigation | Phase A pre-condition check: `ss -tlnp | grep 24001` before gateway is deployed. If occupied, stop and report to PM/PO for resolution. |
| Rollback | File-transport-only path remains active; no rollback of code required |
| Rollback blocker? | No |

### R-03: Message durability failure (persistent mailbox path issue)

| Field | Detail |
|-------|--------|
| Description | `/opt/elis/a2a/mailboxes/` path is not writable, or filesystem permissions prevent message file creation |
| Likelihood | Low — mitigated by Phase A ownership/permission check before activation |
| Impact | Medium — message delivery silently fails or raises unhandled exception |
| Mitigation | Phase A check: verify directory is writable by gateway process user before accepting first message. Transport falls back to `/tmp/elis_a2a/` if persistent path is unavailable. |
| Rollback | Remove persistent mailbox path; revert `_MAILBOX_ROOT` in `a2a_local_transport.py` to `/tmp/elis_a2a/` |
| Rollback blocker? | No |

### R-04: OpenClaw config corruption

| Field | Detail |
|-------|--------|
| Description | Phase E config update to `~/.openclaw/openclaw.json` corrupts the live config, breaking OpenClaw agent dispatch |
| Likelihood | Low — mitigation: config must be read-then-patch (never overwrite); Supervisor must verify gateway and config after each change |
| Impact | Critical — all OpenClaw agent sessions could be disrupted |
| Mitigation | Before editing: `cp ~/.openclaw/openclaw.json ~/.openclaw/openclaw.json.bak.$(date +%Y%m%d%H%M%S)`. Patch only the A2A routing block; verify JSON syntax with `python3 -m json.tool` before writing. Requires Supervisor sign-off. |
| Rollback | `cp ~/.openclaw/openclaw.json.bak.<timestamp> ~/.openclaw/openclaw.json`; restart gateway only (not OpenClaw). |
| Rollback blocker? | Only if backup was not taken. Backup is mandatory before any config change. |

### R-05: Contamination from PE-OPS-A2A-PRODUCTION-01

| Field | Detail |
|-------|--------|
| Description | Code, commits, or plans from the contaminated PE-01 branches enter this PE branch via cherry-pick, rebase, or copy |
| Likelihood | Low — forbidden by PE_TASK.md; hard stop in all phases |
| Impact | High — PE result would be contaminated and invalidated |
| Mitigation | Scope gate run before every commit: `git diff --name-status origin/main..HEAD`. Forbidden commits (c4e5754, b550d9e, e7ffbb2) must never appear in git log. |
| Rollback | If contamination detected: stop immediately, report to PM, do not push; PM must rebase or re-open PE from clean baseline |
| Rollback blocker? | No — contamination can be caught before push via scope gate |

### R-06: Gateway message queue memory growth

| Field | Detail |
|-------|--------|
| Description | In-memory per-agent message queues grow unboundedly if agents do not poll or receive messages |
| Likelihood | Medium — agents may go offline; messages will accumulate |
| Impact | Low to Medium — elis-server memory pressure if left unmonitored |
| Mitigation | TTL enforcement: messages with `ttl_seconds` exceeded since `timestamp` are purged from the queue on every enqueue and dequeue cycle. Default TTL is 300 s. Supervisor diagnostic query can inspect queue depth. |
| Rollback | Restart gateway (clears in-memory queues); persistent mailbox not affected |
| Rollback blocker? | No |

### R-07: Durable log unbounded growth

| Field | Detail |
|-------|--------|
| Description | Append-only dispatch log at `/opt/elis/a2a/logs/dispatch.log` grows without bound |
| Likelihood | Medium — A2A is a coordination bus; messages will accumulate over time |
| Impact | Low — disk space on elis-server |
| Mitigation | Daily log rotation via `logrotate` or gateway-internal rotation (new file per day; retain 30 days). Log format: one JSON line per message event. |
| Rollback | Stop gateway; rotate or truncate log manually; restart gateway |
| Rollback blocker? | No |

### R-08: Node.js dependency unavailability

| Field | Detail |
|-------|--------|
| Description | `node` < 18 on elis-server, or `npm install ws` fails due to network restrictions |
| Likelihood | Low — elis-server has `node v22.22.0` (verified via runtime environment) |
| Impact | Medium — gateway cannot start; implementation blocked |
| Mitigation | Phase A pre-condition: `node --version` and `npm ls ws` checks before any code is written. Alternative: use built-in `node:http` module for polling-only mode (no `ws` dependency) as a fallback. |
| Rollback | File-transport-only path remains active; gateway simply does not deploy |
| Rollback blocker? | No |

### R-09: Dispatch provenance proof missing or incomplete

| Field | Detail |
|-------|--------|
| Description | A2A-dispatched agent result does not include a filled DISPATCH_PROVENANCE_PROOF_V1 |
| Likelihood | Medium — provenance proof must be explicitly included in every result |
| Impact | High — PM rejects result without review per PE_TASK.md validity rule |
| Mitigation | Gate 2 acceptance criterion AC-8 explicitly requires DISPATCH_PROVENANCE_PROOF_V1 fields in gateway log for every dispatch. Implementer checks proof before submitting any Gate 2 result. |
| Rollback | No code rollback required — provenance proof is a documentation/reporting obligation |
| Rollback blocker? | No |

---

## 3. Rollback procedures by phase

### 3.1 Rollback from Phase B (gateway deployed, not yet running)

```bash
# Remove gateway files — does not affect any running process
rm -f /opt/elis/a2a/a2a-gateway.js \
      /opt/elis/a2a/a2a-gateway.sh \
      /opt/elis/a2a/package.json
# Verify no gateway process running
lsof -i :24001 || echo "Port 24001 free"
```

Outcome: system returns to file-transport-only mode. No service restart required.

### 3.2 Rollback from Phase C (persistent mailbox active)

```bash
# Revert _MAILBOX_ROOT in a2a_local_transport.py to /tmp/elis_a2a/
# (git revert the Phase C commit or manual edit)
# Existing messages in /opt/elis/a2a/mailboxes/ can be archived or left in place
```

Outcome: transport reverts to ephemeral `/tmp/elis_a2a/`. Persistent mailbox is inert
(no code reads it). No service restart required.

### 3.3 Rollback from Phase D (integration tests added)

Tests are additive only. Remove `tests/test_a2a_gateway.py` if needed. CI passes on
`test_a2a_local_transport.py` alone.

### 3.4 Rollback from Phase E (OpenClaw config updated, gateway running)

```bash
# 1. Stop the gateway
kill -TERM $(cat /opt/elis/a2a/gateway.pid 2>/dev/null) 2>/dev/null || \
  pkill -f a2a-gateway.js

# 2. Restore OpenClaw config from backup
cp ~/.openclaw/openclaw.json.bak.<timestamp> ~/.openclaw/openclaw.json

# 3. Verify JSON is valid
python3 -m json.tool ~/.openclaw/openclaw.json > /dev/null && echo "Config OK"

# 4. Verify port is free
lsof -i :24001 || echo "Port 24001 free"
```

Outcome: OpenClaw reverts to Discord/session routing. A2A routing is disabled.
No restart of OpenClaw daemon is required (config is hot-reloaded or takes effect on
next session start — confirm with Supervisor before proceeding).

### 3.5 Full rollback (revert entire PE from git)

```bash
git revert <gate-2-commit-sha>
# Or:
git revert --no-commit HEAD~N  # where N = number of Gate 2 commits
git commit -m "revert(PE-OPS-A2A-PRODUCTION-02): rollback A2A production deployment"
```

Outcome: all PE-02 code changes are reverted. Local file transport on
`/tmp/elis_a2a/` remains available (it was merged in PE-OPS-A2A-RUNTIME-01 and is
unaffected). No service restart, no config revert, no database migration required.

---

## 4. Rollback triggers

The following conditions trigger immediate rollback:

| Trigger | Required action |
|---------|----------------|
| Non-loopback binding detected at gateway startup | Stop gateway, report to PM, do not re-deploy without config fix |
| OpenClaw agent sessions disrupted after config change | Restore backup config immediately (§3.4) |
| A2A message containing a secret, token, or credential | Stop gateway, report to PM/PO as security incident |
| Scope gate detects contamination from PE-01 | Stop work, report to PM, do not push |
| CI failures on `test_a2a_local_transport.py` after Phase C changes | Revert Phase C changes; confirm tests pass before proceeding |
| `/opt/elis/a2a/` path permissions prevent writes | Pause Phase B/C; report to PM |

---

## 5. What rollback does NOT require

- No database or durable-log migration reversal (log is additive only)
- No secret rotation or credential change (no secrets are stored in A2A)
- No Hermes config rollback (Hermes is not modified by this PE)
- No CI workflow file rollback (CI workflows are not modified by this PE in Gate 1)
- No production cutover recovery task (rollback restores Discord/session routing as-is)

---

## 6. Evidence expectation

Rollback readiness is demonstrated by:
- Clean scope gate output before every commit
- Phase A pre-condition checks documented in Gate 2 HANDOFF.md
- OpenClaw config backup confirmed before Phase E
- `test_a2a_local_transport.py` CI green at all checkpoints

---

## 7. References

- `PE_TASK.md` — hard stops and constraints
- `docs/governance/ELIS_A2A_Production_Rollback.md` — baseline rollback posture
- `docs/governance/ELIS_A2A_Production_Security_Model.md` — security controls
- `docs/governance/ELIS_A2A_Runtime_Spec.md` §6 — runtime rollback approach
- `AGENTS.md` §2.4 — evidence-first reporting
- `A2A_Production_Plan.md` — phased implementation plan (same PE)
