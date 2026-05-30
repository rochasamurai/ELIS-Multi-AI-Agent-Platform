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
- Gate 1 (discovery and planning pass) by `infra-impl-a`
- Gate 2 (validation) by `infra-val-b`
- Any subsequent gates explicitly approved by PM within this PE

---

## Permitted dispatch method

- **`sessions_spawn.agentId`** — `sessions_spawn` called with an explicit
  `agentId` matching a configured agent, `context="isolated"`,
  `cleanup="keep"`, `runtime="subagent"`, explicit `cwd` set to the
  agent's live workspace from `~/.openclaw/openclaw.json`, and a
  `taskName` that includes the PE ID and gate.

Required parameters for every permitted dispatch:

| Parameter | Required value |
|-----------|---------------|
| `agentId` | assigned agent (infra-impl-a or infra-val-b) |
| `cwd` | agent workspace from live `~/.openclaw/openclaw.json` |
| `context` | `"isolated"` |
| `cleanup` | `"keep"` |
| `runtime` | `"subagent"` |
| `taskName` | must include PE ID and gate label |
| `runTimeoutSeconds` | bounded value (≤ 600) |

---

## Forbidden dispatch methods (hard block — no exceptions)

The following methods are explicitly forbidden for all work under
this exception and for all phases of PE-OPS-A2A-PRODUCTION-02:

| Method | Reason |
|--------|--------|
| `sessions_spawn` without `agentId` | Inherits PM CWD/context; no workspace binding |
| `sessions_spawn` with `runtime="acp"` | ACP runtime path; bypasses provenance chain |
| `sessions_spawn` with `acp_command` | ACP command path; bypasses agentId binding |
| `sessions_send` for dispatch | Cross-agent send; blocked by visibility gate; not a dispatch path |
| `delegate_task` for dispatch | Tool not present in PM tool suite |
| `delegate_task.acp_command` | ACP command path; forbidden |
| `acp_command` (any form) | Bypasses agentId binding and provenance chain |
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
- PM sessions_spawn.agentId path must be replaced by the A2A/Kanban dispatch path
- All future PEs must dispatch exclusively via the A2A/Kanban path
- This file remains in the repo as a historical record; it is not
  deleted on sunset

---

## PM sign-off

PM-CHORE-108 · 2026-05-29 · Authorised by PO (PE_OPENING_PLAN_V4 accepted)
