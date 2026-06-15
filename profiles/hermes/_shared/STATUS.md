# ELIS Status Snapshot Convention

This document defines the status snapshot concept for ELIS Hermes profiles. This is a design/documentation convention only — no scripts or automated implementation is authorised without a separate PE.

## Purpose

Each ELIS profile should be able to produce a standardised status snapshot on PO request. The snapshot provides a consistent view of the agent's current operational state.

## Status Snapshot Fields

Every status snapshot must include:

| Field | Description | Required |
|---|---|---|
| `agent` | Profile name (elis-ideas, elis-advisor, elis-pm, elis-supervisor, elis-github) | Yes |
| `timestamp` | ISO 8601 timestamp | Yes |
| `role_state` | Current operational state: `IDLE`, `ACTIVE`, `BLOCKED`, `REVIEWING`, `EXECUTING` | Yes |
| `current_pe` | Active PE ID if currently engaged in a PE; `NONE` otherwise | Yes |
| `current_task` | Current Kanban task ID if executing a task; `NONE` otherwise | Yes |
| `readiness` | `READY`, `NOT_READY`, `MAINTENANCE` | Yes |
| `blockers` | List of active blockers preventing progress; `NONE` if clear | Yes |
| `last_action` | Brief description of the last completed action with timestamp | Yes |
| `evidence_path` | Reference to the last evidence produced (e.g., Kanban comment, file path, message ID) | Yes |
| `next_approval_required` | Description of the next PO approval gate; `NONE` if idle | Yes |
| `session_health` | `HEALTHY`, `DEGRADED`, `NEEDS_HANDOFF` | Yes |

## Per-Profile Role State Values

### elis-ideas
- `IDLE` — no active capture or research
- `CAPTURING` — actively saving an idea
- `RESEARCHING` — actively researching a topic
- `ESCALATING` — escalating a finding to PO

### elis-advisor
- `IDLE` — no active review
- `REVIEWING` — actively reviewing a packet
- `AWAITING_EVIDENCE` — waiting for additional evidence from PO
- `VERDICT_READY` — verdict produced, awaiting PO acknowledgment

### elis-pm
- `IDLE` — no active PE coordination
- `COORDINATING` — actively managing PE tasks
- `SYNTHESISING` — compiling status across tasks
- `AWAITING_AGENT` — waiting for agent evidence
- `AWAITING_PO` — waiting for PO approval

### elis-supervisor
- `IDLE` — no active diagnostic or change
- `DIAGNOSING` — actively diagnosing an issue
- `AWAITING_APPROVAL` — change proposed, awaiting PO approval
- `EXECUTING` — applying an approved change
- `ROLLING_BACK` — reverting a failed change

### elis-github
- `IDLE` — no active operation
- `SETUP_BLOCKED` — in SETUP phase, Tier 1+ blocked
- `EXECUTING_TIER0` — executing a read-only operation
- `EXECUTING_TIER1` — executing within a PE handoff (production only)
- `AWAITING_TIER2_APPROVAL` — Tier 2 operation proposed, awaiting PO per-PR approval
- `TIER3_REFUSED` — Tier 3 operation was requested and correctly refused

## Snapshot Principle

Status snapshots are the agent's self-report of its current state. They are not authoritative evidence of task completion — they are operational transparency aids. Evidence of completed work is always in the form of command output, file state, or repository artefacts.