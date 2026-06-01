# ALTERNATION WAIVER — PE-OPS-OPENCLAW-CLI-PATH-01

> Classification: OPS_AGENT_ALTERNATION_RULE_VIOLATION_AT_PE_OPENING
> Waiver status: GRANTED (PO, 2026-06-01)

---

## Violation

| Field | Value |
|---|---|
| PE | PE-OPS-OPENCLAW-CLI-PATH-01 |
| Domain | ops |
| Actual implementer | `infra-impl-b` (engine: claude) |
| Expected implementer (by alternation) | `infra-impl-a` (engine: codex) |
| Validator | `infra-val-a` |

**Rule violated:** AGENTS.md §2.1 — alternation rule. The last two merged ops-domain PEs before this one were:

| PE | Implementer | Engine |
|---|---|---|
| `PE-OPS-WORKTREE-BINDING-02` | `infra-impl-b` | claude |
| `PE-OPS-PO-ADVISOR-01` | `infra-impl-b` | claude |

The correct next ops implementer should have been `infra-impl-a` (codex). PM selected `infra-impl-b` by incorrectly treating `PE-OPS-A2A-PRODUCTION-02` (infra-impl-a) as the last merged ops PE, without accounting for the two later merged ops PEs listed above.

## Root Cause

PM's PE-opening logic used a partial recent context when reading the ops-domain merged history. The two ops PEs merged between `PE-OPS-A2A-PRODUCTION-02` and this PE were not included in the alternation check.

## Waiver Rationale

PO grants a one-time waiver for the following reasons:

1. The actual host/systemd operation (Gate 2) was executed by ELIS Supervisor — not infra-impl-b.
2. infra-impl-b committed evidence artefacts (HANDOFF.md) only; no product code was changed.
3. infra-val-a performed independent validation (V2 PASS confirmed).
4. The PE is complete and validated; redoing with `infra-impl-a` would add no assurance and create unnecessary churn.
5. The violation is recorded transparently in this artefact.

## PO Approval

Approved by: Carlos Rocha (PO), 2026-06-01

Scope: one-time, this PE only.

## Hard Constraints

- This waiver does **not** change the alternation rule globally.
- Future ops PEs must alternate correctly from `infra-impl-b` (i.e., the next ops implementer must be `infra-impl-a`).
- The implementer record in `CURRENT_PE.md` is **not** falsified; `infra-impl-b` is correctly recorded as the actual implementer.

## Required Follow-up

PM PE-opening logic must be updated to scan the full merged ops registry (all rows, in table order) rather than relying on partial recent context. This is recorded as a lesson in `LESSONS_LEARNED.md`.

## Reference

- AGENTS.md §2.1 — alternation rule
- CURRENT_PE.md — registry row for PE-OPS-OPENCLAW-CLI-PATH-01
- `check_current_pe.py` — `_validate_alternation()` — no approved waiver bypass mechanism exists in the script; this file serves as the transparency record only
