# PE-OPS-A2A-PRODUCTION-01 — Put A2A Internal Agent Communication into Production

## PE_ID
PE-OPS-A2A-PRODUCTION-01

## Objective
Put the ELIS A2A internal agent communication layer (established by PE-OPS-A2A-RUNTIME-01) into production: make the transport persistent, production-grade, and actively used by ELIS agents for internal coordination — while keeping Discord as the exclusive PO-facing channel.

## Opening packet (corrected — PM-CHORE-107 r2)
- Lane: **Strict**
- Baseline HEAD: `83f91cd9ca8f955cd804ec58039a3a28f1e563c6`
- Branch: `feature/pe-ops-a2a-production-01-a2a-internal-agent-communication-production`
- Implementer: `infra-impl-a`
- Validator: `infra-val-b`
- Supervisor verification role: read-only only
- Dispatch: **HELD** — PM must issue explicit dispatch instruction

## First-pass scope (Strict lane — PO-approved)
Read-only discovery and planning only. No implementation, no config edits, no live routing.

Allowed:
- `HANDOFF.md` updates if needed
- `.elis/pe/PE-OPS-A2A-PRODUCTION-01/PE_TASK.md` updates
- Read-only inspection of PE-OPS-A2A-RUNTIME-01 artefacts on `main`
- Read-only inspection of current A2A runtime/config/status on elis-server
- Implementation plan document
- Risk and rollback plan document
- Proposed file scope for actual implementation

Not allowed in first pass:
- Runtime code changes
- OpenClaw session mutation
- Service restart or reload
- A2A live routing enablement
- Any config/auth/secret changes

## What is already implemented (PE-OPS-A2A-RUNTIME-01, merged 2026-05-26)
- `scripts/a2a_local_transport.py` — file-based transport at `/tmp/elis_a2a/<recipient>/`
- `schemas/a2a_message.schema.json` — five message types (status, reset_ack, task_state, evidence_ref, failure)
- `schemas/a2a_envelope.schema.json`
- `tests/test_a2a_local_transport.py` — 30/30 passing
- `docs/governance/ELIS_A2A_Runtime_Spec.md`
- `docs/governance/ELIS_A2A_Communication_Matrix.md`
- `docs/governance/ELIS_A2A_Production_Backbone.md` (design/spec only)
- `docs/governance/ELIS_A2A_Production_Security_Model.md` (design/spec only)
- `docs/governance/ELIS_A2A_Production_Rollback.md` (design/spec only)

## What "production" means in this PE
Defined in GATE_1_A2A_PRODUCTION_READINESS_PLAN — see PM report for detail.

## Hard stops (Strict lane)
- No live config edits
- No OpenClaw session mutation
- No service restart/reload without explicit per-operation PO approval
- No A2A live routing enablement without PO approval
- No secrets, tokens, or credentials in messages or code
- No dispatch automation

## Rollback posture
- Discord/session routing remains operational fallback
- New transport gated behind explicit enable step (not automatic)
- Rollback: abandon branch or `git revert` — no service action required in planning phase

## Evidence requirements
- Baseline HEAD must match `origin/main`
- Clean worktree required before any commit
- All state claims require pasted command output
- Validator verdict must include inline evidence before the verdict line

## Handoff requirements
- Opening packet recorded in `CURRENT_PE.md`
- Task file at approved path (this file)
- Implementer dispatch deferred until PM issues explicit instruction
