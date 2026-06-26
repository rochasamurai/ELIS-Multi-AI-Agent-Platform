# ELIS Agent Communications Operating Model

**PE:** PE-OPS-AGENT-COMMS-01
**Status:** APPROVED
**Version:** 1.0.0
**Date:** 2026-06-26
**Issuing Authority:** ELIS PO (Carlos Rocha)

---

## 1. Scope and Applicability

### 1.1 Scope
Defines the communications operating model for the ELIS multi-agent platform governing A2A (JSON-RPC), Kanban (elis-a2a-implementation board), Discord (#elis-pe-reports), and GitHub (Issues/PRs).

### 1.2 Applicability
All five active ELIS Hermes profiles:
- **elis-ideas** — research / idea capture
- **elis-advisor** — PO decision-support and governance review
- **elis-pm** — Kanban-based PM and PE coordination
- **elis-supervisor** — platform operations and live profile/runtime execution owner
- **elis-github** — GitHub operations only

### 1.3 Governance Principles
1. **Separation of duties** — no agent may implement and validate the same artifact.
2. **PO approval gate** — all PE openings and merges require Carlos Rocha approval.
3. **Evidence durability** — scratch workspace is ephemeral; authoritative evidence goes to Kanban comments, Discord, or board artifacts directory.
4. **Deterministic rejection** — policy violations produce deterministic rejection codes.
5. **Localhost-only binding** — all A2A endpoints bind to 127.0.0.1 only.

---

## 2. Agent Roles and Identities

### 2.1 Canonical Role Names

| Role | A2A sender_role | Kanban assignee | Port | Agent Card | Server Running |
|------|----------------|-----------------|------|------------|----------------|
| ELIS Advisor | advisor | elis-advisor | 9500 | Yes | Yes (systemd) |
| ELIS Supervisor | supervisor | elis-supervisor | 9501 | Yes | Yes (systemd) |
| ELIS PM | pm | elis-pm | 9502 | Yes (on disk) | No (deferred) |
| ELIS Ideas | ideas | elis-ideas | — | No | No |
| ELIS GitHub | github | elis-github | — | No | No |

### 2.2 Role Boundaries (Hard Limits)

- **PM**: Coordinates via Kanban, creates tasks, authors gate packets. Does NOT implement code, validate code, write to source control, or perform GitHub operations directly.
- **Advisor**: Validates packets, returns PASS/FAIL/BLOCKED verdicts. Does NOT implement, dispatch, or execute runtime changes.
- **Supervisor**: Executes runtime operations, reports results with evidence. Does NOT author governance packets, validate, or dispatch agents.
- **Ideas**: Captures and develops ideas for PO review. Does NOT dispatch agents, validate implementation, or modify platform state.
- **GitHub**: Source-control writes only, within PO-approved Tier scope. Does NOT validate, dispatch, or approve work.

---

## 3. A2A / Kanban / Discord / GitHub Responsibility Matrix

| Activity | A2A | Kanban | Discord #elis-pe-reports | GitHub |
|----------|-----|--------|------------------------|--------|
| Task dispatch/assignment | — | Primary | Notification | — |
| Execution request (PM→Advisor) | Primary | Trigger ref | Summary on completion | — |
| Execution request (PM→Supervisor) | Primary | Trigger ref | Summary on completion | — |
| Validation request (PM→Advisor) | Primary | Trigger ref | Summary on verdict | — |
| Validation verdict return | Primary | Recorded as comment | Notification | — |
| Status/progress update | Optional (A2A status) | Heartbeat | Periodic digest | — |
| PE lifecycle tracking | — | Primary | START/COMPLETE events | Issue per PE |
| Governance approval record | — | Comment/metadata | Notification | Issue/PR |
| Blocked-task escalation | — | Block state | Auto-alert (future) | — |
| Macro-event (START, SUMMARY, PASS, FAIL, BLOCKED) | — | Not authoritative | Authoritative | — |
| Source-control change tracking | — | Task reference | — | Primary |
| Code review | — | Task reference | — | Primary (PR) |

**Key rules:**
- A2A = operational message plane for inter-agent requests
- Kanban = persistent coordination state for task lifecycle
- Discord #elis-pe-reports = human notification channel for macro-events only; NOT authoritative for Kanban task lifecycle state or GitHub source-control state
- GitHub = authoritative source-control artifact record

---

## 4. Allowed Communication Flow Table

### 4.1 Approved Directional Flows

| From | To | A2A Allowed | Kanban | Discord | GitHub |
|------|----|-------------|--------|---------|--------|
| PM | Advisor | Yes (request, ack, status) | Create task | START + verdict | Issue ref |
| PM | Supervisor | Yes (request, ack, status) | Create task | START + completion | Issue ref |
| Advisor | PM | Deferred (no PM server) | Comment on PM task | Final report | — |
| Supervisor | PM | Deferred (no PM server) | Comment on PM task | Final report | — |
| PM | GitHub | — | Create task (coordinated via Kanban, not direct A2A) | Notification | Issue/PR |
| Advisor→Advisor | Prohibited (self-target) | — | — | — |
| Supervisor→Supervisor | Prohibited (self-target) | — | — | — |
| Advisor→Supervisor | Prohibited (no policy support) | — | — | — |
| Ideas→Any | Prohibited (not in ALLOWED_SENDER_ROLES) | — | — | — |

**Note on PM→GitHub routing:** PM does NOT perform GitHub operations directly. When GitHub work is required, PM creates a Kanban task for elis-github with the required scope. ELIS GitHub executes the operation and reports back.

### 4.2 Inbound Message Types
- **request**: Execution or validation request (PM→Advisor/Supervisor)
- **ack**: Acknowledgement of receipt
- **status**: Status update on ongoing task
- **policy_rejection**: Outbound-only (produced by TaskUpdater.reject())

### 4.3 Agent Card Discovery
Each agent with a running server exposes a well-known Agent Card at `<base_url>/.well-known/agent-card` with name, version, capabilities, skills, and supported interfaces.

---

## 5. Prohibited Communication Patterns

### 5.1 Hard Prohibitions (Policy-Enforced)

| Pattern | Rejection Code |
|---------|---------------|
| Self-target | REJECTED_SELF_TARGET |
| Missing elis_sender_role or elis_message_type | REJECTED_MALFORMED_ENVELOPE |
| Unknown sender role | REJECTED_UNKNOWN_SENDER |
| Unsupported message type | REJECTED_UNSUPPORTED_TYPE |
| Autonomous follow-on | REJECTED_AUTONOMOUS_FOLLOW_ON |
| PM targeting disallowed recipient | REJECTED_DISALLOWED_RECIPIENT |
| Missing elis_sent_at | E_TS_MISSING |
| Malformed elis_sent_at | E_TS_MALFORMED |
| Stale timestamp (>300s) | E_TS_STALE |
| Future timestamp (>30s skew) | E_TS_FUTURE |

### 5.2 Operational Prohibitions

- Agent implementing AND validating the same artifact.
- PM writing code or running implementation commands.
- Advisor dispatching tasks to implementers.
- Supervisor authoring governance packets.
- GitHub performing validation or approval.
- Scratch workspace as authoritative evidence store.
- 0.0.0.0 or public host bindings.
- Kanban comment overriding GitHub PR state.
- Discord #elis-pe-reports overriding Kanban task lifecycle state.

### 5.3 Deprecated Patterns

| Legacy | Replacement |
|--------|------------|
| Manual Discord reporting | Structured #elis-pe-reports format |
| Unstructured A2A payloads | Mandatory elis_task_ref + elis_pe_ref in metadata |
| Ad-hoc agent-to-agent | Standardised AgentCard → ClientFactory path |

---

## 6. A2A Message Schema and Reference Requirements

### 6.1 Required Metadata Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| elis_sender_role | string | Always | pm, advisor, or supervisor |
| elis_message_type | string | Always | request, ack, or status |
| elis_sent_at | ISO 8601 | Always | UTC with literal Z |
| elis_policy_version | string | Always | Semantic version (currently 1.0.0) |
| elis_task_ref | string | Required for all operational messages; diagnostic-only messages may omit only when explicitly labelled diagnostic | Kanban task ID or PE reference |
| elis_target_role | string | PM messages | Declared recipient (advisor, supervisor) |
| elis_pe_ref | string | Required for all PE-scoped operational messages | PE identifier for traceability |

**Task and PE reference rule (deterministic):**
- `elis_task_ref`: Required for all operational messages. Diagnostic-only messages may omit only when the message metadata includes `"elis_message_class": "diagnostic"`. This prevents silent task-reference gaps while preserving diagnostic telemetry that does not map to a specific Kanban task.
- `elis_pe_ref`: Required for all PE-scoped operational messages (any message whose action is part of an active PE). Non-PE operational status checks may omit.

### 6.2 Optional Fields
elis_gate_ref, elis_session_id, elis_evidence_path, elis_message_class

### 6.3 Message Envelope Structure

```json
{
  "message_id": "<uuid>",
  "context_id": "<uuid>",
  "role": "ROLE_USER",
  "parts": [{"text": "Message body"}],
  "metadata": {
    "elis_sender_role": "pm",
    "elis_message_type": "request",
    "elis_policy_version": "1.0.0",
    "elis_sent_at": "2026-06-26T12:00:00Z",
    "elis_task_ref": "t_abc12345",
    "elis_target_role": "advisor",
    "elis_pe_ref": "PE-OPS-AGENT-COMMS-01",
    "elis_gate_ref": "Gate 2"
  }
}
```

### 6.4 Rejection Response

```json
{
  "elis_rejection_code": "REJECTED_SELF_TARGET",
  "elis_rejection_text": "REJECTED: self-target not allowed (pm → pm)."
}
```

### 6.5 Task State Mapping
A2A SUBMITTED/WORKING → Kanban running, INPUT_REQUIRED → blocked, COMPLETED → done, FAILED → blocked or done-with-FAIL-metadata

---

## 7. Kanban State Transition Integration Rules

### 7.1 Standard States
triage → todo → ready (dependencies met) → running → blocked or done

### 7.2 A2A Integration
- Task created → kanban_create → todo
- Dependencies met → auto-promote ready
- Assignee picks up → auto-promote running
- PM dispatches → A2A request + Discord START
- Work completes → kanban_complete + A2A status + Discord SUMMARY
- Work blocks → kanban_block + A2A INPUT_REQUIRED + Discord BLOCKED

### 7.3 Gate Progression
Parent-child dependencies via `parents` parameter on kanban_create. Gate N must reach `done` before Gate N+1 auto-promotes to `ready`.

### 7.4 Evidence Capture
All evidence MUST be in a durable channel (board artifacts directory, Kanban comment, or Discord). Scratch workspace files are NOT durable.

### 7.5 Cleanup Rules
Never delete tasks. Classify blocked as superseded (archive) or deferred (preserve). Never unblock deferred tasks without PO direction.

---

## 8. #elis-pe-reports Macro-Event Integration Rules

### 8.1 Discord Authority Scope
Discord #elis-pe-reports is **authoritative only for human-visible macro-event reporting**. It is NOT authoritative for:
- Kanban task lifecycle state (authoritative source: Kanban board DB)
- GitHub source-control state (authoritative source: GitHub UI / gh CLI)
- PE governance decisions (authoritative source: Kanban comments + metadata + PO approval)

### 8.2 Mandatory Events

- **START**: Task claimed (if task body requires reporting) — PE, Task, Agent, Status=STARTED, Scope, Expected output, Stop condition
- **PASS**: kanban_complete with success — PE, Task, Agent, Status=PASS, Evidence, Verdict
- **FAIL**: kanban_complete with validation failure — PE, Task, Agent, Status=FAIL, Evidence, Defects
- **BLOCKED**: kanban_block called — PE, Task, Agent, Status=BLOCKED, Reason
- **SUMMARY**: Task completed with actionable output — PE, Task, Agent, Summary

### 8.3 Reporting Format

START:
```
PE: <PE identifier>
Task: <Kanban task ID> — <Title>
Agent: <Agent display name>
Status: STARTED
Kanban task ID: <t_xxxx>
Scope: <what will be done>
Not approved: <out-of-scope>
Expected output: <deliverable>
Stop condition: <when worker stops>
```

Terminal event:
```
PE: <PE identifier>
Task: <Kanban task ID> — <Title>
Agent: <Agent display name>
Status: PASS | FAIL | BLOCKED
Kanban task ID: <t_xxxx>
Evidence: <path or reference>
Actions performed: <summary>
Out-of-scope actions: <none or list>
Output / verdict: <detail>
Next required action: <what happens next>
Stop condition: <met>
```

### 8.4 Prohibitions
- No intermediate working-state events
- No speculative next steps in terminal events
- No secrets, tokens, or PII
- #elis-pe-reports is NOT the sole coordination channel

---

## 9. Failure / Retry / Escalation Policy

### 9.1 Failure Classification

| Class | Example | Action |
|-------|---------|--------|
| Transient | Network timeout | Retry 3x with exponential backoff |
| Configuration | Missing credential | Block, report to PO |
| Logic/Policy | Validation FAIL | Narrow editorial correction, re-validate |
| Protocol | Worker exits without complete/block | Dispatcher re-queues, limited retries |
| Resource | OOM, segfault | Block, operator intervention |
| Timeout | Exceeds max_runtime | SIGTERM, re-queue as timed_out |

### 9.2 Retry Limits
- Crashed (protocol violation): 1 retry, then blocked
- Timed out: 2 retries, then blocked
- Validation FAIL: unlimited (each fix → re-validate)
- Blocked for input: unlimited (human unblocks to resume)

### 9.3 Escalation Chain
1. Worker → kanban_block with specific reason
2. 4 hours stale → dispatcher reclaims, re-queues
3. 3 reclaims without progress → auto-notify PM via #elis-pe-reports
4. PM reviews → unblock, reassign, or PO escalation
5. PO escalation → PM notifies Carlos Rocha via Discord

### 9.4 Stale Task Timeout
Default: 4 hours (14400s). Heartbeat required at least once per hour for tasks expected >1 hour. On stale heartbeat: reclaimed, re-queued as ready, no failure counter tick.

---

## 10. Advisor Validation Checklist

### 10.1 Structural Completeness
- [ ] Packet includes all required sections
- [ ] All references resolvable
- [ ] No placeholder text or TODOs
- [ ] Version matches PE gate stage

### 10.2 Policy Compliance
- [ ] No role boundary violations
- [ ] Approval gates respected
- [ ] Loopback-only bindings enforced
- [ ] Implementer/validator separation maintained
- [ ] Scratch workspace not used for durable evidence

### 10.3 Technical Correctness
- [ ] Commands/procedures syntactically valid
- [ ] Rollback plan exists for runtime changes
- [ ] Evidence capture paths accessible
- [ ] Timestamps use ISO 8601 UTC with Z
- [ ] No secrets in plaintext

### 10.4 Artifact Integrity
- [ ] Changed files named
- [ ] Test counts and pass rates reported
- [ ] Decisions documented with rationale
- [ ] Evidence in durable channel

### 10.5 Verdict Output
PASS, FAIL (with specific defects), or BLOCKED (with missing prerequisite named). FAIL is an actionable stepping stone, not a blocker.

---

## 11. Supervisor Implementation / Reporting Checklist

### 11.1 Pre-Execution
- [ ] Confirm task scope matches request
- [ ] Verify credentials/environment readiness
- [ ] Read-only health check of existing state
- [ ] Confirm no conflicting run in progress

### 11.2 Execution
- [ ] Follow procedure exactly as specified
- [ ] Capture PID, command, user, venv, bind assertions
- [ ] Foreground-only shell commands with tee -a evidence redirection
- [ ] No systemd activation without PO approval
- [ ] Emergency cleanup rule ready

### 11.3 Post-Execution Report
Report includes: PE, Task, Agent, Status, Evidence path, Actions performed, Out-of-scope actions, Verdict, Next action, Stop condition.

### 11.4 Evidence Requirements
PID, binding address (must be 127.0.0.1:x), smoke test results, full start command, log output.

---

## 12. PM Coordination Checklist

### 12.1 PE Initiation
- [ ] PE control record created
- [ ] Execution graph defined
- [ ] PO approval obtained
- [ ] All scopes and stop conditions documented
- [ ] Child tasks with correct parent dependencies
- [ ] Each child assigned to correct specialist

### 12.2 Task Dispatch
- [ ] Task body includes all required context
- [ ] Pre-create implementer + validator child tasks
- [ ] Validator auto-promotes on impl done
- [ ] START+SUMMARY reporting requirement included
- [ ] Appropriate workspace_kind

### 12.3 Gate Completion
- [ ] Summary includes concrete artifacts
- [ ] Metadata includes machine-readable facts
- [ ] Code changes needing review: block with review-required
- [ ] Evidence in durable channel

### 12.4 PE Closeout
- [ ] All gates completed and validated
- [ ] Advisor PASS obtained
- [ ] PO closeout approval obtained
- [ ] Final #elis-pe-reports SUMMARY
- [ ] Historical evidence preserved

### 12.5 Emergency Stop
At ~20K+ input tokens or ~80K+ context: complete current action, post state as comment, kanban_block with context-exhaustion reason, require fresh reset.

---

## 13. Future Automation Recommendations

### HIGH Priority
1. **PM inbound A2A server** (port 9502) — successor PE to enable bidirectional flows
2. **Scheduled PM→Advisor dispatch** — cron-based health/status polling

### MEDIUM Priority
3. **Mandatory elis_task_ref enforcement** — update `_build_governed_metadata()` to require task_ref for non-diagnostic operational messages
4. **Cron board-status digest** — daily to #elis-pe-reports
5. **GitHub Issue auto-creation on PE open** — dispatch elis-github

### LOW Priority
6. **Blocked-task auto-escalation** — cron alert for tasks blocked >N hours
7. **Heartbeat digest** — brief status for long-running tasks

### Longer-Term
8. Agent Card auto-discovery in Kanban dispatch
9. Unified A2A message log / audit trail
10. Cross-profile notification routing for completions
11. Structured error taxonomy beyond rejection codes

---

## 14. References

| Reference | Location |
|-----------|----------|
| A2A Policy Module | `/opt/elis/repo/elis/a2a/policy.py` |
| PM Agent Card | `/opt/elis/repo/elis/a2a/pm/agent_card.py` |
| PM Client | `/opt/elis/repo/elis/a2a/pm/client.py` |
| Advisor Agent Card | `/opt/elis/repo/elis/a2a/advisor/agent_card.py` |
| Supervisor Agent Card | `/opt/elis/repo/elis/a2a/supervisor/agent_card.py` |
| Gate 0 Review Report | Kanban task `t_f86444c1` comment #82 |
| ELIS PM Identity | `~/.hermes/profiles/elis-pm/SOUL.md` |
| Kanban Worker Skill | `kanban-worker` skill |
| Kanban Board | `elis-a2a-implementation` |
| A2A Production Closeout | PE-OPS-A2A-PRODUCTION-02 |
| Validated at Gate 2 | Kanban task `t_0aaf1aea` comment #85 |

---

## Revision History

| Version | Date | Author | Change |
|---------|------|--------|--------|
| 0.1 | 2026-06-26 | ELIS PM | Gate 1 DRAFT |
| 1.0 | 2026-06-26 | ELIS PM | APPROVED — incorporated Gate 2 non-blocking recommendations: deterministic elis_task_ref/elis_pe_ref rules, Discord authority scope clarification, PM→GitHub routing preservation |
