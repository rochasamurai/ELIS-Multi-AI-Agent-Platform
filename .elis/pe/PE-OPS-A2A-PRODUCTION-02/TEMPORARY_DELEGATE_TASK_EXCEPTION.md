# TEMPORARY_DELEGATE_TASK_EXCEPTION — PE-OPS-A2A-PRODUCTION-02

> Repo artefact. PM-authored. Committed before Implementer dispatch.
> This exception record is part of the auditable provenance chain
> for PE-OPS-A2A-PRODUCTION-02.

---

## Exception metadata

| Field | Value |
|-------|-------|
| PE ID | PE-OPS-A2A-PRODUCTION-02 |
| Delegating agent | PM (`pm`) |
| Receiving agent — Implementer | `infra-impl-a` |
| Receiving agent — Validator | `infra-val-b` |
| Issued | 2026-05-29 |
| PM sign-off | PM-CHORE-108 |

---

## Justification

A2A and Kanban-based dispatch are not yet production-ready. Until those
mechanisms are operational and validated, the PM must delegate PE tasks
to Implementer and Validator agents via the configured agentId dispatch
path in OpenClaw. This exception permits that temporary delegation for
the duration of PE-OPS-A2A-PRODUCTION-02.

This PE was opened specifically because PE-OPS-A2A-PRODUCTION-01 was
contaminated by dispatch provenance failures. The constraints in this
exception directly address the root causes of that contamination.

---

## Scope

This exception covers:
- Gate 1 (discovery and planning pass) by `infra-impl-b`
- Gate 2 (validation) by `infra-val-a`
- Any subsequent gates explicitly approved by PM within this PE

---

## Permitted dispatch method

- **Configured agentId dispatch** via OpenClaw (`sessions_send` to
  the configured agentId, routed to the agent's live workspace)

---

## Forbidden dispatch methods (hard block — no exceptions)

The following methods are explicitly forbidden for all work under
this exception and for all phases of PE-OPS-A2A-PRODUCTION-02:

| Method | Reason |
|--------|--------|
| `acp_command` (any form) | Bypasses agentId binding and provenance chain |
| `sessions_spawn` (raw or PM-subagent path) | Creates unbound session in wrong CWD/worktree |
| `raw_acp` | Direct ACP without configured agentId; no workspace binding |
| `manual_pm_execution` | PM operating in agent role; violates role separation |
| PM worktree execution | Any agent running from `/opt/elis/agent-worktrees/pm`; violates workspace binding |

Any use of a forbidden method voids this exception and renders the
affected result contaminated.

---

## Constraints

1. Dispatch must target the agent's configured workspace as recorded
   in `/home/samurai/.openclaw/openclaw.json` (live config):
   - `infra-impl-a` → `/opt/elis/agent-worktrees/infra-impl-a` (live: openrouter/qwen/qwen3-coder-flash)
   - `infra-val-b`  → `/opt/elis/agent-worktrees/infra-val-b`  (live: openrouter/z-ai/glm-5.1)

2. Every dispatched result must include a filled
   `DISPATCH_PROVENANCE_PROOF_V1` (14-field schema in `PE_TASK.md`).
   PM must verify the proof before accepting any result.

3. The PE branch (`feature/pe-ops-a2a-production-02-productionise-a2a-dispatch-provenance-controls`)
   must be checked out in the agent's fixed workspace before work begins.

4. No content from PE-OPS-A2A-PRODUCTION-01 branches may enter this
   PE branch via any git operation.

---

## Sunset condition

This exception expires when **A2A/Kanban dispatch is production-ready**
and validated as the authoritative dispatch mechanism for ELIS agents.

At that point:
- PM delegate_task path must be removed or disabled
- All future PEs must dispatch exclusively via the A2A/Kanban path
- This file remains in the repo as a historical record; it is not
  deleted on sunset

---

## PM sign-off

PM-CHORE-108 · 2026-05-29 · Authorised by PO (PE_OPENING_PLAN_V4 accepted)
