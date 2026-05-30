# PE_TASK — PE-OPS-A2A-PRODUCTION-02

> PM-authored. Committed before Implementer dispatch.
> Implementer reads this file as Step 0 after CURRENT_PE.md.

---

## Identity

| Field | Value |
|-------|-------|
| PE ID | PE-OPS-A2A-PRODUCTION-02 |
| Title | Productionise A2A Dispatch Under Provenance Controls |
| Domain | ops |
| Lane | Strict |
| Branch | feature/pe-ops-a2a-production-02-productionise-a2a-dispatch-provenance-controls |
| Baseline | adbae97fa96af1877106ca4523ee05340f5d1a6a |
| Implementer | infra-impl-a |
| Validator | infra-val-b |
| Opened | 2026-05-29 |
| PM-CHORE | 108 |

---

## Objective

Put the ELIS A2A internal agent communication layer into production with
full dispatch provenance controls. This PE supersedes the contaminated
PE-OPS-A2A-PRODUCTION-01, which was invalidated due to:

- WRONG_IMPLEMENTER_EXECUTION (infra-impl-a assigned; infra-impl-b ran)
- WRONG_WORKTREE_EXECUTION (ran from PM worktree /opt/elis/agent-worktrees/pm)
- PM_SUBAGENT_DISPATCH_CWD_ERROR (spawned as PM subagent, not own session)
- DISPATCH_PROVENANCE_FAILURE (no provenance proof; review authorship unverifiable)

No content from PE-OPS-A2A-PRODUCTION-01 branches may be cherry-picked
or rebased into this PE branch. Plan/spec docs on main may be read as
prior work only.

---

## Dispatch constraints

See `TEMPORARY_DELEGATE_TASK_EXCEPTION.md` in this directory.

Forbidden dispatch methods (hard block):
- `sessions_spawn` without `agentId`
- `sessions_spawn` with `runtime="acp"`
- `sessions_spawn` with `acp_command`
- `sessions_send` for dispatch
- `delegate_task` for dispatch
- `delegate_task.acp_command`
- `acp_command` (any form)
- `raw_acp`
- `manual_pm_execution` (PM operating in agent role)
- PM worktree execution (running from /opt/elis/agent-worktrees/pm)

Permitted dispatch method:
- `sessions_spawn.agentId` — `sessions_spawn` with explicit `agentId`,
  `context="isolated"`, `cleanup="keep"`, `runtime="subagent"`,
  `cwd` = agent workspace from live `~/.openclaw/openclaw.json`,
  `taskName` includes PE ID and gate label

---

## Authoritative config

Config source for workspace binding and model/provider:
  `/home/samurai/.openclaw/openclaw.json` (live, Supervisor-verified)

Stale and out of scope:
  `/opt/elis/repo/openclaw/openclaw.json`

Verified agent bindings (re-read live config immediately before dispatch):

| agentId | workspace | model |
|---------|-----------|-------|
| infra-impl-a | /opt/elis/agent-worktrees/infra-impl-a | openrouter/qwen/qwen3-coder-flash |
| infra-val-b  | /opt/elis/agent-worktrees/infra-val-b  | openrouter/z-ai/glm-5.1           |

---

## First-pass scope (Strict lane)

Gate 1 — read-only discovery and planning only. No implementation,
no config edits, no live routing, no runtime directory creation.

Allowed writes (Implementer):
- `.elis/pe/PE-OPS-A2A-PRODUCTION-02/HANDOFF.md`
- `.elis/pe/PE-OPS-A2A-PRODUCTION-02/A2A_Production_Plan.md`
- `.elis/pe/PE-OPS-A2A-PRODUCTION-02/A2A_Production_Risk_Rollback.md`

Allowed reads:
- `scripts/a2a_local_transport.py`
- `tests/test_a2a_local_transport.py`
- `schemas/a2a_envelope.schema.json`
- `schemas/a2a_message.schema.json`
- `docs/governance/ELIS_A2A_*.md`
- `docs/openclaw/ELIS_A2A_GATEWAY_SPEC.md`
- `.elis/pe/PE-OPS-A2A-PRODUCTION-01/` (read-only reference)
- Read-only runtime/config inspection on elis-server

Not allowed in first pass:
- Runtime code changes (scripts/, elis/, tests/)
- OpenClaw/Hermes mutation or config change
- Service restart or reload
- A2A live routing enablement
- Runtime directory creation (`/opt/elis/a2a/` or similar)
- New `docs/ops/a2a/` directory
- PR creation

Hard stops (all phases):
- Do not edit OpenClaw/Hermes config
- Do not restart or reload services
- Do not create `/opt/elis/a2a/`
- Do not enable A2A routing
- Do not create PR without explicit PM instruction
- A2A remains disabled by default until explicit PO enablement

---

## Validator review artefact

Canonical path for this PE:
`.elis/pe/PE-OPS-A2A-PRODUCTION-02/REVIEW_PE-OPS-A2A-PRODUCTION-02.md`

Root-level HANDOFF.md is NOT used. Canonical HANDOFF path:
`.elis/pe/PE-OPS-A2A-PRODUCTION-02/HANDOFF.md`

---

## DISPATCH_PROVENANCE_PROOF_V1  (14-field — mandatory)

The Implementer must submit a filled proof in their opening Status Packet
before any work is accepted. The Validator must submit a separate filled
proof before their review is accepted. PM verifies both proofs.

The Implementer does not define, amend, or interpret this schema.

```
DISPATCH_PROVENANCE_PROOF_V1
requested_agent_id:          <must match CURRENT_PE.md assignment>
actual_agent_id:             <agentId of the session that ran the work>
actual_session_id:           <OpenClaw session key>
actual_cwd:                  <working directory at execution time>
actual_worktree:             <output of: git rev-parse --show-toplevel>
branch:                      <output of: git branch --show-current>
head:                        <output of: git rev-parse HEAD>
git_identity:                <output of: git config user.name and user.email>
model_provider_profile:      <model/provider from session_status; must match
                              live ~/.openclaw/openclaw.json entry>
dispatch_method:             <how this session was invoked>
openclaw_config_agent_match: <PASS if actual_worktree matches workspace in
                              ~/.openclaw/openclaw.json for actual_agent_id;
                              else FAIL>
acp_command_not_used:        <PASS if no acp_command was invoked; else FAIL>
pm_worktree_not_used:        <PASS if actual_worktree ≠
                              /opt/elis/agent-worktrees/pm; else FAIL>
dispatch_timestamp:          <ISO-8601 timestamp of session start>
```

Validity rule: any FAIL in the three boolean fields → result rejected
without review.

Config source for `openclaw_config_agent_match`:
  `/home/samurai/.openclaw/openclaw.json` (live)
  NOT `/opt/elis/repo/openclaw/openclaw.json` (stale)
