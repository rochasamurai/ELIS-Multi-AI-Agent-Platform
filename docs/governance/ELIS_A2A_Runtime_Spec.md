# ELIS A2A Runtime Specification

> PE: PE-OPS-A2A-RUNTIME-01  
> Status: active  
> Implementer: infra-impl-a  
> Base branch: main  
> Date: 2026-05-25

---

## 1. Purpose and Scope

This document defines the governance boundaries, message contract, and rollback approach for the **ELIS local A2A transport layer** introduced by PE-OPS-A2A-RUNTIME-01.

The A2A layer enables ELIS agents to exchange structured coordination messages on the same host without routing every internal signal through Discord.  Discord remains the **exclusive PO-facing channel**.

---

## 2. What A2A Is

- A **passive, local, file-based** message transport between ELIS agents running on the same host.
- A coordination signal bus: agents can exchange status updates, task-state changes, evidence references, reset acknowledgements, and failure notifications.
- An internal visibility layer that supplements — and never replaces — the existing PE workflow evidence trail.
- Implemented as a Python module (`scripts/a2a_local_transport.py`) with a JSON Schema envelope (`schemas/a2a_message.schema.json`).
- Transport mechanics: one JSON file per message, stored under `/tmp/elis_a2a/<recipient>/`, no sockets, no HTTP, no external network calls of any kind.

---

## 3. What A2A Is Not

The A2A transport layer explicitly **cannot** and **must not**:

| Prohibited action | Rationale |
|---|---|
| Claim or exercise governance authority | Governance decisions remain with the PM and PO via Discord and the PE workflow |
| Claim or exercise merge authority | Merges are executed by the GitHub Agent only after PO/PM approval; A2A plays no part |
| Bypass PO approval | PO approval gates are enforced by branch protection and CI; A2A messages carry no approval signals |
| Bypass implementer/validator gate checks | Gate checks (black, ruff, pytest, HANDOFF, REVIEW) are CI-enforced; A2A cannot alter their outcome |
| Replace PE evidence requirements | Evidence (command output, HANDOFF, REVIEW files) must still be produced and committed per §2.4 of AGENTS.md |
| Route PO-facing communications | All communications visible to the PO occur via Discord |
| Change runtime configuration or services | The transport is purely file-based; no daemons, no config changes, no service restarts |
| Carry authentication or secrets | Messages must not contain tokens, credentials, or secret values |

---

## 4. Message Types

All messages conform to `schemas/a2a_message.schema.json`.  The five permitted message types are:

| Type | Purpose | Typical sender → recipient |
|---|---|---|
| `status` | Report the current operational status of an agent or PE | pm → supervisor, advisor → pm |
| `reset_ack` | Acknowledge a workspace or context reset | supervisor → pm, impl → pm |
| `task_state` | Notify of a PE or task state transition | pm → supervisor, pm → advisor |
| `evidence_ref` | Reference a committed evidence artefact | impl → pm, val → pm |
| `failure` | Signal a detected failure condition for awareness | any → pm |

### 4.1 Message envelope fields

| Field | Required | Type | Description |
|---|---|---|---|
| `message_id` | Yes | UUID string | Unique identifier for this message |
| `sender` | Yes | string | Sending agent name (e.g. `pm`, `supervisor`, `advisor`) |
| `recipient` | Yes | string | Receiving agent name or `broadcast` |
| `message_type` | Yes | enum (see §4) | One of the five permitted types |
| `payload` | Yes | object | Message body; content schema depends on type |
| `timestamp` | Yes | ISO 8601 string | UTC creation timestamp |
| `pe_id` | No | string | PE identifier this message relates to |

---

## 5. Governance Constraints (hard rules)

The following constraints are **non-negotiable** and are verified by the test suite:

1. `A2ATransport.has_governance_authority` must equal `False`.
2. `A2ATransport.has_merge_authority` must equal `False`.
3. `A2ATransport.can_bypass_po_approval` must equal `False`.
4. `A2ATransport.can_bypass_gate_checks` must equal `False`.
5. `A2ATransport` must not expose `approve`, `merge`, or `grant_authority` methods.

Any future modification to `scripts/a2a_local_transport.py` that introduces such attributes or methods is a scope violation and must be rejected by the Validator.

---

## 6. Rollback Approach

Because the A2A layer is purely additive and does not modify any runtime configuration, service, or CI workflow, rollback is straightforward:

1. **Revert the four authorised files** via `git revert <commit-sha>` or by reverting the PR.
2. No service restarts are required.
3. No configuration changes are required.
4. No database or state cleanup is required — `/tmp/elis_a2a/` is ephemeral and is not committed to the repository.

Partial rollback (e.g., removing the transport but keeping the schema) is also safe because the files have no mutual runtime dependency outside the test suite.

---

## 7. Authorised File Scope

Only the following files are part of this PE:

| File | Role |
|---|---|
| `schemas/a2a_message.schema.json` | JSON Schema envelope definition |
| `scripts/a2a_local_transport.py` | Transport module |
| `tests/test_a2a_local_transport.py` | Pytest test suite |
| `docs/governance/ELIS_A2A_Runtime_Spec.md` | This governance boundary document |

No runtime files, CI workflows, service configurations, or secret stores are included.

---

## 8. References

- `AGENTS.md` §2.4 — Evidence-first reporting
- `AGENTS.md` §13 — Secrets isolation policy
- `schemas/a2a_envelope.schema.json` — Pre-existing Phase-1 A2A envelope schema (distinct from this PE's schema)
- `docs/governance/ELIS_A2A_Communication_Matrix.md` — Broader A2A communication matrix
