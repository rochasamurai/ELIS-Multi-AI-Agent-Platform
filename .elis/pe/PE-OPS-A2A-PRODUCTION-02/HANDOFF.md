# HANDOFF — PE-OPS-A2A-PRODUCTION-02 — Gate 2A

> Canonical path: `.elis/pe/PE-OPS-A2A-PRODUCTION-02/HANDOFF.md`
> Implementer: `infra-impl-a`
> Gate: 2A — Code + test + ELIS runtime workspace directory creation
> Date: 2026-05-30

---

## Identity

| Field | Value |
|-------|-------|
| PE ID | PE-OPS-A2A-PRODUCTION-02 |
| Title | Productionise A2A Dispatch Under Provenance Controls |
| Branch | feature/pe-ops-a2a-production-02-productionise-a2a-dispatch-provenance-controls |
| Implementer surface | infra-impl-a |
| Validator surface | infra-val-b |
| Gate | 2A — code + test + ELIS runtime workspace directory creation |

---

## DISPATCH_PROVENANCE_PROOF_V1

```
DISPATCH_PROVENANCE_PROOF_V1
requested_agent_id:          infra-impl-a
actual_agent_id:             infra-impl-a
actual_session_id:           agent:infra-impl-a:subagent:4a473611-4c54-4005-afd2-bacceafed75b
actual_cwd:                  /opt/elis/agent-worktrees/infra-impl-a
actual_worktree:             /opt/elis/agent-worktrees/infra-impl-a
branch:                      feature/pe-ops-a2a-production-02-productionise-a2a-dispatch-provenance-controls
head:                        2217d4e784c34ee302624a1e1707ed490a222f09
git_identity:                infra-impl-a / infra-impl-a@openclaw.local
model_provider_profile:      openrouter/qwen/qwen3-coder-flash  [corrected: Gate 2A session ran as claude-cli/claude-sonnet-4-6; live config binding is openrouter/qwen/qwen3-coder-flash; discrepancy noted per OBS-02]
dispatch_method:             sessions_spawn.agentId
openclaw_config_agent_match: PASS
acp_command_not_used:        PASS
pm_worktree_not_used:        PASS
dispatch_timestamp:          2026-05-30T19:27:00+01:00
```

---

## Gate 2A Summary

Gate 2A implements the production mailbox structure, enabled-sentinel disabled-by-default
guard, and Phase 1 ELIS agent identity smoke round-trips. No OpenClaw/Hermes config was
changed, no service was restarted, and `/opt/elis/a2a/.enabled` was not created — the A2A
transport remains disabled by default until explicit PO enablement.

---

## Files Changed

### `scripts/a2a_local_transport.py`

| Change | Description |
|--------|-------------|
| Constants block | Replaced `_MAILBOX_ROOT = Path("/tmp/elis_a2a")` with three constants: `_A2A_RUNTIME_ROOT = Path("/opt/elis/a2a")`, `_MAILBOX_ROOT = _A2A_RUNTIME_ROOT / "mailboxes"`, `_ENABLED_SENTINEL = _A2A_RUNTIME_ROOT / ".enabled"` |
| New exception class | Added `A2ATransportDisabledError(RuntimeError)` immediately after constants block, before `_VALID_MESSAGE_TYPES` |
| `__init__` | Added `skip_enabled_check: bool = False` keyword-only parameter; raises `A2ATransportDisabledError` when sentinel absent and check not skipped |
| `_mailbox()` | Now creates `inbox/`, `processed/`, and `dead/` subdirectories under `<root>/<recipient>/` and returns `inbox` path |
| `receive()` | Reads from `inbox/`; moves successfully parsed files to `processed/`; moves corrupt files to `dead/` |
| `list_messages()` | Reads from `inbox/` non-destructively |

### `tests/test_a2a_local_transport.py`

| Change | Description |
|--------|-------------|
| `transport` fixture | Added `skip_enabled_check=True` to bypass sentinel in all existing tests |
| `TestGovernanceBoundary` | All 7 methods updated to accept `tmp_path` and use `skip_enabled_check=True` (required because default constructor checks sentinel) |
| `TestGate2AEnabledSentinel` (new) | 3 tests: raises when sentinel absent, succeeds when sentinel present, `skip_enabled_check` bypass |
| `TestGate2AMailboxStructure` (new) | 5 tests: send writes to inbox, receive moves to processed, corrupt moves to dead, list reads inbox only, no crash on empty receive |
| `TestGate2APhase1AgentIds` (new) | Parametrised over 5 Phase 1 agent IDs (pm, infra-impl-a, infra-impl-b, infra-val-a, infra-val-b): send/receive round-trip for each |

---

## ELIS Runtime Workspace Directories Created

