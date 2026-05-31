# A2A Production Plan — PE-OPS-A2A-PRODUCTION-02

> Gate 1 planning document — read-only discovery pass.
> Implementer: infra-impl-a
> Date: 2026-05-30
> Status: Gate 1 — no implementation has occurred.

---

## 1. Objective

Put the ELIS A2A internal agent communication layer into production with full
dispatch provenance controls. This plan supersedes the contaminated
PE-OPS-A2A-PRODUCTION-01, which was invalidated due to dispatch provenance failures
(wrong implementer execution, wrong worktree, PM subagent dispatch).

A2A remains **disabled** by default. All production cutover requires explicit PO
approval per the hard stops in `PE_TASK.md` and `TEMPORARY_DELEGATE_TASK_EXCEPTION.md`.

---

## 2. Current state assessment

### 2.1 What is implemented and on `main`

| Artefact | Path | Status |
|----------|------|--------|
| Local file transport | `scripts/a2a_local_transport.py` | Implemented, tested, merged |
| Local transport schema | `schemas/a2a_message.schema.json` | Merged — 5 message types |
| Phase-1 envelope schema | `schemas/a2a_envelope.schema.json` | Merged — HTTP gateway envelope |
| Transport test suite | `tests/test_a2a_local_transport.py` | 30+ tests passing |
| Runtime spec | `docs/governance/ELIS_A2A_Runtime_Spec.md` | Merged |
| Communication matrix | `docs/governance/ELIS_A2A_Communication_Matrix.md` | Merged |
| Production backbone | `docs/governance/ELIS_A2A_Production_Backbone.md` | Design/spec only |
| Security model | `docs/governance/ELIS_A2A_Production_Security_Model.md` | Design/spec only |
| Rollback plan | `docs/governance/ELIS_A2A_Production_Rollback.md` | Design/spec only |
| Gateway spec | `docs/openclaw/ELIS_A2A_GATEWAY_SPEC.md` | Spec only — not implemented |

### 2.2 What is NOT yet implemented

| Gap | Details |
|-----|---------|
| HTTP/WebSocket gateway | No `/opt/elis/a2a/` directory; no `a2a-gateway.js`; gateway spec exists but is not running |
| Transport persistence | Current mailbox root is `/tmp/elis_a2a/` — ephemeral, lost on reboot |
| Agent identity authentication | No identity verification beyond envelope field validation |
| Durable message log | No append-only audit log for dispatched/ACK'd messages |
| Supervisor diagnostic visibility | No health endpoint, no live queue inspection |
| OpenClaw A2A routing | Not enabled; agents communicate via Discord/session routing |
| Provenance proof integration | DISPATCH_PROVENANCE_PROOF_V1 schema defined for PE governance but not wired into transport |

### 2.3 Phase-1 agent identities (from Communication Matrix)

Phase-1 A2A is restricted to three agent pairs:
- `elis-advisor` ↔ `elis-pm`
- `elis-advisor` ↔ `elis-supervisor`
- `elis-pm` ↔ `elis-supervisor`

All implementer and validator agents (including `infra-impl-a`, `infra-val-b`, etc.)
are **explicitly excluded** from Phase-1 A2A per the Communication Matrix §2.1.

### 2.4 Gateway binding (from ELIS_A2A_GATEWAY_SPEC.md)

- Address: `127.0.0.1:24001` (loopback only — no external interfaces)
- Protocol: HTTP / WebSocket
- TLS: not required (local loopback)
- The gateway must refuse to start if any non-loopback interface is configured.

---

## 3. What "production" means for this PE

Based on the governance artefacts and the PE objective, production means:

1. **Durable transport** — Messages survive process restarts; mailbox root moves from
   `/tmp/elis_a2a/` to a persistent path (proposed: `/opt/elis/a2a/mailboxes/`).

2. **Running HTTP/WebSocket gateway** at `127.0.0.1:24001` — implements the
   `ELIS_A2A_GATEWAY_SPEC.md` API: health, send, polling, WebSocket push.

3. **Authenticated dispatch** — Envelope sender/recipient validated against the three
   Phase-1 identities; non-approved pairs rejected with structured error.

