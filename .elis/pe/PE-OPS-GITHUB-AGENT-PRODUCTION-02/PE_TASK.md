# PE-OPS-GITHUB-AGENT-PRODUCTION-02 — Rebuild GitHub Agent Worktree and Execution Boundary

## PE_ID
PE-OPS-GITHUB-AGENT-PRODUCTION-02

## Objective
Replace the invalid standalone clone at `/opt/elis/agent-worktrees/github-agent` with a proper linked worktree from the canonical repository at `/opt/elis/repo`. Preserve the GitHub Agent isolation model and prepare for Phase 4 (sudoers) and Phase 5 (live auth validation) in later PEs.

## Opening packet
- Lane: Strict
- Baseline HEAD: `83d18db4b892709b3275371bc9280e84be5ad43d` (origin/main)
- Branch: `feature/pe-ops-github-agent-production-02-rebuild-github-agent-worktree`
- Implementer: `infra-impl-b`
- Validator: `infra-val-a`
- Thread: `1509269471875829860`

## Scope
1. Verify current baseline: origin/main, no active PE, `bin/gh-agent` confirmed on main (PR #459).
2. Produce a safe worktree rebuild plan (evidence in HANDOFF.md §Rebuild Plan).
3. Quarantine/backup the existing standalone clone — **only after PO approval of the rebuild plan**.
4. Recreate `/opt/elis/agent-worktrees/github-agent` as a linked worktree from `/opt/elis/repo` on `main`.
5. Set/verify Git identity in worktree: `elis-git-bot <elis-git-bot@electoralintegrity.org>`.
6. Set/verify ownership and ACL model: `elis-github:elis-github`.
7. Verify `.git` is a linked worktree pointer (file), not a standalone `.git` directory.
8. Commit PE evidence artefacts proving the binding to `.elis/pe/PE-OPS-GITHUB-AGENT-PRODUCTION-02/`.

## Out of scope (unless separately approved)
- No OpenClaw config edit
- No `enabled: true` change
- No OpenClaw reload/restart
- No sudoers rule creation
- No live GitHub API call
- No token generation test
- No GitHub Agent dispatch
- No GitHub push/PR/merge by GitHub Agent
- No secrets/private-key inspection
- No changes to `/opt/elis/secrets/*`

## Acceptance criteria

| AC | Criterion |
|----|-----------|
| AC-1 | `/opt/elis/agent-worktrees/github-agent/.git` is a **file** (worktree pointer), not a directory. |
| AC-2 | Linked worktree is registered in `/opt/elis/repo/.git/worktrees/github-agent/` (or canonical equivalent). |
| AC-3 | `git -C /opt/elis/agent-worktrees/github-agent rev-parse --abbrev-ref HEAD` returns `main`. |
| AC-4 | `git -C /opt/elis/agent-worktrees/github-agent config user.name` returns `elis-git-bot`. |
| AC-5 | `git -C /opt/elis/agent-worktrees/github-agent config user.email` returns `elis-git-bot@electoralintegrity.org`. |
| AC-6 | Ownership: `stat -c '%U:%G' /opt/elis/agent-worktrees/github-agent` returns `elis-github:elis-github`. |
| AC-7 | Old standalone clone is quarantined/renamed before removal (backup path recorded in evidence). |
| AC-8 | Evidence artefacts committed to `.elis/pe/PE-OPS-GITHUB-AGENT-PRODUCTION-02/` on the implementation branch. |
| AC-9 | Validator (`infra-val-a`) independently confirms AC-1 through AC-8 with PASS verdict in `REVIEW.md`. |

## Implementation boundaries
- Write path: repository files only within the approved file scope (opening phase)
- No worktree mutation until PO explicitly approves the rebuild plan
- No credential creation, copying, or inspection
- No secret printing
- No auth profile edits
- No service restart/reload
- No OpenClaw/Hermes runtime config change
- No GitHub push, PR, or merge

## First-pass file scope (opening phase — PM action on main)
- `CURRENT_PE.md`
- `.elis/pe/PE-OPS-GITHUB-AGENT-PRODUCTION-02/PE_TASK.md`
- `.elis/pe/PE-OPS-GITHUB-AGENT-PRODUCTION-02/HANDOFF.md`

## Approved implementation file scope (post-opening, unlocked by PO rebuild-plan approval)
- `/opt/elis/agent-worktrees/github-agent` (worktree rebuild — destructive; PO approval required)
- `.elis/pe/PE-OPS-GITHUB-AGENT-PRODUCTION-02/EVIDENCE.md` (implementer evidence artefact)
- `.elis/pe/PE-OPS-GITHUB-AGENT-PRODUCTION-02/REVIEW.md` (validator-owned)

## Validation approach
- Validator (`infra-val-a`) runs independently from `infra-val-a` worktree
- Validator confirms each AC in `REVIEW.md` with pass/fail verdict and evidence
- Gate 1: PM reviews implementation evidence; Gate 2: PO approves after validator PASS

## Risks

| Risk | Mitigation |
|------|-----------|
| Standalone clone removal is destructive | Quarantine/rename to `github-agent.standalone-backup.<timestamp>` before `git worktree add`; PO approval required per step |
| Linked worktree add may fail if canonical repo is on a different branch | Canonical repo checked out to `main` before `git worktree add` |
| Ownership reset may require `sudo` | `elis-github` user context or `sudo chown` with appropriate sudo rule; PM must not use sudo directly |

## Rollback / safety notes
- Old standalone clone preserved as `github-agent.standalone-backup.<timestamp>` until PO confirms linked worktree is healthy
- All repository changes on feature branch are reversible via `git revert` or branch abandonment
- No service or runtime state is modified during opening phase; rollback requires no service action
- If any hard stop is violated, PM halts and notifies PO before any further action

## Hard stops
- No worktree mutation until PO explicitly approves the rebuild plan
- No credential creation, copying, or inspection
- No secret printing or reading from `/opt/elis/secrets/*`
- No service restart/reload
- No OpenClaw/Hermes runtime config change
- No GitHub push
- No PR creation
- No merge
- No implementation dispatch until PO approval
- No validator dispatch until implementation complete and PM gate passed
- No `sessions_spawn` or `sessions_send`
