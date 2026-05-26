# ELIS AI Business Management Lab — Updated Operational Model

**Document:** `ELIS_Architecture_Updated_Operational_Model_2026-05-20.md`  
**Updated:** 2026-05-26  
**Status:** Operational architecture update after `PE-OPS-A2A-RUNTIME-01` and PR #457  
**Language:** UK English  

---

## 1. Naming and mission update

The renamed public/strategic identity is:

# ELIS AI Business Management Lab  
## AI-Native Software Delivery for Business Leaders

This is accurate based on the approved positioning already discussed:

> ELIS AI Business Management Lab is an AI-native management laboratory that teaches business leaders and students how to define, delegate, govern, validate, and deliver software-enabled business solutions through AI agents, without needing to become advanced programmers.

The internal operational names can continue to be used where useful:

- **ELIS Server** — the Ubuntu server/runtime environment.
- **ELIS Multi-AI Agent Platform** — the engineering/platform repository and architecture.
- **ELIS AI Business Management Lab** — the strategic product, education and research framing.
- **ELIS Supervisor** — canonical name for the read-only supervisory/diagnostic agent.
- **ELIS Advisor** — advisory-only Hermes-hosted PO support role, not yet fully productionised.
- **ELIS PM** — OpenClaw-hosted project/PE coordinator.

This document uses **ELIS AI Business Management Lab** as the strategic name, while preserving **ELIS Server** and **ELIS Platform** for operational clarity.

---

## 2. Current operational architecture

ELIS currently combines:

1. **Discord as the PO-facing interface**
   - PO interacts with PM and Supervisor through Discord.
   - PE-specific threads are used for scoped operational conversations.
   - Thread/session binding remains a critical governance control.

2. **OpenClaw as the main agent runtime**
   - Hosts PM, implementers, validators and GitHub-related agents.
   - Maintains agent configuration and model/provider routing.
   - Uses fixed worktrees under `/opt/elis/agent-worktrees/`.

3. **Hermes as supervisory/advisory runtime**
   - Hosts ELIS Supervisor.
   - Target home for ELIS Advisor.
   - Intended to support advisory, diagnostic and later Kanban/workboard functions.

4. **Git and GitHub as source-of-truth delivery infrastructure**
   - Git branches, commits, PRs, CI and REVIEW artefacts remain authoritative evidence.
   - GitHub write path is intended to be mediated by GitHub Agent, but that path is currently blocked and must be productionised.

5. **A2A local runtime foundation**
   - Newly merged via `PE-OPS-A2A-RUNTIME-01` / PR #457.
   - Provides a local file-based transport, schema, tests and documentation for structured internal agent communication.
   - Not yet a production control plane or dispatch authority.

---

## 3. Recent achievements

### 3.1 `PE-OPS-A2A-RUNTIME-01` completed and merged

`PE-OPS-A2A-RUNTIME-01 — Implement Local A2A Backbone for Structured Agent Communication` was completed and merged through PR #457.

Merged evidence:

- **PR:** `#457`
- **Merge commit:** `72b0da3e94dab7bd1afc2867c7afadb581dc6828`
- **Branch:** `feature/pe-ops-a2a-runtime-01-clean-local-backbone`
- **Final PR head before merge:** `e5691abec97748e0f415b8752536d0a319cc4c4e`
- **Base:** `main`
- **Checks:** all required checks passed before merge.

Validated implementation files:

- `docs/governance/ELIS_A2A_Runtime_Spec.md`
- `schemas/a2a_message.schema.json`
- `scripts/a2a_local_transport.py`
- `tests/test_a2a_local_transport.py`

PE artefacts:

- `.elis/pe/PE-OPS-A2A-RUNTIME-01/PE_TASK.md`
- `.elis/pe/PE-OPS-A2A-RUNTIME-01/HANDOFF.md`
- `.elis/pe/PE-OPS-A2A-RUNTIME-01/REVIEW.md`

State/registry files:

