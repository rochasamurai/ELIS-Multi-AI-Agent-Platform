# ELIS Agent Dispatch Binding and Validation Rules for Runtime/Worktree Separation

## Overview
This document outlines the governance rules and validation procedures for agent dispatch binding and worktree separation in the ELIS system. These rules ensure that agents are properly dispatched to their designated fixed workspaces and that runtime/worktree separation is maintained during GitHub operations.

## Purpose
To establish clear binding requirements and validation procedures for all agents that operate within the ELIS environment, particularly those performing GitHub operations. This includes maintaining strict separation between runtime environments and source worktrees to prevent operational and security risks.

## Scope
These rules apply to all ELIS agents that:
- Perform GitHub operations (PR creation, commits, etc.)
- Operate within fixed workspaces
- Require source path identification for security and compliance
- Must maintain explicit separation between runtime and source contexts

## Core Principles

### 1. Fixed Workspace Binding
Each agent must bind to exactly one fixed workspace as its primary operational context.

### 2. Runtime/Worktree Separation
Agents must enforce separation between:
- Runtime execution environment (where the agent executes)
- Source worktree (where PR changes come from)
- These contexts must always differ to maintain security boundaries

### 3. Identity Verification
Agent identity must be verified against the workspace binding and validated through multiple mechanisms.

### 4. Authorization Chain
All agent operations must traverse proper authorization chains through PM/PO for any GitHub write operations.

## Binding Validation Process

### Pre-Dispatch Validation
Before any agent activation:
1. Verify the target fixed workspace path is valid
2. Confirm proper workspace binding for the agent role
3. Ensure the workspace matches the agent's expected identity
4. Validate that the workspace has appropriate permissions

### Runtime/Worktree Verification Flow
For every agent operation involving GitHub:
1. **Identity Check**: `pwd` vs `git rev-parse --show-toplevel` comparison
2. **Separation Validation**: Ensure runtime ≠ source worktree paths
3. **Repository Check**: Validate both paths are git repositories
4. **Permission Verification**: Verify required accesses are available

### Validation Components

#### 1. Path Identity Validation
```
# Validate that runtime is properly separated from source
RUNTIME_PATH=$(pwd)
SOURCE_PATH=$(git rev-parse --show-toplevel)

if [ "$RUNTIME_PATH" = "$SOURCE_PATH" ]; then
    echo "ERROR: Runtime and source worktrees must be different"
    exit 1
fi
```

#### 2. Workspace Validity Check
```
# Verify both workspaces are valid fixed workspaces
if [[ ! -d "$RUNTIME_PATH" ]] || [[ ! -d "$SOURCE_PATH" ]]; then
    echo "ERROR: Invalid workspace path detected"
    exit 1
fi

if ! git -C "$RUNTIME_PATH" rev-parse --git-dir >/dev/null 2>&1; then
    echo "ERROR: Runtime workspace is not a git repository"
    exit 1
fi

if ! git -C "$SOURCE_PATH" rev-parse --git-dir >/dev/null 2>&1; then
    echo "ERROR: Source workspace is not a git repository"
    exit 1
fi
```

#### 3. Fixed Workspace Verification
Agents must validate that:
- The workspace path is within the fixed workspace hierarchy
- Workspace identity matches agent configuration
- The workspace corresponds to the PE being operated on  
- The workspace has not been quarantined or deactivated

## Agent Assignment and Dispatch Rules

### Role-Based Assignment
- Implementer agents must bind to their designated implementer workspace
- Validator agents must bind to their designated validator workspace
- GitHub Agent must bind to its designated GitHub workspace
- All assignments follow the fixed workspace model

### Dispatch Boundaries
1. **Fixed Path Validation**: No runtime path may resolve to a different workspace than assigned
2. **Workspace Integrity**: No changes to fixed workspace layout outside of defined processes
3. **Access Restrictions**: Runtime workspace cannot be used as source workspace
4. **Authorization Dependencies**: All operations require proper PM/PO authorization for GitHub writes

## SELF_CONTAINED_STATE_CHANGING_DISPATCH_RULE