4. **Durable message log** — Append-only log of every message send, ACK, and failure
   event. Each log entry includes: timestamp, message_id, sender, recipient,
   message_type, and outcome (accepted / rejected / failure classification).

5. **Supervisor diagnostic visibility** — Supervisor can query the health endpoint and
   inspect per-agent queue depth without consuming messages.

6. **Provenance controls** — Every agent dispatch via A2A must include a
   DISPATCH_PROVENANCE_PROOF_V1 record in the message payload or associated log entry,
   confirming: actual_agent_id, actual_worktree, session_id, model_provider_profile,
   and dispatch_method.

7. **OpenClaw integration** — A2A routing enabled in live OpenClaw config
   (`~/.openclaw/openclaw.json`) after explicit PO gate approval.

---

## 4. Phased implementation plan

### Phase A — Pre-conditions (must be confirmed before any code is written)

| Check | Action required |
|-------|----------------|
| PO gate approval for runtime directory creation | PM/PO explicit instruction before `/opt/elis/a2a/` is created |
| Node.js version on elis-server | Verify `node --version` ≥ 18 (read-only check) |
| Available port | Verify `127.0.0.1:24001` is free (read-only check) |
| `ws` npm package availability | Verify `npm ls ws` or `npm install ws` can run in isolated context |
| No contamination from PE-OPS-A2A-PRODUCTION-01 | Confirmed: forbidden commits not in this branch |

### Phase B — Runtime directory and gateway implementation

Requires explicit PO gate approval before execution.

| Step | File | Action |
|------|------|--------|
| B.1 | `/opt/elis/a2a/` | Create directory; set ownership `elis-impl:elis-impl` (or per PO instruction); mode `750` |
| B.2 | `/opt/elis/a2a/package.json` | Create Node.js manifest; declare `ws` dependency |
| B.3 | `/opt/elis/a2a/a2a-gateway.js` | Implement per `ELIS_A2A_GATEWAY_SPEC.md`: loopback binding, HTTP endpoints, WebSocket, envelope validation, pair validation, prohibited content scan, per-agent queues, TTL, structured logging |
| B.4 | `/opt/elis/a2a/a2a-gateway.sh` | Create startup wrapper: checks loopback binding, starts gateway, logs PID |

### Phase C — Durable mailbox and message log

| Step | File | Action |
|------|------|--------|
| C.1 | `/opt/elis/a2a/mailboxes/` | Create persistent mailbox root |
| C.2 | `/opt/elis/a2a/logs/dispatch.log` | Create append-only dispatch log; rotate daily |
| C.3 | `scripts/a2a_local_transport.py` | Update `_MAILBOX_ROOT` to use `/opt/elis/a2a/mailboxes/` when running in production; keep `/tmp/elis_a2a/` as test/CI fallback |

Note: C.3 requires PO/PM approval because it modifies a file in `scripts/`.

### Phase D — Integration tests

| Step | File | Action |
|------|------|--------|
| D.1 | `tests/test_a2a_gateway.py` (or `.js`) | Implement: round-trip via HTTP, pair rejection, prohibited content rejection, TTL expiry, health endpoint |
| D.2 | CI | Verify all existing tests still pass after Phase C changes |

### Phase E — OpenClaw integration and provenance wiring

Requires explicit PO gate approval before execution.

| Step | Action |
|------|--------|
| E.1 | Update live `~/.openclaw/openclaw.json` to enable A2A routing for Phase-1 agent pairs |
| E.2 | Verify Supervisor can reach health endpoint (`curl -s http://127.0.0.1:24001/health`) |
| E.3 | Confirm DISPATCH_PROVENANCE_PROOF_V1 fields emitted in gateway logs for every dispatch |
| E.4 | Commit production activation runbook to `docs/governance/ELIS_A2A_Production_Activation.md` |

### Phase F — Production readiness verification

| Step | Evidence required |
|------|------------------|
| F.1 | Gateway health check output — `{"status": "ok", ...}` |
| F.2 | Round-trip message proof — send from `elis-pm`, receive at `elis-supervisor` |
| F.3 | Rejected pair proof — `infra-impl-a` → `elis-pm` rejected with structured error |
| F.4 | Durable log entry — one complete log entry showing message_id, sender, recipient, outcome |
| F.5 | All existing tests (`test_a2a_local_transport.py`) still passing under CI |

