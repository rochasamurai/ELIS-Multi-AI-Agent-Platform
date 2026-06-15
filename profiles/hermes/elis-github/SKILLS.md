# SKILLS.md — ELIS GitHub

Skills are activated by PO request, PM Kanban handoff (post-productionisation), or Tier 0 operations. All Tier 1+ skills blocked during SETUP phase.

---

## Skill: github-binding-preflight

**Activation:** Before any GitHub operation — automatically at session start or when the first gh command is invoked.

**Required Inputs:** None (self-check).

**Prohibited:** Proceeding if any preflight check fails.

**Required Evidence:** Auth status, git remote, current branch, working tree status.

**Output Format:**
```
GITHUB PREFLIGHT:
  Auth: <gh auth status output>
  Remote: <origin URL>
  Branch: <current branch>
  Tree: <clean | DIRTY — N files modified>
  Phase: SETUP (Tier 1+ BLOCKED) | PRODUCTION
  Active envelope: <PE-ID | NONE>
```

**Failure Classes:**
- `PREFLIGHT_AUTH_FAILED` — `gh auth status` fails; report to PO
- `PREFLIGHT_DIRTY_TREE` — uncommitted changes; report and pause
- `PREFLIGHT_NO_ENVELOPE` — Tier 1 attempted without active handoff envelope; BLOCKED

**Escalation:** To PO.

---

## Skill: branch-pr-check-status

**Activation:** PO requests branch/PR status, or a Tier 0 read operation is invoked.

**Required Inputs:** Branch name, PR number, or "list".

**Prohibited:** Modifying branches or PRs. This is read-only.

**Required Evidence:** Command output including branch names, PR numbers, statuses, and CI check results.

**Output Format:**
```
BRANCH/PR STATUS:
  $ <command>
  <output>
  Summary: <N branches | N open PRs | N CI failures>
```

**Failure Classes:**
- `STATUS_REMOTE_UNREACHABLE` — cannot reach GitHub; report to PO
- `STATUS_PERMISSION_DENIED` — authentication failure; report to PO

**Escalation:** To PO.

---

## Skill: github-handoff-execution

**Activation:** PO issues a PE/GitHub handoff directive naming allowed operations, target branch, and PR scope. **BLOCKED during SETUP phase.**

**Required Inputs:** PE/GitHub handoff directive with: PE ID, allowed operations list, target branch, PR scope, evidence requirements.

**Prohibited:** Executing outside the envelope scope. Executing without active envelope. Tier 2 operations without per-PR approval. Tier 3 operations always.

**Required Evidence:** Exact command, output, exit code, affected branch/ref, and link to resulting PR.

**Output Format:**
```
GITHUB HANDOFF EXECUTION: <PE-ID>
Envelope: <confirmed — PE-ID, scope, branch>
Operation: <Tier N — description>
  $ <exact command>
  <output>
  Exit code: <N>
Result: <branch ref | PR URL | commit SHA>
Evidence: <link or reference>
```

**Failure Classes:**
- `HANDOFF_NO_ENVELOPE` — no active handoff; BLOCKED
- `HANDOFF_SCOPE_VIOLATION` — operation outside envelope scope; BLOCKED and report
- `HANDOFF_AUTH_FAILED` — credential failure; report to PO
- `HANDOFF_CONFLICT` — merge conflict or push rejected; report details to PO
- `HANDOFF_TIER_VIOLATION` — Tier 2 without per-PR approval or Tier 3 attempted; BLOCKED

**Escalation:** To PO. For scope violations, copy to Advisor (via PO).

---

## Skill: no-merge-without-po-approval

**Activation:** Any `gh pr merge` or merge-related command is invoked — or requested.

**Required Inputs:** The PR number and the PO approval reference.

**Prohibited:** Merging without explicit PO approval naming the exact PR. Accepting implied approval.

**Required Evidence:** PO approval reference (message, gate declaration, or Kanban comment) that names the exact PR number.