Agents that perform state-changing operations (e.g., GitHub write operations) must operate within a self-contained dispatch model that:
1. Ensures all inputs and outputs are explicitly defined
2. Requires validation of all external state dependencies 
3. Maintains deterministic and reproducible behavior
4. Provides clear auditing of all operations
5. Enforces authorization chain through PM/PO before any write operation

## STATE_CHANGING_DISPATCH_PRE_RESET_RULE

State-changing dispatch operations must be preceded by a complete reset of the agent's working state to ensure clean, deterministic execution and prevent contamination from previous operations.

## COMPLETE_COMMIT_EVIDENCE_BEFORE_REVALIDATION_RULE

All revalidation activities require complete commit evidence before proceeding. This ensures that validation is performed against committed code and not on temporary or uncommitted changes. The commit evidence includes:
1. Fully committed and integrated changes
2. Explicit commit SHA of the validated state
3. Verification that the commit is reachable from the target branch
4. Evidence that the validation was performed on committed code state

## TWO_INSPECTION_ONLY_FAILURE_ESCALATION_RULE

Any failure during operation validation must trigger a two-inspection escalation process:
1. Initial failure inspection to identify root cause
2. Second validation attempt with enhanced diagnostics
3. Escalation to supervisor role if failure persists after second inspection

## VALIDATOR_BRANCH_OWNERSHIP_RULE

Validator agents must only operate on branches they exclusively own, preventing cross-contamination of validation results and ensuring clear ownership of validation artifacts.

## IMPLEMENTER_BRANCH_RELEASE_AFTER_IMPLEMENTATION_RULE

Implementer agents must release their working branches and clean up any temporary artifacts after successful implementation, ensuring no lingering state affects future operations.

## GITIGNORE_POLICY_CHANGE_INTEGRATION_RULE

When gitignore policy changes are introduced, they must be integrated systematically with existing workspace governance to maintain consistent exclusion patterns across all agent workspaces.

## VALIDATION_AFTER_PASS_WITH_NOTES_RULE

Operations that pass validation but include notes or warnings must be documented and reviewed by the appropriate oversight role for potential action items.

## CHILD_SESSION_NO_IMPLIED_CONTEXT_RULE

Child sessions spawned from parent dispatches must not carry implied context from their parents. Each child session must establish its own explicit context and validate all assumptions independently.

## PM_STATE_CHANGING_DISPATCH_SKILL

The PM (Product Manager) role must possess the skill to issue state-changing dispatch commands that can only be executed after proper authorization chain validation from PM/PO for any write operations on GitHub.

## DISPATCH_CONTRACT_MACHINE_CHECK_RULE

All dispatch contracts must include machine-checkable validation routines to verify the compatibility of dispatch parameters with agent capabilities and workspace expectations before operation initiation.

## DOCS_ONLY_CORRECTION_DISPATCH_RULE

Documentation-only corrections must be submitted within the correct documentation governance framework, following the same validation processes as operational changes, including proper branch tagging and review cycles.

## OPENCLAW_CONFIG_EMERGENCY_CORRECTION_RECORD_RULE

All emergency configuration corrections applied to OpenClaw runtime must be recorded in a dedicated correction log that includes timestamp, operator identity, change impact assessment, and rollback procedure documentation.

## Enforcement Mechanisms

### Automated Enforcement
1. **Startup Validation**: Agent initialization checks binding validity
2. **Operation Validation**: Each GitHub operation validates separation  
3. **Continuous Monitoring**: Runtime checks for workspace integrity
4. **Error Reporting**: Clear messaging on validation failures

### Policy Violations
When violations are detected:
1. Immediate termination of the operation
2. Detailed error logging with validation details
3. Alert generation to supervision systems
4. Automatic isolation of problematic agent instance

### Audit Requirements
All binding and validation activities must be:
- Logged with timestamps
- Include agent identity and workspace details
- Capture validation parameters and results
- Store in a centralized audit trail for compliance

## Integration with Existing Protocols

### Alignment with PE Operating Protocol
These binding rules integrate with the PE Operating Protocol by:
- Reinforcing fixed workspace constraints
- Maintaining agent identity verification requirements
- Supporting the worktree preflight checklist
- Enabling Supervisor role monitoring of bindings

### Relationship to GitHub Agent Operating Model
The dispatch binding rules support and enhance:
- GitHub write boundary enforcement
- Source path governance
- Fixed workspace compliance
- Risk mitigation for unauthorized operations