---

## 5. Proposed file scope for Gate 2

| File | Status | Gate 2 action |
|------|--------|--------------|
| `/opt/elis/a2a/a2a-gateway.js` | Does not exist | Create |
| `/opt/elis/a2a/a2a-gateway.sh` | Does not exist | Create |
| `/opt/elis/a2a/package.json` | Does not exist | Create |
| `tests/test_a2a_gateway.py` | Does not exist | Create |
| `docs/governance/ELIS_A2A_Production_Activation.md` | Does not exist | Create |
| `scripts/a2a_local_transport.py` | Exists | Modify `_MAILBOX_ROOT` for production path — PO approval required |

Files that must NOT be modified without explicit PM/PO instruction:
- `schemas/a2a_envelope.schema.json`
- `schemas/a2a_message.schema.json`
- `docs/governance/ELIS_A2A_Communication_Matrix.md`
- `docs/governance/ELIS_A2A_Runtime_Spec.md`
- `docs/openclaw/ELIS_A2A_GATEWAY_SPEC.md`
- Any CI workflow files
- Any `CURRENT_PE.md` or governance files outside `.elis/pe/PE-OPS-A2A-PRODUCTION-02/`

---

## 6. Acceptance criteria (proposed)

| AC | Description |
|----|-------------|
| AC-1 | Gateway starts, binds to `127.0.0.1:24001`, and responds `{"status": "ok"}` on `/health` |
| AC-2 | Round-trip message: `elis-pm` sends, `elis-supervisor` receives, content matches, ACK emitted |
| AC-3 | Disallowed pair (`infra-impl-a` → `elis-pm`) is rejected with structured error response |
| AC-4 | Prohibited content (e.g. `git push` in body) is rejected |
| AC-5 | Durable log contains at least one complete dispatch entry with all required fields |
| AC-6 | All 30+ existing `test_a2a_local_transport.py` tests pass under CI |
| AC-7 | Gateway refuses to start if a non-loopback interface is configured |
| AC-8 | DISPATCH_PROVENANCE_PROOF_V1 fields (actual_agent_id, actual_worktree, session_id, model, dispatch_method) are present in the log for every gateway dispatch |
| AC-9 | No secrets, tokens, credentials, or API keys appear in any A2A message or log entry |
| AC-10 | A2A transport carries no governance authority, merge authority, or PO approval signals (verified by attribute checks on gateway object) |

---

## 7. Hard stops (all phases — no exceptions)

- A2A remains disabled by default until explicit PO enablement instruction
- No OpenClaw/Hermes config edits without explicit PO approval per operation
- No service restart or reload without explicit PO approval per operation
- No `/opt/elis/a2a/` creation without explicit PO gate approval
- No PR creation (PM pushes and opens PR)
- No content from PE-OPS-A2A-PRODUCTION-01 branches (commits c4e5754, b550d9e, e7ffbb2)
- All live config reads must use `~/.openclaw/openclaw.json` (NOT stale `/opt/elis/repo/openclaw/openclaw.json`)

---

## 8. References

- `PE_TASK.md` — authoritative scope and constraints for this PE
- `TEMPORARY_DELEGATE_TASK_EXCEPTION.md` — dispatch method authorisation
- `scripts/a2a_local_transport.py` — existing transport implementation
- `schemas/a2a_message.schema.json` — local transport envelope schema
- `schemas/a2a_envelope.schema.json` — Phase-1 HTTP gateway envelope schema
- `docs/openclaw/ELIS_A2A_GATEWAY_SPEC.md` — gateway implementation specification
- `docs/governance/ELIS_A2A_Communication_Matrix.md` — Phase-1 agent identities and pairs
- `docs/governance/ELIS_A2A_Runtime_Spec.md` — governance boundaries
- `docs/governance/ELIS_A2A_Production_Security_Model.md` — security controls
- `docs/governance/ELIS_A2A_Production_Rollback.md` — rollback posture
- `AGENTS.md` — workflow rules and evidence requirements
