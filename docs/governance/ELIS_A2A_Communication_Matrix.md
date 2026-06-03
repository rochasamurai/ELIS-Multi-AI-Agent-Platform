# ELIS A2A Communication Matrix — Phase 1

**Status:** Phase 1 — Local-only A2A protocol specification for structured internal communication
among ELIS Advisor, ELIS PM, and ELIS Supervisor.

**Version:** 1.0
**Date:** 2026-05-09
**Owner:** Carlos Rocha, Product Owner
**Scope:** A2A message protocol, agent identities, allowed pairs, message types, payload schemas,
routing rules, gateway binding, and hard prohibitions.

---

## 1. Purpose

This document defines Phase 1 of the Agent-to-Agent (A2A) communication matrix for the ELIS
multi-agent system. It establishes a minimal, local-only communication protocol that enables
structured message exchange, evidence requests, advisory review, and read-only diagnostics
among the three governance agents:

- ELIS Advisor
- ELIS PM
- ELIS Supervisor

A2A supports governed, auditable inter-agent messaging without granting execution, validation,
GitHub write, or configuration authority to any agent through the A2A channel.

---

## 2. Agent Identities and Roles

| Identity | Canonical ID | Role |
|----------|-------------|------|
| ELIS Advisor | `elis-advisor` | Advisory-only agent. Reviews PE packets, assesses risk, drafts governance advice, and requests evidence. May not dispatch, implement, validate, modify config, or write to GitHub. |
| ELIS PM | `elis-pm` | Project Manager agent. Orchestrates PE assignments, routes messages, dispatches implementers/validators as authorised, and receives status packets. |
| ELIS Supervisor | `elis-supervisor` | Advisory and operational agent. Diagnoses gateway/service health, verifies auth and connectivity, inspects logs, and reports operational risk. May not dispatch, validate PE work, modify config, write to GitHub, or merge. |

### 2.1 Phase-1 Only Agents

The following agents are **explicitly excluded** from Phase-1 A2A:
- All implementer agents (`harvest-impl-a`, `screen-impl-b`, `extract-impl-a`, `synth-impl-b`,
  `prisma-impl-b`, `prog-impl-a`, `prog-impl-b`, `infra-impl-a`, `infra-impl-b`)
- All validator agents (`harvest-val-b`, `screen-val-a`, `extract-val-b`, `synth-val-a`,
  `prisma-val-a`, `prog-val-a`, `prog-val-b`, `infra-val-a`, `infra-val-b`)
- GitHub Agent (future A2A participant — see §2.2)
- Any agent not listed in Section 2

### 2.2 Future A2A Participant — github-agent

**Status:** Mailbox creation deferred to Gate 2. No A2A mailbox exists for github-agent in Phase 1.

The GitHub Agent (`github-agent`) is designated as a future A2A request/report participant.
Once its A2A mailbox is created in Gate 2, the following communication pairs will be added:

```
PM <-> GitHub Agent
```

**Planned A2A message types (post-mailbox creation):**
- `GITHUB_OPERATION_REQUEST_V1` — PM requests a GitHub write operation
- `GITHUB_OPERATION_REPORT_V1` — GitHub Agent reports operation result
- `GITHUB_STATUS_REQUEST_V1` — PM requests GitHub Agent status
- `GITHUB_STATUS_REPORT_V1` — GitHub Agent reports operational status

**Authority constraint:** github-agent has **no authority expansion via A2A**. Its A2A
participation does not grant it implementation, validation, config editing, credential access,
or any GitHub write authority beyond what is already defined in its operating model
(`ELIS_GitHub_Agent_Operating_Model.md`). A2A is a communication channel only — the
permission matrix in the GitHub Agent operating model remains the sole source of
authority boundaries for the github-agent role.

Until Gate 2, all github-agent communication uses the Discord-based routing path defined
in the PM orchestration rules.

**Prohibited during Gate 1:**
- Creating github-agent A2A mailbox files
- Registering github-agent in gateway configuration
- Any runtime A2A setup for github-agent

---

## 3. Allowed Communication Pairs

Phase 1 allows exactly three communication pairs:

```
Advisor   <->   PM
Advisor   <->   Supervisor
PM        <->   Supervisor
```

The full agent inventory (18+ agents from the OpenClaw configuration) is **not** exposed
through A2A. Only the three Phase-1 identities defined in Section 2 may send or receive
A2A messages.

---

## 4. Message Types