- `CURRENT_PE.md`
- `.elis/state/current_pe.json`

Validation result:

- Original intended validator path restored to `infra-val-b`.
- Validator verdict: **PASS**.
- A2A local transport tests: **30/30 passed**.
- Dispatch contract tests after CI correction: **7/7 passed**.
- No runtime, service, auth, provider or OpenClaw/Hermes config changes were included.

### 3.2 A2A local capability now exists

The merged A2A runtime provides a local, file-based foundation for structured messages between ELIS agents.

The current scope is intentionally limited to local runtime primitives, including:

- message schema;
- local transport;
- file-backed mailbox under `/tmp/elis_a2a/`;
- structured message types;
- tests for local round-trip behaviour;
- governance documentation clarifying non-authority boundaries.

The A2A runtime is **not yet production dispatch infrastructure**.

It must not yet:

- dispatch agents;
- approve work;
- bypass PO approval;
- bypass implementer/validator gates;
- replace `HANDOFF.md`, `REVIEW.md`, Git commits or PR evidence;
- push, merge or create PRs;
- act as governance authority.

### 3.3 PM model changed successfully

The PM runtime was moved to:

- `claude-cli/claude-sonnet-4-6`

The live PM configuration change was later verified as isolated. It did not overwrite the live OpenRouter model matrix for infra/prog agents.

### 3.4 Live OpenClaw model matrix preserved

A suspected model configuration drift was investigated.

Conclusion:

- Live `~/.openclaw/openclaw.json` remains authoritative for runtime.
- PM now uses Claude CLI.
- Infra/prog implementers and validators remain OpenRouter-based in the live runtime matrix.
- The drift is between live runtime config and repo/docs config, not a live runtime overwrite.

Accepted live runtime matrix for key agents:

| Agent | Live model |
|---|---|
| `pm` | `claude-cli/claude-sonnet-4-6` |
| `infra-impl-a` | `openrouter/qwen/qwen3-coder-flash` |
| `infra-impl-b` | `openrouter/deepseek/deepseek-v4-flash` |
| `infra-val-a` | `openrouter/deepseek/deepseek-v4-pro` |
| `infra-val-b` | `openrouter/z-ai/glm-5.1` |
| `prog-impl-a` | `openrouter/qwen/qwen3-coder-flash` |
| `prog-impl-b` | `openrouter/deepseek/deepseek-v4-flash` |
| `prog-val-a` | `openrouter/deepseek/deepseek-v4-pro` |
| `prog-val-b` | `openrouter/z-ai/glm-5.1` |

Future task registered:

`PE-OPS-OPENCLAW-CONFIG-SYNC-01 — Align Repo/Docs OpenClaw Model Matrix with Live Runtime`

### 3.5 GitHub Agent blocker identified

GitHub Agent could not be used to push and create PR #457.

Supervisor diagnosis found:

- `github-agent` is registered in OpenClaw.
- `github-agent` is not currently enabled.
- Fresh GitHub Agent session spawn is blocked.
- Required credential file is missing:
  - `/opt/elis/secrets/github-agent.env`
- Worktree-local `GH_CONFIG_DIR` access fails due to permission issues.
- Ambient `gh` identity available is `rochasamurai`, while intended GitHub Agent identity is:
  - `elis-git-bot <elis-git-bot@electoralintegrity.org>`

PR #457 was therefore pushed/created manually by PO as an explicit exception.

Classification:

- `GITHUB_AGENT_PRODUCTION_BLOCKED`
- `GITHUB_AGENT_CREDENTIAL_PATH_MISSING`
- `GITHUB_AGENT_AUTH_IDENTITY_NOT_VERIFIED`
- `AMBIENT_GH_IDENTITY_UNSAFE_FOR_AGENT_WRITE`

---

## 4. Key lessons from the latest PE

### 4.1 Prompt governance is not enough

The recent PE exposed the difference between:

- rules described in prompts; and
- deterministic controls enforced by software.

