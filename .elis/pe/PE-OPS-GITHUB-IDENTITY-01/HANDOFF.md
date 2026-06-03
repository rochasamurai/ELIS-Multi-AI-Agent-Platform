# HANDOFF — PE-OPS-GITHUB-IDENTITY-01

**Gate:** 1 — Implementation
**Date:** 2026-06-03
**Agent:** infra-impl-b
**Branch:** feature/pe-ops-github-identity-01-enforce-elis-github-production-identity
**Base branch:** main

---

## 1. Classification

| Code | Description |
|------|-------------|
| `GITHUB_ACTIONS_RUNNER_DISPATCH_PATH_ORPHANED` | GitHub Actions self-hosted runner dispatch path (`implementer-runner.yml`, `[self-hosted, elis-server]` labels) has no runner installed or registered. Path is not provisioned. |
| `DOCUMENTED_DISPATCH_PATH_NOT_PROVISIONED` | The workflow dispatch path is documented in governance docs as non-functional until a PO-approved provisioning PE enables it. |
| `PM_GUIDANCE_STALE_AFTER_ELIS_GITHUB_CREATION` | PM documentation (`docs/openclaw/workspace-pm/AGENTS.md` §3.1) updated to reflect that the automatic dispatch chain is non-functional until runner is provisioned. |
| `IMPLEMENTER_RUNNER_WORKFLOW_UNUSABLE` | `implementer-runner.yml` references `[self-hosted, elis-server]` labels but no runner exists. Workflow cannot execute CI steps. |

---

## 2. Files Changed

| Path | Change |
|------|--------|
| `docs/governance/ELIS_GitHub_Agent_Operating_Model.md` | Added §1.1 identity/actor terminology table; added §4.4a Mandatory Launcher Rule; added §4.4b raw `gh` policy with `TEMPORARY_HUMAN_GITHUB_AUTH_RISK`/`GITHUB_ACTOR_MISMATCH` classification; added §4.4c A2A flow stub (mailbox deferred to Gate 2); added §4.4d secret boundary section documenting `/opt/elis/secrets/github-agent.env` existence/permissions requirements. |
| `docs/openclaw/workspace-pm/AGENTS.md` | Updated §3.1 with dispatch-path correction: `GITHUB_ACTIONS_RUNNER_DISPATCH_PATH_ORPHANED` classification; `implementer-runner.yml` chain non-functional until runner provisioned; current ELIS production path favours governed OpenClaw/Hermes invocation; ELIS GitHub is governed operations actor not runner replacement. Verified §4.1 PR Merge Routing is accurate — no update needed. |
| `docs/governance/ELIS_A2A_Communication_Matrix.md` | Added §2.2 future A2A participant (github-agent) with mailbox creation deferred to Gate 2; documented that github-agent has no authority expansion via A2A. |

---

## 3. Documentation Changes Summary

### 3.1 Identity/Actor Terminology (§1.1 in GitHub Agent Operating Model)

Added canonical identity table documenting four bindings of the ELIS GitHub production identity:
- OS user `elis-github`
- Git commit author `elis-git-bot <elis-git-bot@electoralintegrity.org>`
- GitHub API/PR actor `app/elis-github`
- GitHub.com bot account `elis-git-bot`

Security context note clarifies these are distinct bindings of the same identity, governed by the permission matrix and launcher rule.

### 3.2 Mandatory Launcher Rule (§4.4a)

All mutating GitHub CLI operations MUST use `bin/gh-agent`. Direct `gh` for mutating operations is prohibited. Scope covers PR creation, update, review, merge, comment, and push.

### 3.3 Raw `gh` Policy (§4.4b)

Direct `gh` permitted only for documented read-only operations. Any invocation resolving to `rochasamurai` must be classified `TEMPORARY_HUMAN_GITHUB_AUTH_RISK` or `GITHUB_ACTOR_MISMATCH`.

### 3.4 A2A Flow Stub (§4.4c)

github-agent A2A mailbox creation deferred to Gate 2. Planned message types listed.

### 3.5 Secret Boundary (§4.4d)

`/opt/elis/secrets/github-agent.env` existence/permissions requirements documented. File contents not inspected.

### 3.6 PM Dispatch Path Correction (§3.1 in workspace-pm AGENTS.md)

GitHub Actions self-hosted runner dispatch classified `GITHUB_ACTIONS_RUNNER_DISPATCH_PATH_ORPHANED`. Must not be treated as active dispatch path until runner is installed, registered, governed, and PO-approved.

### 3.7 A2A Participant Registration (§2.2 in A2A Communication Matrix)

github-agent added as future A2A participant. No authority expansion via A2A. Mailbox creation deferred to Gate 2.

---

## 4. Confirmation

- [x] **No host-runtime changes:** No systemd services modified, no packages installed, no user accounts created, no network configuration changed.
- [x] **No secrets inspected:** `/opt/elis/secrets/github-agent.env` contents not read, viewed, or accessed.
- [x] **No GitHub writes:** No `git push`, `gh` commands, PR creation, or remote mutations executed.
- [x] **No credential mutation:** No tokens, credentials, or authentication state created, rotated, or modified.
- [x] **No .git/config editing:** No remote URL, user, or credential configuration changed.
- [x] **No IDENTITY.md, TOOLS.md, or SOUL.md edits:** Persistent runtime files unchanged.
- [x] **No OpenClaw or Hermes config changes.**
- [x] **No github-agent A2A mailbox files created.**
- [x] **No validator dispatched.**

---

## 5. Commit

**Commit SHA:** `e2e35680`

**Commit message:** `docs(gate-1): wire ELIS GitHub production identity into governance docs [PE-OPS-GITHUB-IDENTITY-01]`

---

## 6. Gate 1 Completion Status

**Status:** IMPLEMENTATION_COMPLETE — awaiting commit and push.

All four deliverables implemented:
| Deliverable | Status |
|-------------|--------|
| 1.1 — GitHub Agent Operating Model updates | ✅ Complete |
| 1.2 — workspace-pm AGENTS.md §3.1 dispatch-path correction | ✅ Complete |
| 1.3 — A2A Communication Matrix github-agent participant | ✅ Complete |
| 1.4 — HANDOFF.md | ✅ Complete |

---

*HANDOFF.md · PE-OPS-GITHUB-IDENTITY-01 · Gate 1 · infra-impl-b · 2026-06-03*