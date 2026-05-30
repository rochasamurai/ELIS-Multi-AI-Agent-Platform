# HANDOFF — PE-OPS-A2A-PRODUCTION-02 — Gate 1

> Canonical path: `.elis/pe/PE-OPS-A2A-PRODUCTION-02/HANDOFF.md`
> Implementer: `infra-impl-a`
> Gate: 1 — Read-only discovery and planning pass
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
| Gate | 1 — planning pass only |

---

## Gate 1 summary

Gate 1 is a read-only discovery and planning pass. No runtime code, no config edits,
no service restarts, no live routing, no `/opt/elis/a2a/` directory creation. The
deliverables are three planning documents committed on the PE branch.

### What was done in Gate 1

1. Read and verified all authorised artefacts on `origin/main`:
   - `scripts/a2a_local_transport.py`
   - `tests/test_a2a_local_transport.py`
   - `schemas/a2a_envelope.schema.json`
   - `schemas/a2a_message.schema.json`
   - `docs/governance/ELIS_A2A_Runtime_Spec.md`
   - `docs/governance/ELIS_A2A_Communication_Matrix.md`
   - `docs/governance/ELIS_A2A_Production_Backbone.md`
   - `docs/governance/ELIS_A2A_Production_Security_Model.md`
   - `docs/governance/ELIS_A2A_Production_Rollback.md`
   - `docs/openclaw/ELIS_A2A_GATEWAY_SPEC.md`
   - `.elis/pe/PE-OPS-A2A-PRODUCTION-01/` (read-only prior context)

2. Ran `python3 scripts/check_current_pe.py` — PASS.

3. Ran scope gate `git diff --name-status origin/main..HEAD` — only PM-authored
   files present; no scope contamination.

4. Produced three planning documents:
   - `A2A_Production_Plan.md` — current-state assessment, production gap analysis,
     phased implementation plan, proposed file scope, acceptance criteria
   - `A2A_Production_Risk_Rollback.md` — risk register, mitigations, rollback procedures

### What was NOT done in Gate 1

- No runtime code written or modified
- No tests added or changed
- No schemas modified
- No OpenClaw/Hermes config touched
- No service started, stopped, or restarted
- No `/opt/elis/a2a/` directory created
- No A2A routing enabled
- No PR created (PM pushes)

---

## What Gate 2 must address

Gate 2 is the actual implementation pass. Each sub-item below requires explicit PM/PO
approval before execution. None of these actions may begin until PM issues a Gate 2
dispatch instruction.

### Gate 2 scope (proposed — PM/PO must confirm before execution)

1. **Durable runtime directory** — Create `/opt/elis/a2a/` with appropriate ownership
   and permissions. Requires explicit PO gate approval.

2. **Node.js gateway implementation** — Implement `a2a-gateway.js` per
   `docs/openclaw/ELIS_A2A_GATEWAY_SPEC.md`:
   - `127.0.0.1:24001` binding (loopback only)
   - HTTP health check, send, and polling endpoints
   - WebSocket push endpoint
   - Envelope validation against `schemas/a2a_envelope.schema.json`
   - Pair validation (three allowed Phase-1 pairs)
   - Prohibited content scanning
   - Per-agent message queues with TTL enforcement
   - Structured logging (stdout + optional `~/.elis/a2a/gateway.log`)

3. **Startup wrapper and package manifest** — `a2a-gateway.sh` and `package.json`
   with `ws` dependency.

4. **Transport persistence** — Route internal agents off `/tmp/elis_a2a/` (ephemeral)
   to the HTTP gateway when it is running, falling back to file transport if gateway is
   not available. Decision on persistence strategy requires PM/PO approval.

5. **Durable message log** — Append-only log of all dispatched and acknowledged
   messages per the security model in `ELIS_A2A_Production_Security_Model.md`.

6. **Integration tests** — Pytest or Node.js tests covering round-trip messaging via
   the HTTP gateway, pair rejection, prohibited content rejection, TTL expiry, and
   health endpoint.

7. **OpenClaw config update** — Enable A2A routing in live config. Requires explicit
   PO gate approval and Supervisor verification. Must be done via live
   `~/.openclaw/openclaw.json` (NOT stale `/opt/elis/repo/openclaw/openclaw.json`).

8. **DISPATCH_PROVENANCE_PROOF_V1 integration** — Confirm that dispatch provenance
   proof schema is recorded for every A2A-dispatched agent result, and that the proof
   fields (worktree, agentId, session, model, cwd) are emitted and verifiable.

### Files proposed for Gate 2 (subject to PM/PO approval)

| File | Action |
|------|--------|
| `/opt/elis/a2a/a2a-gateway.js` | Create — Node.js HTTP/WebSocket gateway |
| `/opt/elis/a2a/a2a-gateway.sh` | Create — startup wrapper |
| `/opt/elis/a2a/package.json` | Create — Node.js manifest |
| `tests/test_a2a_gateway.py` or `tests/test_a2a_gateway.js` | Create — integration tests |
| `docs/governance/ELIS_A2A_Production_Activation.md` | Create — production activation runbook |

No files in `scripts/`, `schemas/`, or existing `docs/governance/` files will be
modified unless PM/PO explicitly authorises the change.

---

## Hard stops — confirmed not triggered in Gate 1

- No changes to `scripts/`, `elis/`, `tests/`, or `schemas/`
- No changes to `docs/governance/` or any file outside the three Gate 1 deliverables
- No OpenClaw/Hermes config edits
- No service restart or reload
- No `/opt/elis/a2a/` directory created
- No A2A live routing enabled
- No PR created
- No content from PE-OPS-A2A-PRODUCTION-01 branches (contaminated commits excluded)

---

## Evidence

```
check_current_pe.py:
CURRENT_PE.md OK — release context, roles, registry, and alternation valid.

Scope gate (git diff --name-status origin/main..HEAD):
A       .elis/pe/PE-OPS-A2A-PRODUCTION-02/PE_TASK.md
A       .elis/pe/PE-OPS-A2A-PRODUCTION-02/TEMPORARY_DELEGATE_TASK_EXCEPTION.md
M       .elis/state/current_pe.json
M       CURRENT_PE.md
```

(Scope gate run before the Gate 1 commit; Gate 1 deliverables will appear after commit.)

---

## Status

Gate 1 complete. Awaiting PM review, scope gate confirmation post-commit, and Gate 2
dispatch instruction from PM before any further work begins.