ELIS has strong governance language, but parts of the workflow still rely on PM, Supervisor and PO manually discovering state.

The system needs more mandatory execution-path automation, especially for:

- PE preflight;
- branch creation;
- target-agent worktree binding;
- branch/commit propagation;
- session reset and acknowledgement;
- dispatch manifests;
- GitHub readiness;
- closeout and state transitions.

### 4.2 Target-agent worktree binding must be preflighted before dispatch

A major recurring failure mode was:

> PM worktree was clean and correct, but implementer/validator worktrees were stale, detached, or missing the expected commit.

New rule to enforce:

`NO_TARGET_AGENT_CLEAN_BRANCH_BINDING_NO_DISPATCH`

PM must not dispatch an implementer or validator until the target agent’s authorised worktree is cleanly bound to the approved PE branch or exact commit.

Required evidence:

- agent identity;
- authorised worktree;
- current branch or detached state;
- current HEAD;
- expected branch;
- expected HEAD;
- merge-base;
- status;
- branch diff;
- stale branch check;
- opening/implementation commit reachability.

### 4.3 Git linked worktree branch exclusivity is a real operational constraint

Git prevents the same named branch from being checked out in multiple linked worktrees at the same time.

This affected validator binding and required detached HEAD validation for some flows.

ELIS must treat this as a normal design constraint, not an exception.

Acceptable patterns:

- implementer holds the named PE branch;
- validator checks out the exact target commit in detached HEAD;
- PM/GitHub Agent uses an authorised branch source for integration/push;
- final branch consolidation happens through a controlled owner.

### 4.4 Validator substitution must preserve engine-pairing invariants

The temporary `infra-val-a` substitution was useful recovery evidence, but it violated the current opposite-engine rule because both implementer and substitute validator resolved to the same engine class.

The corrected path was to revalidate with the originally assigned opposite-engine validator `infra-val-b`.

Lesson:

- Validator substitution is allowed only if it preserves governance invariants, or if PO explicitly authorises a rule change.
- Do not “fix” CI by misrepresenting the actual validator.
- Do not weaken `check_current_pe.py` to fit an exception unless the governance rule itself is being deliberately revised.

### 4.5 CI exposed real state-contract weaknesses

PR #457 initially failed CI because:

1. `CURRENT_PE.md` contained non-canonical role/status strings after validator substitution.
2. `current_pe.json` used a state not accepted by the current checker.
3. `tests/test_pm_dispatch_contract.py` had brittle expectations for active PE state.
4. A historical registry domain classification error caused the alternation checker to compare against the wrong previous PE.

Fixes included:

- canonical `Validator` role field;
- canonical `infra-val-b` validator agent id;
- canonical `gate-2-pending` state;
- minimal dispatch contract test update;
- registry correction for Advisor domain classification.

Lesson:

- `CURRENT_PE.md` is too brittle as a machine source of truth.
- `.elis/state/current_pe.json` should become the canonical machine-readable PE state.
- `CURRENT_PE.md` should be a human-readable rendering checked against JSON, not the primary machine parser target.

### 4.6 GitHub Agent must be productionised before it can be relied upon

The intended governance path is:

`PO → PM → GitHub Agent → GitHub`

But PR #457 proved that this path is not yet operational.

Until fixed, manual PO GitHub operations may be required as explicit exceptions. This should not become normal practice.

### 4.7 A2A should support control-plane evidence, not become authority

A2A should record structured operational events such as:

- `PE_OPENED`
- `AGENT_BOUND`
- `TASK_DISPATCHED`
- `TASK_STARTED`
- `TASK_BLOCKED`
- `HANDOFF_READY`
- `VALIDATION_STARTED`
- `VALIDATION_PASSED`
- `VALIDATION_FAILED`
- `PROVIDER_ERROR`
- `GITHUB_READY`
- `PR_OPENED`
- `PR_MERGED`

But A2A must not approve, dispatch, merge or bypass PO/validator gates.

---

