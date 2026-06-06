# GitHub Transition Rule — ELIS/Hermes Migration

**PEs:** PE-OPS-HERMES-PM-MIGRATION-01  
**Status:** In effect — do not bridge until validated  
**Date:** 2026-06-05

---

## Current State

ELIS GitHub operations (PR creation, merge, push, branch management) are executed through the **existing OpenClaw PM → ELIS GitHub Agent** path. This path is production and authoritative.

## Rule

> **Until ELIS GitHub is migrated to Hermes or a governed cross-runtime bridge is validated, GitHub tasks continue through the existing OpenClaw PM → ELIS GitHub path.**

## Hermes/Kanban GitHub Boundaries

| Allowed | Not Allowed |
|---|---|
| Track GitHub task status in Kanban (visibility only) | Direct GitHub operations from Hermes PM |
| Reference GitHub PR/issue URLs in Kanban task bodies | Hermes PM creating PRs, pushing, or merging |
| Kanban task notes about GitHub-related workflow state | Hermes PM using `gh` CLI or GitHub API for writes |

## ELIS PM Pilot Constraint

The ELIS PM pilot profile (`elis-pm`) has:
- **No `terminal` toolset** — cannot execute `gh` CLI commands
- **No `file` toolset** — cannot read/write repository files
- **No GitHub write authority** — enforced at Hermes profile level
- **Kanban-only toolset** — coordination without execution

## Future Migration Gate

Before ELIS GitHub can be migrated to Hermes or bridged across runtimes:

1. A governed cross-runtime bridge must be designed and approved by PO
2. GitHub Agent auth must be validated under Hermes (not assumed from OpenClaw)
3. A migration test must demonstrate PR create, merge, and cleanup on a non-production repo
4. Rollback to OpenClaw GitHub path must remain available

## No Action Without PO Approval

No GitHub write authority changes, no `gh` token sharing across runtimes, no cross-runtime GitHub bridging without explicit PO approval and a dedicated PE.
