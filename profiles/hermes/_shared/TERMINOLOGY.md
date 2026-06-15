# ELIS Terminology — Canonical Definitions

This document is authoritative for all five ELIS Hermes profiles. When a term is used in any SOUL.md, AGENTS.md, SKILLS.md, or governance document, it carries the meaning defined here.

## Roles

- **PO (Product Owner):** Carlos Rocha. The sole authority for ELIS platform decisions, PE approval, merge approval, productionisation, and governance. All directives originate from PO.

- **PE (Platform Engineering):** A bounded unit of ELIS platform work. A PE has: an ID, scope, assigned agents (implementer + validator), evidence checklist, approval gates, and a designated PM coordinator. No PE is active until PO opens it.

- **PM (Project Manager):** ELIS PM agent. Coordinates PE workflow via Kanban task decomposition and dispatch. Does not implement, validate, or write to source control.

- **Advisor:** ELIS Advisor agent. PO decision-support and governance review. Produces structured verdicts, risk classifications, and safe-next-action recommendations. Advisory only — never decides or acts.

- **Supervisor:** ELIS Supervisor agent. Platform operations and live profile/runtime execution owner. Diagnoses, fixes, verifies, and reports — within PO-approved scope only.

- **Ideas:** ELIS Ideas agent. Research, idea capture, and exploration. Captures and develops ideas for later review by Advisor or PM.

- **GitHub (elis-github):** ELIS GitHub agent. GitHub operations only — within tiered governance gates. Currently in SETUP phase.

- **Implementer:** A PE-assigned agent that writes code. Must be separate from the validator. (Role definition — no specific deployed agent at present.)

- **Validator:** A PE-assigned agent that validates implementation. Must be separate from the implementer. (Role definition — no specific deployed agent at present.)

## Processes

- **Kanban:** The ELIS coordination mechanism. A shared board (`/home/samurai/.hermes/kanban.db`) used by PM to create, decompose, track, and dispatch PE tasks. Operational coordination state — not final governance authority.

- **Gate:** A checkpoint within a PE where evidence is gathered, reviewed, and approved (by Advisor, PO, or both) before proceeding to the next phase. Gates are sequential and must not be skipped.

- **Handoff:** Transfer of a bounded task scope from one agent to another. Requires: source agent, target agent, PE ID, scope, constraints, expected output format, and PO awareness.

- **Reset/Binding Acknowledgement:** A mandatory pre-engagement statement from any agent entering a PE session. Must include: identity, PE ID, role, scope, branch, HEAD, git status, timestamp, prior-context-discarded, and scope-boundary.

- **Productionisation:** The PO declaration that transitions `elis-github` from SETUP phase to PRODUCTION phase, enabling Tier 1 operations within PE handoff envelopes. A single, explicit PO statement in `#elis-github`.

## Evidence and Approval

- **Evidence:** Verifiable command output, file state, hash, or agent report that demonstrates a gate requirement has been met. Must include exact commands and provenance.

- **Approval Gate:** A PO decision point. No PE phase proceeds without PO approval. Advisor may recommend; PO decides.

- **Hard Stop:** A condition that halts all progress on a PE or operation. Must be reported immediately. Examples: dirty working tree, auth failure, scope violation, tier violation, secret exposure risk.

- **Tier (GitHub):** The four-level operation classification for elis-github. Tier 0 = always allowed (read/status). Tier 1 = allowed within PE handoff envelope (BLOCKED during setup). Tier 2 = explicit PO per-PR approval. Tier 3 = always denied.

## States

- **BLOCKED:** Cannot proceed. A hard stop or missing approval prevents progress.
- **READY_FOR_REVIEW:** All evidence gathered; awaiting Advisor or PO review.
- **APPROVED:** PO has authorised the next phase or operation.
- **SETUP:** Pre-productionisation state. Tier 1+ mutations blocked.
- **PRODUCTION:** Post-productionisation state. Tier 1 available within PE handoff scope.

## Model/Provider Agnostic

**Model/provider agnostic** means ELIS Core behaviour and governance remain stable when the runtime model, provider, fallback model, or inference route changes. Identity files (SOUL.md), governance documents (_shared/*.md), role definitions (AGENTS.md), and skill definitions (SKILLS.md) must not depend on any specific AI model or provider. Model/provider details belong only in `config.yaml`.