## Compliance Framework

### Audit Checklist
For runtime/worktree separation compliance:
- [ ] Runtime workspace path != Source workspace path
- [ ] Both workspaces are valid git repositories
- [ ] Workspace identities match agent configurations
- [ ] Agent binding certificate is valid
- [ ] No unauthorized access to runtime workspace as source

### Incident Response
When binding failures occur:
1. Identify violation type (path, identity, authorization)
2. Escalate to Supervisor role for assessment
3. Isolate affected agent instance
4. Document for post-mortem analysis
5. Implement preventive measures for recurrence

## Version History

| Version | Date       | Author | Changes |
|---------|------------|--------|---------|
| 1.3     | 2026-05-17 | PM     | Restored core dispatch rules and expanded state change validation |
| 1.0     | 2026-05-17 | PM     | Initial draft incorporating runtime/worktree separation requirements |

## References
- `docs/governance/ELIS_PE_Operating_Protocol.md`
- `docs/governance/ELIS_GitHub_Agent_Operating_Model.md`
- `docs/governance/ELIS_Worktree_Preflight_Checklist.md`
- `docs/ops/github-agent/GITHUB_AGENT_RULES.md`## 6a. LATEST VALIDATOR REVIEW MUST BE ON FINAL PR BRANCH RULE

### 6a.1 Rule Statement
A validator PASS is valid **only when backed by a committed PE-specific REVIEW.md** that resides on the final implementation/PR branch (not a separate validation branch, not a detached-HEAD commit, not uncommitted).

### 6a.2 REVIEW.md Requirements
The REVIEW.md on the final PR branch must:
1. Be committed as part of the branch's commit history (visible via `git log --all -- REVIEW.md` on the target branch).
2. Reference the **final validated branch HEAD** or the **final validation target commit** (the exact commit SHA that was reviewed and deemed ready for closeout).
3. Record the final checks performed and the verdict (`PASS`, `FAIL`, or `BLOCKED`).
4. Be authored by the validator agent, not by the implementer, PM, or any other role.

### 6a.3 Commitment Requirement
The latest validator REVIEW.md update must be:
- **Committed** — not staged, not uncommitted, not in a stash
- **Present on the final implementation/PR branch** — the branch that will be merged or closed out
- Identifiable via `git log --oneline <branch> -- <REVIEW.md-path>` before push/PR/merge/closeout

### 6a.4 PASS Dependency
Validator must not report PASS until:
1. REVIEW.md is written with the full verdict packet.
2. REVIEW.md's tracked/committed/integration status is explicit (committed on the target branch, not floating on a separate validation branch).
3. The final checks match the branch HEAD that will be merged.

### 6a.5 Enforcement
- `check_validation_readiness.py` must include a `COMMITTED_REVIEW_ON_BRANCH` check that verifies the REVIEW.md is committed and reachable from the current branch HEAD.
- If the latest REVIEW.md update is not committed on the current branch, the validator must reject the state and report `REVIEW_NOT_ON_BRANCH`.

## 6b. AUTHORISED EXECUTION OWNER FOR BRANCH INTEGRATION RULE

### 6b.1 Rule Statement
PM coordinates PE workflow but **must not execute merges, pushes, PR actions, or any Git history rewrites directly**. All branch integration operations (push, PR creation, merge, rebase of the target branch) must be executed by the authorised execution owner in the authorised worktree.

### 6b.2 Eligible Execution Owners
Branch integration may be performed by:
- **GitHub Agent** — after explicit PM/PO approval for each operation
- **Implementer** — local branch commits only; push only when PM/PO explicitly instructs
- **Validator** — local REVIEW.md commits on the shared PE branch only; no push or PR operations

### 6b.3 PM Coordination Boundary
PM is authorised to:
- Propose and plan PEs
- Maintain CURRENT_PE.md registry
- Create and maintain PE_TASK.md
- Dispatch implementers and validators
- Interpret PE status and coordinate workflow
- Request PO approval when needed

PM is **explicitly forbidden** from:
- Running `git push` (any remote)
- Creating or modifying PRs
- Running `git merge` (local or remote)
- Running `git rebase` (of target branches; local task-branch rebase requires authorisation)
- Running `git commit --amend` or any history-rewriting operation
- Writing to GitHub via any tool (gh CLI, API, browser)

