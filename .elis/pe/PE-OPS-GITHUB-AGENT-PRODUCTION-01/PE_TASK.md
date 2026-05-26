# PE-OPS-GITHUB-AGENT-PRODUCTION-01 — Restore and Productionise GitHub Agent Write Path

## PE_ID
PE-OPS-GITHUB-AGENT-PRODUCTION-01

## Objective
Restore and productionise the GitHub Agent write path so ELIS has a verified, least-privilege, auditable GitHub operation route using the intended `elis-git-bot` identity, not ambient `rochasamurai` credentials.

## Opening packet
- Lane: Strict
- Baseline HEAD: `904342cfd02ce85dcc9d4f9f05f96eef3e80d530`
- Branch: `feature/pe-ops-github-agent-production-01-restore-productionise-github-agent-write-path`
- Implementer: `infra-impl-b`
- Validator: `infra-val-a`
- Thread: `1508908981849034833`

## Scope
- Restore `/opt/elis/secrets/github-agent.env` or approved credential mount
- Fix GitHub Agent `GH_CONFIG_DIR` permissions so `gh` commands succeed from the agent process
- Verify `elis-git-bot <elis-git-bot@electoralintegrity.org>` as the canonical Git identity for all GitHub Agent operations
- Verify GitHub Agent worktree binding and reset/binding acknowledgement
- Enable/spawn GitHub Agent through the approved route (OpenClaw session or equivalent)
- Perform read-only GitHub readiness checks (e.g. `gh auth status`, `gh repo view`) to confirm the path is clean
- Push/create PR only after explicit PO approval obtained in this thread
- No merge without separate PO approval

## Out of scope
- No credential creation or copying by agents
- No branch protection changes
- No merge automation changes
- No OpenClaw/Hermes config changes outside the GitHub Agent credential mount
- No changes to any other agent's credentials or identity
- No GitHub Agent worktree reset/cleanup during opening phase

## Acceptance criteria

| AC | Criterion |
|----|-----------|
| AC-1 | `/opt/elis/secrets/github-agent.env` (or approved credential mount) is present, readable by the GitHub Agent process, and contains a valid `GH_TOKEN` for `elis-git-bot`. |
| AC-2 | `GH_CONFIG_DIR` is set to an agent-owned path with correct permissions; `gh auth status` exits 0 and reports `elis-git-bot` as the authenticated identity. |
| AC-3 | Git identity is confirmed as `elis-git-bot <elis-git-bot@electoralintegrity.org>` for commits and operations in the GitHub Agent worktree. |
| AC-4 | GitHub Agent is enabled in the approved runtime and can be spawned via the approved route without error. |
| AC-5 | GitHub Agent worktree binding is verified and a reset/binding acknowledgement is committed to the PE artefact directory. |
| AC-6 | Read-only GitHub readiness check passes: `gh repo view rochasamurai/elis` (or equivalent canonical repo) returns without error. |
| AC-7 | No ambient `rochasamurai` GitHub writes are observed during or after the PE; any residual ambient credential is identified and documented. |
| AC-8 | Validator (`infra-val-a`) independently confirms AC-1 through AC-7 with PASS verdict and evidence committed to `.elis/pe/PE-OPS-GITHUB-AGENT-PRODUCTION-01/REVIEW.md`. |

## Known starting blockers
- GitHub Agent registered but not enabled.
- Credential/env file missing: `/opt/elis/secrets/github-agent.env`
- GitHub Agent `GH_CONFIG_DIR` permission issue.
- Intended Git identity: `elis-git-bot <elis-git-bot@electoralintegrity.org>`
- Ambient `gh` identity previously observed: `rochasamurai`
- GitHub Agent fresh session/spawn/readiness path blocked.
- PR #457 required manual PO GitHub exception due to the above blockers.

## Implementation boundaries
- Write path: repository files only within the approved file scope for the opening phase
- No credential creation or copying
- No secret printing
- No auth profile edits
- No service restart/reload
- No OpenClaw/Hermes runtime config change
- No `tools.sessions.visibility=all`
- No GitHub push, PR, or merge until PO explicitly approves after Supervisor verification

## First-pass file scope (opening phase only)
- `CURRENT_PE.md`
- `.elis/state/current_pe.json`
- `.elis/pe/PE-OPS-GITHUB-AGENT-PRODUCTION-01/PE_TASK.md`
- `.elis/pe/PE-OPS-GITHUB-AGENT-PRODUCTION-01/HANDOFF.md`

## Approved implementation file scope (post-opening, requires PM authorisation to unlock)
- `/opt/elis/secrets/github-agent.env` (credential restore — PO action, not agent)
- `openclaw/openclaw.json` (GitHub Agent enable — requires PO approval)
- `.elis/pe/PE-OPS-GITHUB-AGENT-PRODUCTION-01/REVIEW.md` (validator-owned)
- Any governance/runbook doc for the restored GitHub Agent path

## Validation approach
- Validator (`infra-val-a`) runs independently from `infra-val-a` worktree
- Validator confirms each AC in REVIEW.md with pass/fail verdict and evidence
- Gate 1: PM reviews implementation commit; Gate 2: PO approves after validator PASS

## Risks
| Risk | Mitigation |
|------|-----------|
| `github-agent.env` must be recreated by PO manually (agent cannot create credentials) | PO pre-flight: create the file with a valid `elis-git-bot` PAT before implementation starts |
| `GH_CONFIG_DIR` fix may require service restart | Gate: implementer documents the fix; PO approves restart separately |
| `elis-git-bot` PAT may be expired | PO verifies token validity before marking AC-1 complete |
| Residual `rochasamurai` ambient auth may re-appear if env is not isolated | Implementer must confirm GitHub Agent process uses its own `GH_CONFIG_DIR` and not the system default |

## Rollback / safety notes
- All repository changes are reversible via `git revert` or branch abandonment
- Credential mount restoration is a PO action; rollback is removing the file
- No service or runtime state is modified during opening phase; rollback requires no service action
- If any hard stop is violated, PM halts and notifies PO before any further action

## Hard stops
- No credential creation or copying by any agent
- No secret printing
- No auth profile edits
- No GitHub push
- No PR creation
- No merge
- No service restart/reload
- No OpenClaw/Hermes runtime config change
- No `tools.sessions.visibility=all` ad hoc change
- No GitHub Agent worktree reset/cleanup
- No implementation dispatch
- No validator dispatch
- No `sessions_spawn` or `sessions_send`
