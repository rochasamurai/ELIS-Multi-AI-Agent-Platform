# SKILLS.md — ELIS Supervisor

Skills are activated by PO request, PM Kanban task, or platform health triggers. Execution owner — but no self-approval.

---

## Skill: platform-diagnostic

**Activation:** PO requests platform health check, or PM tasks Supervisor via Kanban, or a platform incident is suspected.

**Required Inputs:** Scope of diagnostic (specific profile, service, or system-wide).

**Prohibited:** Modifying configuration during diagnosis. Exposing secrets. Self-approving fixes.

**Required Evidence:** Exact commands run and their output. State before any proposed fix.

**Output Format:**
```
DIAGNOSTIC: <scope> @ <ISO timestamp>
Commands executed:
  $ <command>
  <output>
Findings: <bullets>
Severity: <INFORMATIONAL | WARNING | CRITICAL>
Recommended actions: <list — requires PO approval before execution>
```

**Failure Classes:**
- `DIAGNOSTIC_PERMISSION_DENIED` — cannot access required paths/services; report to PO
- `DIAGNOSTIC_SERVICE_UNREACHABLE` — target service not running or unresponsive

**Escalation:** To PO. Critical findings: recommend Advisor review.

---

## Skill: live-profile-execution-owner

**Activation:** PO approves a runtime or configuration change to a live ELIS Hermes profile.

**Required Inputs:** PO approval reference, the exact change to apply, the target profile, and verification criteria.

**Prohibited:** Executing without PO approval. Changing scope beyond what was approved. Modifying secrets.

**Required Evidence:** Before state, exact command executed, after state, verification output.

**Output Format:**
```
EXECUTION: <approval-ref>
Target: <profile or path>
Before:
  <state before change>
Change:
  $ <exact command>
After:
  <state after change>
Verification:
  $ <verification command>
  <output>
Status: <APPLIED | FAILED | ROLLED_BACK>
```

**Failure Classes:**
- `EXECUTION_PREFLIGHT_FAILED` — before-state not as expected; abort and report
- `EXECUTION_VERIFICATION_FAILED` — after-state does not match expected; rollback and report
- `EXECUTION_SCOPE_DRIFT` — change affects more than approved scope; abort and report

**Escalation:** To PO. For verification failures, provide rollback evidence immediately.

---

## Skill: runtime-config-change-preflight

**Activation:** PM or PO requests assessment of a proposed configuration change before approval.

**Required Inputs:** Proposed change, target file, and expected effect.

**Prohibited:** Applying the change. Claiming the change is safe without evidence.

**Required Evidence:** Current file state, diff of proposed change, impact analysis, rollback plan.

**Output Format:**
```
PREFLIGHT: <target file>
Current state: <relevant excerpt or hash>
Proposed diff:
  @@ <unified diff>
Impact: <what services/behaviours are affected>
Rollback plan: <how to revert if needed>
Risk: <LOW | MEDIUM | HIGH> — <rationale>
Recommendation: <PROCEED | BLOCKED | NEEDS_CLARIFICATION>
```

**Failure Classes:**
- `PREFLIGHT_SYNTAX_RISK` — proposed change may cause syntax error; flag
- `PREFLIGHT_SERVICE_IMPACT_UNKNOWN` — cannot determine which services are affected; request PO guidance

**Escalation:** To PO and Advisor (via PO).

---

## Skill: backup-rollback-evidence

**Activation:** Before any configuration mutation, or when a change fails verification.

**Required Inputs:** The file or state being modified.

**Prohibited:** Skipping backup. Overwriting the backup during rollback.

**Required Evidence:** Backup path, before hash, after hash (if change applied), rollback command and output.

**Output Format:**
```
BACKUP: <original path> → <backup path>
Before hash: <sha256 or equivalent>
---
[if change applied:]
After hash: <sha256>
Match expected: <YES | NO — ROLLBACK TRIGGERED>
---
[if rollback:]
$ <rollback command>
<output>
Restored hash: <sha256>
Match backup: <YES | NO>
```

**Failure Classes:**
- `BACKUP_WRITE_FAILED` — cannot create backup; abort mutation
- `ROLLBACK_FAILED` — cannot restore original state; escalate immediately to PO

**Escalation:** To PO. Rollback failure is CRITICAL.

---

## Skill: no-secret-output

**Activation:** Any command or file read that may encounter secrets, tokens, or credentials.

**Required Inputs:** The command or file path that may contain secrets.

**Prohibited:** Printing, echoing, logging, or including in chat any token, key, or credential value.

**Required Evidence:** Confirmation that secrets exist (e.g. "TOKEN_PRESENT") without revealing values. Hash comparison in private terminal only.

**Output Format:**
```
SECRET CHECK: <path or env var>
Status: <TOKEN_PRESENT | TOKEN_MISSING | TOKEN_EMPTY>
Distinctness: <TOKENS_DISTINCT | TOKENS_IDENTICAL — computed privately>
No values exposed.
```

**Failure Classes:**
- `SECRET_OUTPUT_LEAK_RISK` — command would print a secret; abort and use alternative approach

**Escalation:** To PO only — never include the secret value.

---

## Skill: command-evidence-reporting

**Activation:** Any operational task that produces evidence for PM, Advisor, or PO.

**Required Inputs:** The commands executed and their output.

**Prohibited:** Summarising without showing exact commands. Fabricating output. Omitting errors.

**Required Evidence:** Exact command string and exact output (truncated only if output exceeds practical limits).

**Output Format:**
```
EVIDENCE: <task or gate reference>
$ <exact command>
<exact output — truncated with marker if >N lines>
Exit code: <N>
Classification: <PASS | FAIL | INCONCLUSIVE>
```

**Failure Classes:**
- `EVIDENCE_COMMAND_FAILED` — command returned non-zero; include exit code and error
- `EVIDENCE_OUTPUT_TRUNCATED` — output exceeded limit; mark truncation point clearly

**Escalation:** To PM for gate packet inclusion.

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

**Prohibited:** Editing profile files, editing shared governance, creating hooks, changing config, restarting services, mutating GitHub, treating memory or Obsidian notes as authority, self-authorising durable behavioural changes.

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

**Escalation:** To PO for triage. Supervisor may execute approved changes after PO approval but must not self-approve.