### 6b.4 Authorised Worktree Requirement
Branch integration must be executed from the **authorised Git worktree** for the executing role, not from the OpenClaw runtime workspace, the canonical repo (`/opt/elis/repo`), or any other filesystem location.

### 6b.5 Enforcement
- `check_pm_no_write.py` enforces the PM no-write rule across all PE evidence directories.
- The Supervisor agent monitors for role boundary violations.
- Any detection of PM-authored commits outside `PE_TASK.md` is a `PM_WRITE_VIOLATION`.

## 8. Deterministic Checks

Required checks for every PE dispatch:
1. **Dispatch binding check** (`scripts/check_dispatch_binding.py`) — verifies branch, HEAD, worktree cleanliness, and runtime/worktree binding
2. **Implementation readiness check** (`scripts/check_implementation_readiness.py`) — verifies branch, HEAD, worktree cleanliness, PE task packet, and scope files
3. **Validation readiness check** (`scripts/check_validation_readiness.py`) — verifies worktree scope, expected commit, clean tracked state, and artefact completeness
4. **Fixed worktrees audit** (`scripts/check_fixed_worktrees.py`) — verifies each fixed worktree is registered, has correct origin, and is free of runtime/bootstrap files
5. **Persistent context check** (`scripts/check_persistent_context_files.py`) — verifies runtime/bootstrap files exist in the expected location

---
## Model Binding Requirement for ELIS Agent Dispatch

**Added: PE-OPS-A2A-PRODUCTION-02**

### Requirement

Every `sessions_spawn.agentId` dispatch to an ELIS Platform agent MUST include an explicit
`model` parameter matching the target agent's live `~/.openclaw/openclaw.json` model entry.

`agentId` controls workspace routing and session identity only. Without an explicit `model`
parameter, OpenClaw inherits the caller's model — violating ELIS 2-agent model resilience.

### Required dispatch parameters

| Parameter          | Requirement                                                    |
|--------------------|----------------------------------------------------------------|
| `agentId`          | Assigned agent from live config                                |
| `model`            | Must match agent's `model` field in live `~/.openclaw/openclaw.json`; or named PO exception required |
| `cwd`              | Agent workspace from live config                               |
| `context`          | `"isolated"`                                                   |
| `cleanup`          | `"keep"`                                                       |
| `runtime`          | `"subagent"`                                                   |
| `taskName`         | Must include PE ID and gate label                              |
| `runTimeoutSeconds`| Bounded value (≤ 600)                                          |

### Live ELIS Platform agent model registry

Source: `/home/samurai/.openclaw/openclaw.json` (authoritative — re-read immediately before dispatch)

| ELIS agent     | Configured model                        |
|----------------|-----------------------------------------|
| infra-impl-a   | openrouter/qwen/qwen3-coder-flash       |
| infra-impl-b   | openrouter/deepseek/deepseek-v4-flash   |
| infra-val-a    | openrouter/deepseek/deepseek-v4-pro     |
| infra-val-b    | openrouter/z-ai/glm-5.1                 |
| prog-impl-a    | (read from live config before dispatch) |
| prog-impl-b    | (read from live config before dispatch) |
| prog-val-a     | (read from live config before dispatch) |
| prog-val-b     | (read from live config before dispatch) |

Values for prog-* agents must be read from live config immediately before dispatch — they are not reproduced here to avoid drift.

### Validation tool

`scripts/check_agent_model_registry.py` — validates that all ELIS Platform agents in scope have
an explicit model entry in the live OpenClaw config. Run with `--check` (default). CI-safe.

```bash
python scripts/check_agent_model_registry.py --check
```

### Exceptions

Any dispatch using a model other than the agent's live config entry requires a named, PO-approved
exception recorded in the opening Status Packet of the affected PE gate. Exception must name:
- The actual model used
- The configured model
- The PO approval reference (PM-CHORE or PE ID)

### ELIS 2-agent model resilience rule

Implementer and Validator for any PE gate must run on different AI models. If both sessions
inherit the same caller model, the resilience requirement is not met. The `model` parameter
in `sessions_spawn` is the mechanism that enforces this.
