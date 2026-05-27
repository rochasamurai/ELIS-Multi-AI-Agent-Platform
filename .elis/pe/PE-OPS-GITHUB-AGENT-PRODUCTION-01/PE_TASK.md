# PE-OPS-GITHUB-AGENT-PRODUCTION-01 — Productionise GitHub Agent via GitHub App Installation-Token Auth

## PE_ID
PE-OPS-GITHUB-AGENT-PRODUCTION-01

## Objective
Productionise the GitHub Agent so ELIS has a verified, least-privilege, auditable GitHub operation route using the ELIS GitHub App installation-token model (App: "ELIS GitHub", ID: 3884378, Installation: 136081387), not a long-lived PAT and not ambient `rochasamurai` credentials. `bin/gh-agent` generates a short-lived installation access token at runtime; no token or private key is ever printed or persisted.

## Opening packet
- Lane: Strict
- Baseline HEAD: `904342cfd02ce85dcc9d4f9f05f96eef3e80d530`
- Branch: `feature/pe-ops-github-agent-production-01-github-app-launcher`
- Implementer: `infra-impl-b`
- Validator: `infra-val-a`
- Thread: `1508908981849034833`

## Scope
- `bin/gh-agent`: implement GitHub App installation-token launcher (DONE — commit 2f67f8c)
- `/opt/elis/secrets/github-agent.env`: must contain `GITHUB_APP_ID`, `GITHUB_APP_INSTALLATION_ID`, `GITHUB_APP_PRIVATE_KEY_PATH` (PO-provisioned)
- GitHub App private key at `GITHUB_APP_PRIVATE_KEY_PATH`: owned by `elis-github:elis-github-secrets`, mode 640 (PO-provisioned)
- Rebuild `github-agent` as a linked worktree (Phase 2 — pending merge)
- Create sudoers rule for `elis-github` execution wrapper (Phase 4 — pending PO approval)
- Enable GitHub Agent in OpenClaw after worktree and launcher are correct (Phase 5 — pending PO approval)
- Validate read-only GitHub App auth before any write operation
- Push/create PR only after explicit PO approval obtained in this thread
- No merge without separate PO approval

## Out of scope
- No long-lived PAT as production auth path
- No `gh auth login` as production path
- No ambient `rochasamurai` auth fallback
- No credential creation or copying by agents
- No branch protection changes
- No merge automation changes

## Acceptance criteria

| AC | Criterion |
|----|-----------|
| AC-1 | `/opt/elis/secrets/github-agent.env` is present, readable by the `elis-github` process, and contains `GITHUB_APP_ID=3884378`, `GITHUB_APP_INSTALLATION_ID=136081387`, and `GITHUB_APP_PRIVATE_KEY_PATH` pointing to the provisioned private key. |
| AC-2 | `/opt/elis/secrets/elis-github.private-key.pem` is present, owned by `elis-github:elis-github-secrets`, mode 640, and readable by the `elis-github` process. |
| AC-3 | `bin/gh-agent` generates a short-lived GitHub App installation access token via RS256 JWT exchange; the token is never printed, written to disk, or persisted beyond the `gh` subprocess. |
| AC-4 | `GH_CONFIG_DIR` is isolated to the GitHub Agent workspace; no ambient `rochasamurai` keyring or `~/.config/gh` is used. |
| AC-5 | GitHub Agent linked worktree is rebuilt from `origin/main` with correct ownership (`elis-github:elis-github`) after merge. |
| AC-6 | Read-only GitHub App auth validation passes: installation repository access confirmed without push or write. |
| AC-7 | No ambient `rochasamurai` GitHub operations are performed by the GitHub Agent; isolation is verified. |
| AC-8 | Validator (`infra-val-a`) independently confirms AC-1 through AC-7 with PASS verdict and evidence committed to `.elis/pe/PE-OPS-GITHUB-AGENT-PRODUCTION-01/REVIEW.md`. |

## Known starting blockers (at PE open — updated 2026-05-27)
- ~~Credential/env file missing~~ — PO-provisioned with GitHub App metadata.
- ~~GitHub Agent not enabled~~ — deferred to Phase 5 pending launcher merge and worktree rebuild.
- Standalone clone at `/opt/elis/agent-worktrees/github-agent` not yet replaced by linked worktree.
- Sudoers rule for `elis-github` execution wrapper not yet created.
- `bin/gh-agent` feature branch not yet pushed/merged to main.

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
- `bin/gh-agent` (DONE — commit 2f67f8c on feature branch, pending push/merge)
- `/opt/elis/secrets/github-agent.env` (PO-provisioned with GitHub App metadata — agents must not edit)
- `/opt/elis/secrets/elis-github.private-key.pem` (PO-provisioned — agents must not read or print)
- OpenClaw config (GitHub Agent enable — requires PO approval and Supervisor path)
- `.elis/pe/PE-OPS-GITHUB-AGENT-PRODUCTION-01/REVIEW.md` (validator-owned)
- Any governance/runbook doc for the GitHub App launcher operational path

## Validation approach
- Validator (`infra-val-a`) runs independently from `infra-val-a` worktree
- Validator confirms each AC in REVIEW.md with pass/fail verdict and evidence
- Gate 1: PM reviews implementation commit; Gate 2: PO approves after validator PASS

## Risks
| Risk | Mitigation |
|------|-----------|
| Private key read requires `elis-github` user — `samurai` cannot access it | All live auth validation runs as `elis-github` via the sudoers execution wrapper (Phase 4) |
| GitHub App installation token exchange is a live API call — cannot be unit-tested offline | Static + fail-closed checks completed; live validation gated on PO approval (Phase 5) |
| Linked worktree rebuild requires removal of standalone clone — destructive | PO approval required per-step; linked backup preserved at `github-agent.linked-backup.20260508T141916` |
| OpenClaw config edit requires Supervisor path (unverified schema risk) | PM must not edit `openclaw.json`; route via Supervisor only |
| Residual `rochasamurai` ambient auth may re-appear if `GH_CONFIG_DIR` is not isolated | `bin/gh-agent` exports `GH_CONFIG_DIR` to isolated workspace path; no keyring fallback |

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
