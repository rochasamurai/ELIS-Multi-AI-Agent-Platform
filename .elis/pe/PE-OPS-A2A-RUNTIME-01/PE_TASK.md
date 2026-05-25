# PE-OPS-A2A-RUNTIME-01 — Implement Local A2A Backbone for Structured Agent Communication

## PE_ID
PE-OPS-A2A-RUNTIME-01

## Objective
Implement a local-only A2A communication backbone that enables ELIS agents to exchange structured messages (status, reset/binding acknowledgement, task state, evidence reference, failure-class) without relying solely on Discord thread routing.

## Opening packet
- Lane: Strict
- Baseline HEAD: `a61a0a173568bbce7d9446245f8117f237d352bd`
- Branch: `feature/pe-ops-a2a-runtime-01-clean-local-backbone`
- Implementer: `infra-impl-a`
- Validator: `infra-val-b`
- Thread: `1508557746319003780`
- Session ID: `a848d4fe-7c79-4839-b6cb-630161fc85cd`

## Scope
- Local-only A2A backbone — no remote or cloud-relay dependencies in Phase 1
- Structured message envelope: `status`, `reset_ack`, `task_state`, `evidence_ref`, `failure`
- Message delivery contract between PM, Supervisor, and Advisor agents
- Schema and validation for envelope types
- Governance boundary documentation

## Out of scope
- Discord integration or replacement (Discord remains the PO-facing channel)
- Remote/off-host A2A routing
- Runtime configuration changes
- Service restarts or OpenClaw/Hermes reload
- GitHub PR creation or merge actions
- Any governance authority claims via A2A
- Any merge authority via A2A

## Acceptance criteria

| AC | Criterion |
|----|-----------|
| AC-1 | Local A2A transport layer is implemented and reachable between PM, Supervisor, and Advisor agents without Discord routing. |
| AC-2 | Structured message envelope schema covers at minimum: `status`, `reset_ack`, `task_state`, `evidence_ref`, `failure` message types. |
| AC-3 | A2A layer must not claim or exercise governance authority — all governance decisions remain with PO and the existing PE protocol. |
| AC-4 | A2A layer must not claim or exercise merge authority — all merges require PO approval and gate passage. |
| AC-5 | A2A must not bypass PO approval on any action that currently requires it. |
| AC-6 | A2A must not bypass implementer/validator gate checks. |
| AC-7 | A2A must not replace existing PE evidence requirements (REVIEW.md, gate comments, PR evidence). |
| AC-8 | No runtime/config/service changes are introduced. |
| AC-9 | A smoke test confirms message round-trip between at least two agent endpoints locally. |
| AC-10 | Validator independently confirms AC-1 through AC-9 with pass verdict and evidence committed to `.elis/pe/PE-OPS-A2A-RUNTIME-01/REVIEW.md`. |

## Implementation boundaries
- Write path: repository files only within the approved file scope
- No changes to `openclaw/openclaw.json`, OpenClaw runtime config, Hermes config, or any service definition
- No secret or token changes
- No dispatch to implementer or validator until PM explicitly approves after PO/Supervisor verification
- No `sessions_spawn` or `sessions_send` in opening phase

## First-pass file scope
- `CURRENT_PE.md`
- `.elis/state/current_pe.json`
- `.elis/pe/PE-OPS-A2A-RUNTIME-01/PE_TASK.md`
- `.elis/pe/PE-OPS-A2A-RUNTIME-01/HANDOFF.md`

## Approved implementation file scope (post-opening, requires PM authorisation to unlock)
- `docs/governance/ELIS_A2A_Runtime_Spec.md`
- `schemas/a2a_message.schema.json`
- `scripts/a2a_local_transport.py` (or equivalent)
- `tests/test_a2a_local_transport.py`
- `.elis/pe/PE-OPS-A2A-RUNTIME-01/REVIEW.md` (validator-owned)

## Validation approach
- Validator (`infra-val-b`) runs independently from `infra-val-b` worktree
- Validator confirms each AC in REVIEW.md with pass/fail verdict and evidence
- Gate 1: PM reviews implementation commit; gate 2: PO approves after validator PASS

## Rollback/safety notes
- All changes are repository-only; rollback is `git revert` or branch abandonment
- No service or runtime state is modified; rollback requires no service action
- If any hard stop is violated, PM stops work and notifies PO before continuing

## Hard stops
- No implementation files until PO/Supervisor verify this opening commit
- No implementer dispatch
- No validator dispatch
- No `sessions_spawn`
- No `sessions_send`
- No runtime/config/service changes
- No OpenClaw/Hermes restart or reload
- No GitHub PR
- No merge
