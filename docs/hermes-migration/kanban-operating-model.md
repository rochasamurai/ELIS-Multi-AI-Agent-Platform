# Kanban Operating Model — ELIS/Hermes Governance

**PEs:** PE-OPS-HERMES-KANBAN-RUNTIME-01, PE-OPS-HERMES-PM-MIGRATION-01  
**Status:** Pilot phase — not production cutover  
**Date:** 2026-06-05

---

## Core Principle

> **Hermes Kanban is operational coordination state, not final governance authority.**

Kanban tasks track work-in-progress, decomposition, and dispatch. They do not replace repository artefacts, HANDOFF.md evidence packets, or GitHub PRs as the canonical record of completed work.

## Authority Hierarchy

1. **Repository artefacts** — authoritative evidence (commits, PRs, HANDOFF.md, test results, config)
2. **Kanban board** — operational coordination (task lifecycle, decomposition, dispatch tracking)
3. **Discord threads** — communication (not durable governance state)

## Role Boundaries

### ELIS PM (Kanban Orchestrator)

- **May:** Create, decompose, dispatch, and track Kanban tasks
- **May:** Observe board state and report status
- **May:** Coordinate PE workflow across implementers and validators
- **Must not:** Implement code, validate code, write to GitHub, edit config
- **Toolset:** `kanban` only (no terminal, file, web access)

### Implementers

- **May:** Claim and execute implementation tasks
- **Must:** Produce verifiable repository artefacts (commits, diffs, test results)
- **Must:** Report completion with evidence (not just "done" status)

### Validators

- **May:** Claim and execute validation tasks
- **Must:** Produce HANDOFF.md-style evidence packets referencing authoritative HEAD
- **Must:** Verify repository artefacts, not Kanban task metadata

## Separations Preserved

| Separation | Why |
|---|---|
| Implementer ≠ Validator | No self-review. Validation must be independent. |
| PM ≠ Implementer | PM coordinates, never writes code. |
| PM ≠ Validator | PM tracks state, never validates outcomes. |
| Kanban state ≠ Governance evidence | Kanban tracks flow; repo artefacts are the record. |

## Evidence Requirements

Every completed PE task must produce:

1. **HANDOFF.md** or equivalent evidence packet — referencing authoritative commit/HEAD
2. **Status packet** — files changed, checks passed, verdict
3. **Rollback command** — for any reversible change

Kanban task "done" status alone is insufficient evidence of completion.

## HANDOFF/REVIEW Rule

The validator worktree HEAD is authoritative for validation decisions. HANDOFF.md must contain the Status Packet, files list, and checks — but need not include the exact final commit hash (which may shift during closeout).

## Current Phase

Pilot only. PM is the only role with a Hermes Kanban binding. Implementers and validators remain on the OpenClaw production path. Kanban may track their tasks for visibility but must not gate their workflows.
