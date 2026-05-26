# HANDOFF — PE-OPS-GITHUB-AGENT-PRODUCTION-01

## Summary
This PE restores and productionises the GitHub Agent write path so ELIS has a verified, least-privilege, auditable GitHub operation route using the intended `elis-git-bot` identity. The immediate trigger is PR #457 requiring a manual PO GitHub exception because all normal GitHub Agent paths were blocked. Discord remains the PO-facing channel. The GitHub Agent is strictly the write-path tool — no governance or merge authority beyond what the PO approves per operation.

## Opening evidence
- Correction noted: canonical repo path is `/opt/elis/repo`; PM authorised worktree is `/opt/elis/agent-worktrees/pm`.
- PO accepted reset/binding ACK on 2026-05-26 in thread `1508908981849034833`.
- Opening authorised for planning/opening only. No implementation, no credential change, no push, no PR, no merge, no runtime/config/service change.

## Known starting blockers
- GitHub Agent registered but not enabled in OpenClaw runtime.
- Credential/env file missing: `/opt/elis/secrets/github-agent.env`
- GitHub Agent `GH_CONFIG_DIR` permission issue prevents `gh` commands from succeeding.
- Intended Git identity: `elis-git-bot <elis-git-bot@electoralintegrity.org>`
- Ambient `gh` identity previously observed: `rochasamurai` (must be eliminated from agent write path).
- GitHub Agent fresh session/spawn/readiness path blocked.
- PR #457 required manual PO GitHub exception as a result.

## Expected changes (post-opening, unlocked by PM after PO/Supervisor verification)
- PO action (not agent): create/restore `/opt/elis/secrets/github-agent.env` with valid `elis-git-bot` PAT
- `openclaw/openclaw.json` update to enable GitHub Agent (PO approval required before change)
- `GH_CONFIG_DIR` permission fix in GitHub Agent process environment
- `.elis/pe/PE-OPS-GITHUB-AGENT-PRODUCTION-01/REVIEW.md` (validator-owned)
- Any governance/runbook doc for the restored GitHub Agent operational path

## Design decisions
- PO is the only actor who may create or restore credentials — agents must not create, copy, or print secrets.
- GitHub Agent worktree binding must be verified and acknowledged before any write operation.
- All GitHub write operations (push, PR, merge) require explicit PO approval per operation, not just at PE open.
- Ambient `rochasamurai` credential must be quarantined before GitHub Agent is declared production-ready.

## Backup / rollback plan
- All repository changes are reversible via `git revert` or branch abandonment — no service action required.
- Credential mount restore is a PO action; rollback is removing the file.
- No service or runtime state is modified during opening phase.
- If any hard stop is violated at any point, PM halts and notifies PO before any further action.

## Status packet
- Base: `origin/main` @ `904342cfd02ce85dcc9d4f9f05f96eef3e80d530`
- Branch: `feature/pe-ops-github-agent-production-01-restore-productionise-github-agent-write-path`
- Implementer: `infra-impl-b`
- Validator: `infra-val-a`
- PM role: coordination only
- Thread: `1508908981849034833`
- Canonical repo: `/opt/elis/repo`
- PM worktree: `/opt/elis/agent-worktrees/pm`

## Opening phase hard stops (active until PO/Supervisor verify this commit)
- No credential creation or copying by any agent
- No secret printing
- No auth profile edits
- No GitHub push
- No PR creation
- No merge
- No service restart/reload
- No OpenClaw/Hermes runtime config change
- No `tools.sessions.visibility=all`
- No GitHub Agent worktree reset/cleanup
- No implementation dispatch
- No validator dispatch
- No `sessions_spawn` / `sessions_send`
