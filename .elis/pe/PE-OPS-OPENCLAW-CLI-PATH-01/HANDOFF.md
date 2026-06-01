# HANDOFF — PE-OPS-OPENCLAW-CLI-PATH-01

> Implementer slot: infra-impl-b
> Generated: 2026-06-01

---

## PE Identification

- **PE:** PE-OPS-OPENCLAW-CLI-PATH-01
- **Branch:** feature/pe-ops-openclaw-cli-path-01-fix-openclaw-binary-path-resolution
- **Base:** main
- **Implementer slot:** infra-impl-b
- **Validator slot:** infra-val-a

---

## Gate 1 — Diagnosis Evidence

**Root cause:** `~/.config/systemd/user/openclaw-gateway.service` had `PATH` with `/opt/openclaw/tools/node-v22.22.0/bin` appearing before `/opt/openclaw/bin`. Gateway-spawned agent shells inherited this stale `PATH`, so `which openclaw` resolved to `/opt/openclaw/tools/node-v22.22.0/bin/openclaw` (symlink → `openclaw.mjs`, v2026.4.21) instead of `/opt/openclaw/bin/openclaw` (bash wrapper → `entry.js`, v2026.5.27).

**Evidence collected:**

- `which openclaw` → `/opt/openclaw/tools/node-v22.22.0/bin/openclaw`
- `/opt/openclaw/tools/node-v22.22.0/bin/openclaw --version` → `2026.4.21`
- `/opt/openclaw/bin/openclaw --version` → `2026.5.27`
- `/opt/openclaw/bin/openclaw` content: bash wrapper calling `/opt/openclaw/tools/node/bin/node .../entry.js`
- `/opt/openclaw/tools/node-v22.22.0/bin/openclaw`: symlink → `../lib/node_modules/openclaw/openclaw.mjs`
- systemd unit `PATH` line (at Gate 1 read, ~23:22 on 2026-05-31): `/opt/openclaw/tools/node-v22.22.0/bin` appeared first, `/opt/openclaw/bin` was absent
- **Classification:** `SYSTEMD_USER_UNIT_PATH_PRECEDENCE` — stale binary version resolved due to `PATH` ordering in systemd unit

---

## Gate 2 — Supervisor Fix Evidence

- **Fix:** Supervisor prepended `/opt/openclaw/bin` to `PATH` in `~/.config/systemd/user/openclaw-gateway.service`
- **Backup taken:** `openclaw-gateway.service.bak.20260601-173315`
- **Supervisor executed:** `systemctl --user daemon-reload && systemctl --user restart openclaw-gateway`
- **Post-fix `PATH` line:** `Environment=PATH=/opt/openclaw/bin:/opt/openclaw/tools/node-v22.22.0/bin:/home/samurai/.local/bin:...`
- **Gate 2 verdict:** PASS (PO confirmed)

---

## Evidence Discrepancy Reconciliation

Gate 1 (PM read at ~23:22 on 2026-05-31) showed `/opt/openclaw/tools/node-v22.22.0/bin` first (no `/opt/openclaw/bin`). Supervisor at Gate 2 check found `/opt/openclaw/bin` already first in the file.

**Resolution:** file `mtime` shows the service file was last modified at `2026-05-31 23:40:40` — approximately 18 minutes after Gate 1 read. The file was corrected between Gate 1 and Supervisor's check.

**Classification:** `PRE_EXISTING_CORRECTION_BEFORE_SUPERVISOR_CHECK`. The running gateway still had the stale `PATH` in its environment (`PATH` is inherited at process start; editing the unit file does not affect a running process). Supervisor's `daemon-reload + restart` was still required and correct. No contradiction between Gate 1 and Gate 2 evidence; timeline fully reconciled.

---

## PM_ROLE_DISCOVERY_ERROR

During this PE, PM incorrectly concluded that no executable Supervisor agent was available because the Supervisor was absent from the OpenClaw agent list returned by the `sessions/list` API. This was an error.

**Classification:** `PM_ROLE_DISCOVERY_ERROR_OPENCLAW_AGENT_LIST_IS_NOT_ELIS_ROLE_REGISTRY`