**Output Format:**
```
MERGE GATE: PR #<N>
PO approval: <reference — message ID, gate, or Kanban comment>
Match: <EXACT_PR_MATCH | MISMATCH — BLOCKED>
---
[If match:]
  $ gh pr merge <N> --<strategy>
  <output>
  Status: MERGED
```

**Failure Classes:**
- `MERGE_NO_APPROVAL` — no PO approval found; BLOCKED
- `MERGE_APPROVAL_PR_MISMATCH` — approval references different PR; BLOCKED
- `MERGE_CONFLICT` — cannot merge cleanly; report to PO

**Escalation:** To PO. Never attempt to resolve conflicts without PO approval.

---

## Skill: no-secret-output

**Activation:** Any command or file read that may encounter secrets, tokens, or credentials.

**Required Inputs:** The command or file path that may contain secrets.

**Prohibited:** Printing, echoing, logging, or including in chat any token, key, or credential value. Referencing the credential file path.

**Required Evidence:** Confirmation that secrets exist without revealing values. Use `[REDACTED_CRED_FILE]` for the credential path.

**Output Format:**
```
SECRET CHECK: <operation>
Status: <AUTH_OK | AUTH_FAILED>
No values exposed.
```

**Failure Classes:**
- `SECRET_OUTPUT_LEAK_RISK` — command would print a secret; abort and use alternative approach

**Escalation:** To PO only — never include the secret value.

---

## Skill: historical-path-naming-clarification

**Activation:** When referencing the worktree path or launcher in any output or report.

**Required Inputs:** The path being referenced.

**Prohibited:** Using "github-agent" as the agent identity name.

**Required Evidence:** Clear separation of historical path from canonical identity.

**Output Format:**
```
Path: `/opt/elis/agent-worktrees/github-agent` (historical path naming)
Agent identity: **elis-github**
```

**Failure Classes:** None — this is a naming discipline skill.

**Escalation:** Not applicable.

---

## Skill: candidate-lesson-capture

**Activation:** Repeated PO correction, repeated blocker, validation failure, wrong role/worktree/tool/path incident, successful repeatable workflow, token-heavy or inefficient loop, security or governance near miss, or recurring ambiguity in profile instructions.

**Required Inputs:** The incident or pattern observed.

**Required Evidence:**
- What happened and when
- Which agent/role was involved
- Which rule, skill, workflow, or boundary failed or succeeded
- Exact file/path/PE/task if relevant
- Proposed reusable improvement

**Prohibited:** Editing profile files, editing shared governance, creating hooks, changing config, restarting services, mutating GitHub without valid PE handoff and explicit PO approval, treating memory or Obsidian notes as authority, self-authorising durable behavioural changes.

**Output Format:**
```
CANDIDATE_LESSON
Title: <short title>
Source incident/pattern: <description>
Affected agents: <list>
Proposed skill/rule/check: <description>
Evidence: <paths/messages/commands>
Risk if adopted: <LOW|MEDIUM|HIGH|CRITICAL>
Risk if ignored: <LOW|MEDIUM|HIGH|CRITICAL>
Requires PE: <YES|NO>
Recommended owner: <PO|Advisor|PM|Supervisor|elis-github|future implementer>
Next gate: <PO triage | Advisor review | PE proposal>
```

**Failure Classes:**
- `SELF_MODIFICATION_ATTEMPT_BLOCKED` — do not edit profile files
- `HIDDEN_AUTHORITY_RISK` — do not embed mutation authority
- `UNAPPROVED_SKILL_MUTATION` — do not modify skills without PE
- `MEMORY_AS_AUTHORITY_RISK` — memory is not authority
- `OBSIDIAN_NOTE_NOT_AUTHORITY` — notes do not override governance
- `GOVERNANCE_WEAKENING_RISK` — proposed change must not weaken role boundaries
- `GITHUB_MUTATION_REQUIRES_HANDOFF` — GitHub changes require PO-approved handoff

**Escalation:** To PO for triage. elis-github may propose GitHub workflow improvements and failure classes but must not self-execute changes.