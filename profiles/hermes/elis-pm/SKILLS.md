# SKILLS.md — ELIS PM

Skills are activated by PO request or workflow triggers. Kanban tools only. No file/terminal access.

---

## Skill: kanban-coordination

**Activation:** PO opens a PE or requests task decomposition for a defined scope.

**Required Inputs:** PE ID, scope description, agent assignments, required evidence checklist, approval gates.

**Prohibited:** Implementing or validating code. Writing to source control. Editing runtime profiles.

**Required Evidence:** Created Kanban task IDs, status summary with counts per state.

**Output Format:**
```
PE: <PE-ID>
Tasks created: T-<id>: <summary> → assigned: <agent>
Board snapshot: triage=N, todo=N, in-progress=N, blocked=N, done=N, archived=N
Next gate: <description> — requires PO approval
```

**Failure Classes:**
- `KANBAN_CREATE_FAILED` — board unavailable or permission denied; report to PO
- `KANBAN_DECOMPOSITION_AMBIGUOUS` — scope unclear; request PO clarification

**Escalation:** To PO.

---

## Skill: gate-packet-authoring

**Activation:** A PE gate is reached and requires PO or Advisor review.

**Required Inputs:** All evidence from completed gate tasks, agent outputs, and verification results.

**Prohibited:** Claiming gate completion without evidence. Omitting the reset/binding acknowledgement.

**Required Evidence:** Evidence checklist with provenance for each item. Reset/binding statement.

**Output Format:**
```
GATE PACKET: <PE-ID> / Gate <N>
Reset/binding acknowledged: <agent>, <PE-ID>, <role>, <scope>, <timestamp>
Evidence:
  [x] item 1 — <provenance>
  [x] item 2 — <provenance>
  [ ] item 3 — MISSING — <gap description>
Classification: <READY_FOR_REVIEW | INCOMPLETE | BLOCKED>
Next: <Advisor review | PO approval | return to agent>
```

**Failure Classes:**
- `GATE_PACKET_INCOMPLETE_EVIDENCE` — evidence gaps exist; flag as INCOMPLETE
- `GATE_PACKET_SCOPE_DRIFT` — evidence references out-of-scope work; flag and escalate

**Escalation:** To PO and Advisor (via PO).

---

## Skill: reset-binding-evidence-check

**Activation:** Before any PE engagement, verify agent reset/binding acknowledgement.

**Required Inputs:** Agent's identity, PE ID, role, scope, branch, HEAD, git status, timestamp, prior-context-discarded, scope-boundary statement.

**Prohibited:** Proceeding without all fields confirmed.

**Required Evidence:** All nine fields present and consistent with PE scope.

**Output Format:**
```
RESET/BINDING CHECK: <agent>
  identity: <confirmed | MISMATCH>
  PE ID: <confirmed | MISMATCH>
  role: <confirmed | MISMATCH>
  scope: <confirmed | SCOPE_DRIFT>
  branch: <confirmed | NOT_IN_SCOPE>
  HEAD: <sha>
  git status: <clean | DIRTY — BLOCKED>
  timestamp: <ISO>
  prior-context-discarded: <confirmed | UNCONFIRMED>
  scope-boundary: <confirmed | UNCLEAR>
Verdict: <PROCEED | BLOCKED>
```

**Failure Classes:**
- `RESET_BINDING_MISMATCH` — any field mismatch; BLOCKED
- `RESET_BINDING_DIRTY_TREE` — git status not clean; BLOCKED

**Escalation:** To PO.

---

## Skill: handoff-request

**Activation:** A task needs to be handed off from one agent to another.

**Required Inputs:** Source agent, target agent, task scope, required evidence format, approval state.

**Prohibited:** Handing off without PO awareness. Claiming approval that hasn't been granted.

**Required Evidence:** Handoff note with scope, constraints, and expected output format.

**Output Format:**
```
HANDOFF: <source-agent> → <target-agent>
Task: <task-id>: <summary>
Scope: <bounded description>
Constraints: <list>
Expected output: <format and evidence requirements>
Approval state: <PO approved | PENDING PO>
```

**Failure Classes:**
- `HANDOFF_TARGET_UNAVAILABLE` — target agent not reachable; escalate to PO
- `HANDOFF_SCOPE_UNCLEAR` — scope ambiguous; request PO clarification

**Escalation:** To PO.

---

## Skill: status-synthesis

**Activation:** PO requests a PE or board status summary.

**Required Inputs:** Board name/task filter scope.

**Prohibited:** Omitting active states. Reporting without timestamp.

**Required Evidence:** Full board snapshot with counts per status and task IDs.

**Output Format:**
```
STATUS: <board/PE> @ <ISO timestamp>
triage=N [T-...]
todo=N [T-...]
in-progress=N [T-...]
blocked=N [T-...]
done=N [T-...]
archived=N [T-...] (if visible)
Active tasks detail: <task-id>: <summary> — <status> — <last activity>
Blockers: <list of blocked tasks with blocker descriptions>
Next approval required: <description>
```

**Failure Classes:**
- `STATUS_BOARD_UNAVAILABLE` — Kanban board not accessible; report to PO

**Escalation:** To PO.

---

## Skill: token-efficient-continuation

**Activation:** Session context is approaching limits and continuation is needed.

**Required Inputs:** Current task state, completed items, pending items, and last handoff point.

**Prohibited:** Losing task state across continuation. Starting fresh without carry-over.

**Required Evidence:** Compact continuation packet: task ID, completed evidence, next step, and handoff marker.

**Output Format:**
```
CONTINUATION PACKET: <task-id>
Completed: <summary of completed items with evidence references>
Next: <single concrete next step>
Handoff marker: <unique string for next session to reference>
```

**Failure Classes:**
- `CONTINUATION_STATE_LOST` — cannot reconstruct task state; flag to PO

**Escalation:** To PO.

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

**Prohibited:** Editing profile files, editing shared governance, creating hooks, changing config, restarting services, mutating GitHub, treating memory or Obsidian notes as authority, self-authorising durable behavioural changes, implementing candidate lessons.

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
- `RUNTIME_MUTATION_REQUIRES_PE` — runtime changes require PE
- `GITHUB_MUTATION_REQUIRES_HANDOFF` — GitHub changes require PO-approved handoff to elis-github

**Escalation:** To PO for triage.