## 5. Current known blockers and risks

### 5.1 GitHub Agent production blocker

GitHub Agent is registered but not enabled/usable.

Required future work:

- restore credential mount/env file;
- fix `GH_CONFIG_DIR` permissions;
- verify `elis-git-bot` identity;
- prevent ambient `rochasamurai` identity from being used for automated GitHub writes;
- validate GitHub Agent can perform read-only readiness, push and PR creation under governance.

### 5.2 Repo/docs model matrix drift

Live runtime config is currently authoritative, but repo/docs config does not match live model assignments.

Risk:

- operators and agents may read the wrong config layer;
- provider/billing/auth incidents may be misdiagnosed;
- future changes may overwrite the live OpenRouter matrix.

### 5.3 Control plane not yet implemented

Existing scripts are useful checks, but they are not yet a complete mandatory execution path.

Needed capabilities:

- prepare PE branch;
- bind agents;
- propagate commits;
- validate reset/session/thread;
- generate dispatch manifest;
- block unsafe dispatch;
- report status in machine-readable form.

### 5.4 A2A not yet in production

A2A runtime is merged but not integrated into live workflows.

A pilot is needed before production use.

### 5.5 ELIS Advisor not yet productionised

Advisor must still receive a formal production handoff/cutover on Hermes.

---

## 6. Updated next PE sequence

Recommended order after closing `PE-OPS-A2A-RUNTIME-01`:

### 1. `PE-OPS-GITHUB-AGENT-PRODUCTION-01`

**Title:** Restore and Productionise GitHub Agent Write Path

Objective:

- make GitHub Agent the verified, least-privilege, auditable GitHub write path for ELIS.

Scope:

- restore `/opt/elis/secrets/github-agent.env` or approved credential mount;
- fix GitHub Agent `GH_CONFIG_DIR` permissions;
- verify `elis-git-bot` identity;
- verify GitHub Agent worktree;
- enable/spawn GitHub Agent through approved route;
- confirm reset/binding acknowledgement;
- perform read-only GitHub readiness checks;
- push/create PR only after PO approval;
- no merge without separate PO approval.

Hard stops:

- no ambient `rochasamurai` GitHub writes by agents;
- no credential copying;
- no branch protection changes;
- no `tools.sessions.visibility=all` ad hoc change;
- no merge automation without PO approval.

Reason this should come first:

- GitHub Agent blocked the normal PR path for PR #457.
- Future PEs need a reliable governed GitHub write path.

---

### 2. `PE-OPS-ADVISOR-PRODUCTION-01`

**Title:** Production Handoff and Cutover for ELIS Advisor on Hermes

Objective:

- put ELIS Advisor into a stable Hermes-hosted production advisory role.

Scope:

- confirm Advisor identity and canonical naming;
- confirm Hermes runtime/session/channel binding;
- confirm only one Advisor instance is active;
- define advisory-only authority;
- receive this GPT/PO handoff context;
- verify monitoring/log behaviour;
- document rollback;
- ensure Advisor cannot dispatch agents, validate officially, push, merge or change runtime config.

Reason this should come before A2A pilot:

- Advisor can help PO/PM make better governance decisions before live A2A workflow integration.
- Advisor can reduce PO load during future control-plane and A2A pilot work.

---

### 3. `PE-OPS-A2A-PILOT-01`

**Title:** Pilot Local A2A Event Flow for ELIS Dispatch Visibility

Objective:

- use the local A2A runtime in a controlled pilot for structured event recording and status visibility.

Scope:

- record events for one controlled PE flow;
- include PE ID, agent, worktree, branch, HEAD, session/thread, timestamp, status, evidence path and failure class;
- keep Discord as PO-facing interface;
- keep PM as coordinator;
- keep Supervisor read-only;
- A2A is evidence/visibility only.

Hard stops:

- A2A must not dispatch agents;
- A2A must not approve work;
- A2A must not replace `HANDOFF.md` or `REVIEW.md`;
- A2A must not push, merge or create PRs;
- A2A must not become governance authority.