```
$ ls -la /opt/elis/a2a/
total 16
drwxr-x---  4 samurai samurai 4096 May 30 19:29 .
drwxr-xr-x 13 samurai samurai 4096 May 30 19:29 ..
drwxr-x---  2 samurai samurai 4096 May 30 19:29 logs
drwxr-x---  7 samurai samurai 4096 May 30 19:29 mailboxes

$ ls -la /opt/elis/a2a/mailboxes/
total 28
drwxr-x--- 7 samurai samurai 4096 May 30 19:29 .
drwxr-x--- 4 samurai samurai 4096 May 30 19:29 ..
drwxr-x--- 5 samurai samurai 4096 May 30 19:29 infra-impl-a
drwxr-x--- 5 samurai samurai 4096 May 30 19:29 infra-impl-b
drwxr-x--- 5 samurai samurai 4096 May 30 19:29 infra-val-a
drwxr-x--- 5 samurai samurai 4096 May 30 19:29 infra-val-b
drwxr-x--- 5 samurai samurai 4096 May 30 19:29 pm

=== pm ===           dead  inbox  processed
=== infra-impl-a === dead  inbox  processed
=== infra-impl-b === dead  inbox  processed
=== infra-val-a ===  dead  inbox  processed
=== infra-val-b ===  dead  inbox  processed
```

Permissions: owner `samurai:samurai`, mode `750`. `/opt/elis/a2a/.enabled` was NOT created.

---

## Test Results

```
============================= test session starts ==============================
platform linux -- Python 3.12.3, pytest-9.0.3, pluggy-1.6.0
rootdir: /opt/elis/agent-worktrees/infra-impl-a
configfile: pyproject.toml
collected 43 items

tests/test_a2a_local_transport.py ...................................... [100%]

============================== 43 passed in 0.17s ==============================
```

**43 passed, 0 failed.**

---

## Sentinel Absent Verification

```
PASS: A2ATransportDisabledError raised: ELIS A2A transport is disabled.
      Enable marker not found: /opt/elis/a2a/.enabled
```

The default `A2ATransport()` constructor raises `A2ATransportDisabledError` when
`/opt/elis/a2a/.enabled` is absent. CONFIRMED.

---

## Scope Gate

```
$ git diff --name-status HEAD
M       scripts/a2a_local_transport.py
M       tests/test_a2a_local_transport.py
```

Only the two approved implementation files plus this HANDOFF are in scope. No unrelated
files touched.

---

## Hard Stop Confirmations

| Requirement | Status |
|-------------|--------|
| `/opt/elis/a2a/.enabled` NOT created | CONFIRMED |
| No OpenClaw/Hermes config changed | CONFIRMED |
| No service restart or reload | CONFIRMED |
| No A2A routing enabled | CONFIRMED |
| No PR created | CONFIRMED |
| No push | CONFIRMED |
| No files outside approved list touched | CONFIRMED |
| No cherry-pick from PE-OPS-A2A-PRODUCTION-01 branches | CONFIRMED |

---

## ELIS-First Naming Confirmation

All terminology in this HANDOFF and in the code changes uses ELIS-first naming conventions.
"OpenClaw" appears only as a concrete implementation identifier (referencing the
`~/.openclaw/openclaw.json` config file path). No model-coupled agent IDs were used.

---

## Status

Gate 2A complete. Awaiting PM review and Gate 2B dispatch instruction.

---

## Gate 2A-model-fix

### Files created/updated

| File | Change |
|------|--------|
| `scripts/check_agent_model_registry.py` | New — ELIS Platform agent model registry checker |
| `tests/test_check_agent_model_registry.py` | New — full test suite for registry checker |
| `docs/governance/ELIS_Agent_Dispatch_Binding_and_Validation_Rules.md` | Appended model binding requirement section |
| `.elis/pe/PE-OPS-A2A-PRODUCTION-02/PE_TASK.md` | Appended Gate 2A-model-fix scope block |

### Example PASS output

```
ELIS Platform Agent Model Registry Check — config: /home/samurai/.openclaw/openclaw.json

  PASS  infra-impl-a: openrouter/qwen/qwen3-coder-flash
  PASS  infra-impl-b: openrouter/deepseek/deepseek-v4-flash
  PASS  infra-val-a: openrouter/deepseek/deepseek-v4-pro
  PASS  infra-val-b: openrouter/z-ai/glm-5.1
  PASS  prog-impl-a: <model>
  PASS  prog-impl-b: <model>
  PASS  prog-val-a: <model>
  PASS  prog-val-b: <model>

RESULT: PASS — all ELIS Platform agents have model entries in live config
```

### Example FAIL output (one agent missing)

```
ELIS Platform Agent Model Registry Check — config: /home/samurai/.openclaw/openclaw.json

  PASS  infra-impl-a: openrouter/qwen/qwen3-coder-flash
  FAIL  infra-impl-b: model entry missing from live config
  ...

RESULT: FAIL — 1 agent(s) missing model entry: infra-impl-b
```

### Model exception record

Gate 2A-model-fix implementation ran as claude-cli/claude-sonnet-4-6 under PO-approved exception
(MODEL_PROVIDER_PROVENANCE_EXCEPTION_ACCEPTED_BY_PO). Configured model for infra-impl-a is
openrouter/qwen/qwen3-coder-flash. OpenClaw model-registry remediation (MODEL_APPLY_FAILURE)
not yet resolved; explicit model parameter was passed but not honoured at runtime.

### Script read-only confirmation

`check_agent_model_registry.py` is read-only in all modes:
- `--check` (default): reads config and reports; no writes
- `--sync`: exits 2 immediately; no writes, no reads of live config
- No filesystem mutation in any mode

### Status

Gate 2A-model-fix complete. Awaiting Validator review.