**Correction:** The OpenClaw agent list reflects only sessions/agents registered within the OpenClaw gateway. The ELIS Supervisor operates via Hermes/platform channels and is not enumerated by this API. PM must not treat absence from the OpenClaw agent list as proof that an ELIS operational role does not exist. Future PEs must consult `CURRENT_PE.md` and the full ELIS role registry when determining who can execute elevated operations.

---

## Gate 2 (Supplementary) — Drop-in PATH Override Finding and Fix

### Finding

- **Path:** `~/.config/systemd/user/openclaw-gateway.service.d/10-path.conf`
- **Effect:** drop-in contains `Environment=PATH=` without `/opt/openclaw/bin`; applied after main unit file, overriding the fix
- **Classification:** `SYSTEMD_DROPIN_PATH_OVERRIDE_CAUSES_STALE_OPENCLAW_CLI`
- Running gateway PID 141458 `PATH` (from `/proc/141458/environ`): did not contain `/opt/openclaw/bin`

### Supervisor Fix

- **Backup:** `~/.config/systemd/user/openclaw-gateway.service.d/10-path.conf.bak.20260601T171624`
- **Edit:** prepended `/opt/openclaw/bin:/opt/openclaw/tools/node-v22.22.0/bin:` to `Environment=PATH=` in `10-path.conf`
- **Commands:** `systemctl --user daemon-reload && systemctl --user restart openclaw-gateway.service`
- **Result:** gateway active, PID 142663; running gateway `PATH` starts with `/opt/openclaw/bin`

### Supervisor Verification

- `which openclaw`: `/opt/openclaw/bin/openclaw`
- `openclaw --version`: `OpenClaw 2026.5.27`
- `openclaw agent --help | grep session-key`: `--session-key` present
- **Gate 2 verdict:** PASS (PO confirmed)

### Gate 1 vs Gate 2 Discrepancy — Complete Resolution

The earlier reconciliation (file `mtime` 2026-05-31 23:40:40) explained the main service file edit ~18 min after Gate 1. The drop-in finding completes the picture: the drop-in was the definitive cause of the stale `PATH` in the running gateway. Both findings are consistent and non-contradictory.

---

## Acceptance Criteria Checklist

- [x] Drop-in `10-path.conf` `PATH` override identified: `SYSTEMD_DROPIN_PATH_OVERRIDE_CAUSES_STALE_OPENCLAW_CLI`
- [x] Drop-in corrected by Supervisor; `daemon-reload + restart`; gateway `PATH` verified
- [x] Root cause identified: `SYSTEMD_USER_UNIT_PATH_PRECEDENCE`
- [x] Stale binary version confirmed: v2026.4.21 at `/opt/openclaw/tools/node-v22.22.0/bin/openclaw`
- [x] Correct binary confirmed: v2026.5.27 at `/opt/openclaw/bin/openclaw`
- [x] Fix applied by Supervisor: `/opt/openclaw/bin` prepended to `PATH` in systemd unit
- [x] `daemon-reload + restart` executed
- [x] Evidence discrepancy reconciled with file `mtime`
- [x] `PM_ROLE_DISCOVERY_ERROR` documented

---

## Alternation Waiver

- **Classification:** `OPS_AGENT_ALTERNATION_RULE_VIOLATION_AT_PE_OPENING`
- **Waiver status:** GRANTED (PO, 2026-06-01)
- **Waiver artefact:** `.elis/pe/PE-OPS-OPENCLAW-CLI-PATH-01/ALTERNATION_WAIVER.md`
- **Summary:** infra-impl-b (claude) was assigned as implementer; alternation rule required infra-impl-a (codex). PO granted a one-time waiver — see waiver artefact for full rationale.
- **check_current_pe.py status:** `CURRENT_PE_CHECK_NO_WAIVER_MECHANISM` — `_validate_alternation()` has no approved bypass path; waiver is a transparency record only.

---

## Validator Instructions

**Validator (infra-val-a):** verify the post-fix environment as per acceptance criteria. Write `REVIEW_PE-OPS-OPENCLAW-CLI-PATH-01.md` with a `### Evidence` section (required) and `### Verdict` line. Do not mutate any host/systemd files.