---

### 4. `PE-OPS-CONTROL-PLANE-REFERENCES-01`

**Title:** Evaluate Proven Control-Plane Patterns for ELIS

Objective:

- evaluate proven open-source/GitHub patterns for worktree-based AI coding orchestration before building a broader ELIS control plane.

Candidate references:

- Overstory-style worktree + SQLite/mail/event coordination;
- Mission Control/dashboard-style orchestration as observability/control-plane reference only;
- Vibe Kanban/Nimbalyst/Conductor-style worktree boards;
- existing ELIS scripts as the seed of ELIS’s own mandatory execution path.

Outcome:

- recommend a minimal ELIS Execution Control Plane that prepares, verifies, records and blocks execution without becoming governance/merge/approval authority.

---

### 5. `PE-OPS-A2A-PRODUCTION-01`

**Title:** Productionise A2A Event Backbone for ELIS Agent Coordination

Objective:

- move A2A from local pilot to production event backbone only after pilot evidence is good.

Preconditions:

- A2A pilot successful;
- GitHub Agent production path stable;
- Advisor production role available or explicitly deferred;
- clear rollback;
- no authority creep.

Scope:

- production event writing/reading;
- failure-class event capture;
- integration with dashboard/status reporting if available;
- no dispatch authority unless a later PE explicitly grants it under deterministic controls.

---

### 6. `PE-OPS-OPENCLAW-CONFIG-SYNC-01`

**Title:** Align Repo/Docs OpenClaw Model Matrix with Live Runtime

Objective:

- reconcile live `~/.openclaw/openclaw.json` with repo/docs config files.

Scope:

- compare live runtime config;
- repo `openclaw/openclaw.json`;
- docs `docs/openclaw/openclaw_sanitised.json`;
- update repo/docs to match approved live matrix;
- preserve PM Claude setting;
- preserve infra/prog OpenRouter matrix;
- no secrets;
- no runtime restart unless explicitly approved.

This PE can be scheduled before or after A2A pilot depending on operational urgency.

---

## 7. Medium-term architecture target

The desired ELIS operating model is:

```text
PO / business user
  ↓
Discord / Teams interface
  ↓
ELIS PM
  ↓
Execution control plane
  ↓
Implementer / validator agents
  ↓
Git commits, tests, REVIEW/HANDOFF artefacts
  ↓
GitHub Agent
  ↓
PR, CI, merge with PO approval
  ↓
A2A event log + dashboard visibility
  ↓
ELIS Advisor / Supervisor support
```

Authority boundaries:

| Component | Authority |
|---|---|
| PO | Approves scope, exceptions, merge, production changes |
| PM | Coordinates PE workflow, does not implement/validate directly |
| Implementer | Writes implementation in authorised files only |
| Validator | Independently validates and writes `REVIEW.md` |
| Supervisor | Read-only diagnosis and verification |
| Advisor | Advisory-only support for PO/PM decisions |
| GitHub Agent | GitHub write path after PO approval |
| A2A | Structured event/evidence transport, not authority |
| Dashboard | Observability only |

---

## 8. Definition of “production-ready ELIS”

ELIS should be considered operationally mature when:

1. PM cannot dispatch without deterministic preflight PASS.
2. Target-agent worktrees are automatically checked and bound.
3. Branch/commit propagation is scripted and verified.
4. Session/thread/model binding is validated before dispatch.
5. GitHub Agent is the only normal GitHub write path.
6. Supervisor can independently verify all critical state.
7. Advisor is available for governance/strategy support.
8. A2A records structured events for observability.
9. Dashboard provides read-only operational status.
10. CI catches state/metadata drift before merge.
11. Manual PO exceptions are rare and explicitly documented.

The PR #457 experience shows ELIS is moving in the right direction: failures were eventually classified, corrected and validated. The next stage is to reduce the manual loops by converting these lessons into deterministic platform controls.