| Message Type | Description | Allowed Senders | Allowed Recipients |
|-------------|-------------|-----------------|-------------------|
| `structured_message` | Free-form structured message with subject, body, and optional references. | All three agents | All three agents |
| `evidence_request` | Request for specific evidence items from a peer agent. Includes source reference and expected status. | Advisor, PM, Supervisor | Advisor, PM, Supervisor |
| `advisory_review` | Advisory review verdict with evidence citation and risk classification. Advisory only — not an official validation verdict. | Advisor, Supervisor | PM |
| `diagnostic_query` | Read-only diagnostic check request. Limited to pre-approved commands (service status, connectivity, auth). | PM, Supervisor | Supervisor, Advisor |
| `diagnostic_response` | Response to a diagnostic query with read-only result payload. | Supervisor, Advisor | PM, Supervisor |
| `acknowledgement` | Confirms receipt of a message. | All three agents | All three agents |
| `error` | Error notification when a message cannot be processed. | All three agents | All three agents |

---

## 5. Message Envelope Schema

All A2A messages use the envelope schema defined in `schemas/a2a_envelope.schema.json`.
Key envelope fields:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `a2a_version` | string | Yes | Must be `"1.0"`. |
| `message_id` | string (uuid) | Yes | Unique message identifier. |
| `in_reply_to` | string (uuid) | No | If replying, the original message_id. |
| `timestamp` | string (ISO 8601) | Yes | UTC creation timestamp. |
| `sender` | string | Yes | One of: `elis-advisor`, `elis-pm`, `elis-supervisor`. |
| `recipient` | string | Yes | One of: `elis-advisor`, `elis-pm`, `elis-supervisor`. |
| `message_type` | string | Yes | One of the types in Section 4. |
| `payload` | object | Yes | Message content (see Section 6). |
| `ttl_seconds` | integer | No | Default 300. Messages may be discarded after TTL. |

---

## 6. Payload Content per Message Type

### 6.1 structured_message

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `subject` | string | Yes | Short subject line. |
| `body` | string | Yes | Free-text message body. |
| `references` | array[string] | No | Document/file references cited. |
| `classification` | string | No | `governance`, `evidence`, `advisory`, `diagnostic`, `operational`. |

### 6.2 evidence_request

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `subject` | string | Yes | Summary of evidence being requested. |
| `body` | string | Yes | Detailed description of what evidence is needed. |
| `evidence_items` | array[object] | Yes | Each item: `{source, summary, status}` where status is `available`, `missing`, or `pending`. |
| `references` | array[string] | No | Supporting references. |
| `classification` | string | No | Default: `evidence`. |

### 6.3 advisory_review

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `subject` | string | Yes | PE or topic under review. |
| `body` | string | Yes | Detailed advisory analysis. |
| `verdict` | string | Yes | `pass`, `fail`, or `inconclusive`. **Advisory only** — not an official validation verdict. |
| `risk_level` | string | No | `low`, `medium`, `high`, `critical`. |
| `evidence_items` | array[object] | No | Evidence cited in the review. |
| `references` | array[string] | No | Supporting references. |
| `classification` | string | No | Default: `advisory`. |

### 6.4 diagnostic_query

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `subject` | string | Yes | Summary of the diagnostic check. |
| `diagnostic_command` | string | Yes | Read-only check command. Allowed commands: `status`, `connectivity`, `auth`, `logs_inspect`. |
| `body` | string | No | Additional context for the diagnostic. |
| `classification` | string | No | Default: `diagnostic`. |

### 6.5 diagnostic_response

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `subject` | string | Yes | Summary of the diagnostic result. |
| `diagnostic_result` | object | Yes | `{status, output}` with read-only result payload. |
| `classification` | string | No | Default: `diagnostic`. |

### 6.6 acknowledgement

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `subject` | string | Yes | Typically "ACK: <original subject>". |
| `body` | string | Yes | Confirmation text. |
| `classification` | string | No | Default: `operational`. |

### 6.7 error

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `subject` | string | Yes | Error summary. |
| `error_details` | object | Yes | `{code, message}` describing the error. |
| `classification` | string | No | Default: `operational`. |

---

## 7. Routing Rules

1. **Envelope validation.** Every A2A message must validate against `a2a_envelope.schema.json`.
   Invalid messages must be rejected with an `error` response.

2. **Pair validation.** Only the three approved pairs may exchange messages. A message whose
   sender/recipient pair falls outside the allowed pairs must be rejected.

3. **Identity validation.** `sender` and `recipient` must each be one of the three approved
   identities (`elis-advisor`, `elis-pm`, `elis-supervisor`).

4. **Time-to-live.** Messages with `ttl_seconds` exceeded since `timestamp` may be discarded
   by the receiver.

5. **Acknowledgement.** Receivers should respond with an `acknowledgement` message within
   30 seconds of receipt for non-error messages.

6. **No relaying.** A2A does not support message relaying. Only the intended recipient may
   process a message.

---

## 8. Gateway Binding

### 8.1 Network Binding

The A2A gateway **must** bind to:

| Interface | Address | Port | Protocol |
|-----------|---------|------|----------|
| loopback  | `127.0.0.1` | `24001` | HTTP / WebSocket |

