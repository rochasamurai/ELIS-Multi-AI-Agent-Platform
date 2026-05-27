# HANDOFF — PE-OPS-GITHUB-AGENT-PRODUCTION-02

## Summary
Replace the invalid standalone clone at `/opt/elis/agent-worktrees/github-agent` with a proper linked worktree from `/opt/elis/repo`. This PE is Phase 2 of the GitHub Agent production series (PE-OPS-GITHUB-AGENT-PRODUCTION-01 was Phase 1 — `bin/gh-agent` launcher, merged PR #459).

## Phase status (2026-05-27)

| Phase | Description | Status |
|-------|-------------|--------|
| Phase 1 | `bin/gh-agent` GitHub App launcher | MERGED — PR #459, SHA `9a2b31a` |
| Phase 2 | Linked worktree rebuild (this PE) | OPEN — pending PO rebuild-plan approval |
| Phase 4 | Sudoers rule for `elis-github` wrapper | PENDING — requires separate PO approval |
| Phase 5 | Validation and OpenClaw enablement | PENDING — requires separate PO approval |

## Baseline (PE open)
- `origin/main` HEAD: `83d18db4b892709b3275371bc9280e84be5ad43d`
- PM worktree: `/opt/elis/agent-worktrees/pm` — clean, branch `main`
- Canonical repo: `/opt/elis/repo`
- github-agent current state: `/opt/elis/agent-worktrees/github-agent/.git` is a **directory** (standalone clone), branch `chore/github-agent-evidence-closeout`

## Rebuild Plan (Phase 2)

> **GATE: No worktree mutation until PO explicitly approves this plan.**

### Step 1 — Pre-flight checks
```bash
# Confirm PM worktree is clean
git -C /opt/elis/agent-worktrees/pm status --short

# Confirm canonical repo HEAD
git -C /opt/elis/repo rev-parse HEAD
git -C /opt/elis/repo rev-parse --abbrev-ref HEAD

# Confirm github-agent is standalone (not already a linked worktree)
file /opt/elis/agent-worktrees/github-agent/.git
# Expected: /opt/elis/agent-worktrees/github-agent/.git: directory

# Confirm no processes are running from github-agent directory
lsof +D /opt/elis/agent-worktrees/github-agent 2>/dev/null | head -5
```

### Step 2 — Quarantine standalone clone (PO approval required before execution)
```bash
TIMESTAMP=$(date -u +%Y%m%dT%H%M%S)
BACKUP_PATH="/opt/elis/agent-worktrees/github-agent.standalone-backup.${TIMESTAMP}"

# Rename standalone clone to quarantine path
mv /opt/elis/agent-worktrees/github-agent "${BACKUP_PATH}"
echo "Standalone clone quarantined to: ${BACKUP_PATH}"
```

### Step 3 — Ensure canonical repo is on main
```bash
git -C /opt/elis/repo fetch origin main
git -C /opt/elis/repo checkout main
git -C /opt/elis/repo pull --ff-only origin main
```

### Step 4 — Create linked worktree
```bash
git -C /opt/elis/repo worktree add \
  /opt/elis/agent-worktrees/github-agent \
  main
```

### Step 5 — Set Git identity
```bash
git -C /opt/elis/agent-worktrees/github-agent \
  config user.name "elis-git-bot"
git -C /opt/elis/agent-worktrees/github-agent \
  config user.email "elis-git-bot@electoralintegrity.org"
```

### Step 6 — Set/verify ownership
```bash
sudo chown -R elis-github:elis-github \
  /opt/elis/agent-worktrees/github-agent
```
> Note: requires `samurai` sudo permission for `chown` on this path; if not present, escalate to PO.

### Step 7 — Verify linked worktree binding
```bash
# .git must be a FILE (pointer), not a directory
file /opt/elis/agent-worktrees/github-agent/.git
# Expected: .../github-agent/.git: ASCII text

# Worktree registered in canonical repo
git -C /opt/elis/repo worktree list
# Expected: /opt/elis/agent-worktrees/github-agent  <SHA>  [main]

# HEAD matches main
git -C /opt/elis/agent-worktrees/github-agent rev-parse --abbrev-ref HEAD
# Expected: main

# Git identity set
git -C /opt/elis/agent-worktrees/github-agent config user.name
git -C /opt/elis/agent-worktrees/github-agent config user.email

# Ownership
stat -c '%U:%G' /opt/elis/agent-worktrees/github-agent
# Expected: elis-github:elis-github
```

### Step 8 — Commit evidence artefacts
Implementer commits evidence to `.elis/pe/PE-OPS-GITHUB-AGENT-PRODUCTION-02/EVIDENCE.md` on the implementation branch.

### Step 9 — Validator confirmation
Validator (`infra-val-a`) independently runs verification from its own worktree and commits PASS/FAIL verdict to `REVIEW.md`.

## Known constraints
- Ownership change (`chown`) likely requires `sudo`. If `samurai` lacks the required rule, PM escalates to PO before proceeding.
- Canonical repo (`/opt/elis/repo`) is currently on branch `feature/pe-ops-dispatch-wrapper-hardening-02-controlled-pm-dispatch-acceptance`. Step 3 must switch it to `main` before `git worktree add`.
- Old standalone backup is preserved until PO confirms the linked worktree is healthy; deletion requires separate PO confirmation.

## Active hard stops
- No worktree mutation until PO explicitly approves this rebuild plan
- No credential creation or copying
- No secret printing or reading from `/opt/elis/secrets/*`
- No OpenClaw config edit
- No service restart/reload
- No GitHub push/PR/merge
- No validator dispatch without PM gate passage
- If any hard stop is violated, PM halts and notifies PO

## Status packet
- Base: `origin/main` @ `83d18db4b892709b3275371bc9280e84be5ad43d`
- Implementation branch: `feature/pe-ops-github-agent-production-02-rebuild-github-agent-worktree`
- Implementer: `infra-impl-b`
- Validator: `infra-val-a`
- PM role: coordination only
- Thread: `1509269471875829860`
- PM worktree: `/opt/elis/agent-worktrees/pm`
