# HANDOFF — PE-OPS-GITHUB-AGENT-PRODUCTION-01

## Summary
This PE productionises the GitHub Agent using the ELIS GitHub App installation-token model. The production auth path is `bin/gh-agent` generating a short-lived installation access token at runtime via RS256 JWT signing (App: "ELIS GitHub", ID: 3884378, Installation: 136081387, installed on `rochasamurai/ELIS-Multi-AI-Agent-Platform`). No long-lived PAT is used. No ambient `rochasamurai` auth is used. The token lives only in the `gh` subprocess environment and is never printed or persisted.

## Phase status (2026-05-27)

| Phase | Description | Status |
|-------|-------------|--------|
| Phase 0 | Evidence preservation | COMPLETE — sanitised branch pushed to origin |
| Phase 1 | `bin/gh-agent` GitHub App launcher | IMPLEMENTED — commit `2f67f8c`, not yet pushed |
| Phase 2 | Linked worktree rebuild | PENDING — awaiting Phase 1 merge |
| Phase 4 | Sudoers rule for `elis-github` wrapper | PENDING — PO approval required |
| Phase 5 | Validation and OpenClaw enablement | PENDING — PO approval required |

## Secret provisioning (PO-provisioned, 2026-05-27)
- `/opt/elis/secrets/elis-github.private-key.pem`: `elis-github:elis-github-secrets`, mode 640
- `/opt/elis/secrets/github-agent.env`: contains `GITHUB_APP_ID`, `GITHUB_APP_INSTALLATION_ID`, `GITHUB_APP_PRIVATE_KEY_PATH`

## Known remaining blockers
- `bin/gh-agent` feature branch not yet pushed or merged to `origin/main`.
- Standalone clone at `/opt/elis/agent-worktrees/github-agent` not yet replaced by linked worktree.
- Sudoers rule for `elis-github` execution wrapper not yet created (required for live auth validation).
- OpenClaw config edit requires Supervisor path — PM must not edit `openclaw.json` directly.

## Design decisions
- Production auth model: GitHub App installation-token only. No PAT, no `gh auth login`, no ambient `rochasamurai` auth.
- The private key is held at `GITHUB_APP_PRIVATE_KEY_PATH`; readable only by `elis-github`/`elis-github-secrets`.
- `bin/gh-agent` is the sole production launcher; all `gh` calls go through it.
- `GH_CONFIG_DIR` is isolated to the GitHub Agent workspace to prevent keyring/ambient auth fallback.
- All GitHub write operations (push, PR, merge) require explicit PO approval per operation.
- PO is the only actor who may create or modify credentials.
- OpenClaw config changes require Supervisor path — PM coordinates only.

## Backup / rollback plan
- `bin/gh-agent` changes are reversible via `git revert`.
- Linked worktree rebuild: linked backup preserved at `github-agent.linked-backup.20260508T141916`.
- Evidence preservation: sanitised branch `chore/github-agent-evidence-closeout-sanitized` pushed to origin (commit `5f1482f`).
- If any hard stop is violated, PM halts and notifies PO before any further action.

## Status packet
- Base: `origin/main` @ `89b16beca9310790b5bef20bd5da4580bd9b1678`
- Implementation branch: `feature/pe-ops-github-agent-production-01-github-app-launcher`
- Implementation commit: `2f67f8c556d9ec92a99c1a9aa78f766045a1b50e`
- Implementer: `infra-impl-b`
- Validator: `infra-val-a`
- PM role: coordination only
- Thread: `1508908981849034833`
- PM worktree: `/opt/elis/agent-worktrees/pm`

## Active hard stops
- No credential creation or copying by any agent
- No secret printing
- No `gh auth login` as production path
- No ambient `rochasamurai` auth
- No GitHub push / PR / merge without explicit PO approval per operation
- No service restart/reload without PO approval
- No OpenClaw config edit by PM — Supervisor path only
- No linked worktree rebuild without PO approval
- No sudoers changes without PO approval
- No live GitHub API call before Phase 5 PO approval
- No validator dispatch without PO approval