- No external network interfaces may be exposed.
- No TLS is required for local-only traffic on the loopback interface.
- The port `24001` is reserved for A2A gateway traffic.

### 8.2 Startup Behaviour

- The gateway starts as a user-level process (not system-level).
- Expected startup command: `node a2a-gateway.js` or equivalent launch mechanism.
- Gateway logs to stdout and optionally to `~/.elis/a2a/gateway.log`.
- Gateway must verify local-only binding (`127.0.0.1:24001`) on startup and refuse to start
  if any external interface is configured.

### 8.3 Health Check

```
GET http://127.0.0.1:24001/health
→ {"status": "ok", "a2a_version": "1.0", "agents": ["elis-advisor", "elis-pm", "elis-supervisor"]}
```

### 8.4 Message Endpoint

```
POST http://127.0.0.1:24001/message
Content-Type: application/json
Body: <validated A2A envelope JSON>
→ {"status": "accepted", "message_id": "<uuid>"}
```

---

## 9. Hard Prohibitions

The following actions are **strictly prohibited** through the A2A channel:

| Prohibition | Rationale |
|-------------|-----------|
| **No implementation** | Implementer agents are not exposed. A2A may not carry file write, code generation, or implementation commands. |
| **No official validation** | Official validation verdicts must use the standard REVIEW process. A2A advisory review is advisory only. |
| **No GitHub writes** | A2A may not create, modify, or merge PRs, push commits, or write to any Git repository. |
| **No service restarts** | A2A may not issue restart commands for Hermes, OpenClaw, systemd services, or any infrastructure component, unless the minimal local prototype explicitly requires gateway restarts. |
| **No config edits** | A2A may not modify OpenClaw, Hermes, or any system configuration files. |
| **No secret/token changes** | A2A may not provision, rotate, or expose secrets, tokens, credentials, or API keys. |
| **No PR creation or merges** | A2A may not create pull requests or merge changes. |
| **No PO approvals** | A2A may not issue PO-level approvals or authorisations. |
| **No dispatch of agent inventory** | The full OpenClaw agent inventory (18+ agents) must not be exposed through A2A. Only the three Phase-1 identities may be visible. |

---

## 10. Validation Requirements

| Check | Description |
|-------|-------------|
| Envelope schema validation | Every message validated against `a2a_envelope.schema.json`. |
| Pair validation | Enforcement of the three allowed pairs. |
| Identity validation | No unknown agent IDs. |
| Loopback binding | Gateway rejects external IP bindings. |
| Prohibition enforcement | No prohibited message types or payloads pass through. |
| Read-only enforcement | `diagnostic_query` limited to pre-approved commands. |

---

## 11. Phase 1 File Inventory

| File | Description |
|------|-------------|
| `schemas/a2a_envelope.schema.json` | JSON Schema for A2A message envelope |
| `docs/governance/ELIS_A2A_Communication_Matrix.md` | This document — protocol specification |
| `docs/openclaw/ELIS_A2A_GATEWAY_SPEC.md` | Gateway implementation specification |

---

## 12. Relationship to Other Agents

- **ELIS PM** (`pm` in OpenClaw config) is the same identity as `elis-pm` for A2A purposes.
- **ELIS Advisor** is deployed on Hermes (`docs/hermes/ELIS_ADVISOR_HERMES_RUNBOOK.md`),
  not in OpenClaw. Its A2A identity is `elis-advisor`.
- **ELIS Supervisor** is also deployed on Hermes
  (`docs/hermes/ELIS_SUPERVISOR_CHANNEL_BINDING.md`). Its A2A identity is `elis-supervisor`.
- The A2A gateway runs independently of both Hermes and OpenClaw, on `127.0.0.1:24001`.

---

## 13. Phase 1 Blocker Classifications

When Phase 1 evidence is incomplete or a boundary is violated, classify the blocker explicitly:

- `A2A_IDENTITY_UNAUTHORISED`
- `A2A_PAIR_DISALLOWED`
- `A2A_LOOPBACK_VIOLATION`
- `A2A_READ_ONLY_BOUNDARY_BROKEN`
- `A2A_SCHEMA_OR_ENVELOPE_MISMATCH`
- `A2A_FUTURE_RUNTIME_GATED`
- `A2A_DISPATCH_BLOCKED`

These classifications are advisory/governance labels only. They do not authorise runtime execution, implementation dispatch, or live routing.

---

## 14. Future Runtime Gates (Not in Phase 1)

Any live A2A implementation requires separate approval and must satisfy all of the following before deployment:

1. approved schema artefact and validation tests;
2. runtime code review and commit evidence;
3. service-unit or launch-wrapper review;
4. OpenClaw/Hermes config review if any runtime binding is introduced;
5. explicit no-secrets/no-auth-change check;
6. live routing change approval;
7. rollback plan and verification evidence.

Phase 1 does not satisfy these gates; it only defines the governed protocol/spec boundary.
