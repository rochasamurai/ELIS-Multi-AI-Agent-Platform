# Agent Development Guide (AGENTS.md)

This file defines the **two‑agent development workflow** for **ELIS SLR Agent — Release Plan v2.0**.
It is mandatory for all **PEs** targeting the `<base-branch>` line.

**Agent roles**
- **Implementer** (default slot: `a`, e.g. `infra-impl-a`)
- **Validator** (default slot: `b`, e.g. `infra-val-b`)

> Legacy engine labels **CODEX** and **Claude Code** are no longer the current role identifiers.
> Use agent IDs from `CURRENT_PE.md` (e.g. `infra-impl-b`, `infra-val-a`).
> Engine/slot mapping is recorded in §14.2 for CI compatibility only — it must not appear in PE proposals.

> Role assignment is structural, not advisory.
> Every agent reads `CURRENT_PE.md` at repo root as Step 0 to determine its role for the current PE.
> If `CURRENT_PE.md` is absent or the agent's name is not listed, the agent must stop immediately and notify PM.
> The PM edits and commits `CURRENT_PE.md` to `<base-branch>` before any PE begins.
> The PM retains full override authority by editing `CURRENT_PE.md` at any time.

---

## 0) Glossary (quick)

- **PE**: Planned Execution step in `<plan-file>` (e.g., PE0a, PE1a, PE2…)
- **PM**: Project Manager — orchestrates PE assignments, authorises Validator start, approves merges, and receives all Status Packets.
- **Implementer**: writes/changes product code + PE handoff documentation
- **Validator**: verifies acceptance criteria, adds adversarial tests, issues verdict in `REVIEW_PE<N>.md`
- **Status Packet**: the standard evidence bundle required in every agent update to the PM (Section 6)
- **Worktree**: a separate working directory for a branch (prevents checkout conflicts and cross‑PE contamination)
- **Scope gate**: running `git diff --name-status origin/<base-branch>..HEAD` before every commit to verify no unrelated files crept in

---

## 1) Canonical references (read first)

Before starting any work on a PE, every agent MUST read:

0. `CURRENT_PE.md` (authoritative role assignment for the active PE)
1. `CURRENT_PE.md` → read `Plan file` to locate the authoritative plan for this release.
   Example path format: `<plan-location>/<plan-file>`
2. `AGENTS.md` (this file — workflow rules)
3. `LESSONS_LEARNED.md` (running log of error patterns — apply rules listed there before proceeding)
4. `AUDITS.md` (audit expectations)
5. On the PE branch: `HANDOFF.md` (Implementer) **or** `REVIEW_PE<N>.md` (Validator)

---

## 2) Operating rules (hard requirements)

### 2.1 One PE = one branch = one PR
- Every PE is implemented on its own feature branch created from the base branch
  declared in `CURRENT_PE.md` → `Base branch` field.
- The PR base is that same branch unless the release plan explicitly states otherwise.
- Never mix changes from different PEs on the same branch. If `git diff` shows unrelated files, **stop and split**.

### 2.2 Clean working tree before any context switch
- **Never switch branches with a dirty tree.**
- Before `git checkout`, `git rebase`, or `git stash`: run `git status -sb`.
- If output shows `M` or `??`, clean up first:
  - commit on the correct branch **or**
  - move changes to a dedicated WIP branch **or**
  - stash (temporary only — unstash immediately on the correct branch).

### 2.3 File ownership
- **Implementer owns:** all PE code, `HANDOFF.md`, non-test deliverables declared in the PE.
- **Validator owns:** `REVIEW_PE<N>.md`, adversarial tests, minimal scope‑safe fixes **only if strictly required** to satisfy acceptance criteria.
- Neither agent modifies files owned by the other without explicit instructions from the PM.

### 2.4 Evidence‑first reporting (no "trust me")
- Every agent update to the PM MUST include the **Status Packet** (Section 6).
- If a claim is not supported by pasted command output or GitHub Actions check evidence, it is not considered done.
- Within a session, each step in the agent's task list must be confirmed with pasted
  command output before marking it complete. A step marked done without output evidence
  is a workflow violation.
- For portable blocking gates (`black`, `ruff`, lint/validation, and `pytest`), the
  authoritative pass/fail source is GitHub Actions CI. Local runs on `elis-server`
  are supported as preflight checks for fast feedback, but they do not override CI.

### 2.4.1 REVIEW file evidence requirement (hard)
- Every `REVIEW_PE<N>.md` file MUST contain a `### Evidence` section with at least one
  fenced code block showing actual command output or file content. A verdict without
  inline evidence is invalid and will be rejected by Gate 2b.
- The Validator MUST complete all verification steps before writing the `### Verdict`
  line. Verdict-before-evidence is a workflow violation regardless of the final verdict
  value.

### 2.5 Atomic session boundaries — commit before ending
- **Before ending a work session, `git status -sb` must show a clean tree.**
- If files remain uncommitted, commit them on the correct branch with a descriptive message before stopping.
- Never leave implementation files as untracked `??` across a session boundary.
- Stashing across sessions is prohibited; use a WIP commit instead (`git commit -m "wip: ..."`).

### 2.6 Rebase after every `<base-branch>` merge
- After any PR is merged to `<base-branch>`, every active feature branch **must be rebased** before continuing:
  ```bash
  # BASE=$(grep "Base branch" CURRENT_PE.md | awk '{print $NF}')
  git fetch origin
  git rebase origin/$BASE
  ```
- Check drift: `git merge-base origin/$BASE HEAD` — if this returns the tip of `origin/$BASE`, the branch is current.

### 2.7 HANDOFF.md committed before PR is opened
- `HANDOFF.md` is an Implementer deliverable and must be committed on the feature branch **before** `git push` and PR creation.
- Opening a PR without a committed `HANDOFF.md` is a workflow violation. The PR must arrive complete in one push.

### 2.8 Validator does not self-start
- The Validator **waits for explicit PM authorisation** before beginning validation.
- The PM assigns the Validator after receiving the Implementer's Status Packet (§5.1 step 9).
- Assignment may be issued as a short PR comment (for example: `@<validator-agent-id> — assigned as Validator for <PE-ID>. Begin review.`).
- A Validator who starts without PM assignment is out of role.

### 2.9 Mid-session context checkpoint
Before every `git commit`, the active agent must:
1. Re-read `CURRENT_PE.md` → locate `Plan file` → re-read the PE acceptance criteria in that file.
2. Re-read `CURRENT_PE.md` to confirm its role has not changed.
3. Run the scope gate: `git diff --name-status origin/$BASE..HEAD` (`BASE` from `CURRENT_PE.md`).
4. Confirm no unrelated files appear in the diff.
5. Run: `python scripts/check_agent_scope.py`
   If exit code is 1 → stop, close any secret-pattern files, notify PM.
Only then proceed with the commit.

### 2.10 Autonomous gate operation
Gate 1 and Gate 2 are enforced by CI automation after PE-INFRA-04.

**Gate 1 (Validator assignment):**
- Default path: PM dispatches the validator assignment directly via the
  PM-owned OpenClaw CLI direct-agent path (`openclaw agent --agent <validator-id>`)
  after Status Packet and gate checks.
- Documentation: `docs/openclaw/workspace-pm/AGENTS.md` §4 Gate 1.
- `sessions_send` is no longer the primary dispatch mechanism and must not be
  used as the default path.
- Fallback: If PM-owned direct dispatch is unavailable, the validator-assignment
  PR comment path (machine tag `<!-- validator-assignment -->`) triggers
  `validator-dispatch.yml`. This requires the GitHub Actions self-hosted runner
  to be installed and governed — it is not currently active on elis-server.
  PO relay is a last-resort fallback only; it must not replace PM-owned direct
  dispatch as the normal path.
- Supervisor is exception/escalation only, not the routine dispatcher.
  PM must not route routine validator dispatch through Supervisor.
  Escalate to Supervisor only for platform runtime defects.

**Gate 2 (merge):**
- CI reads the REVIEW file verdict after every push to a feature branch.
- On PASS + CI green + no `pm-review-required` label → CI merges automatically.
- On FAIL → CI posts the fix assignment comment to the Implementer.
- A comment-only PASS signal does not satisfy required-review branch
  protection; a formal GitHub approval review from the mapped reviewer
  identity is mandatory.
- PM retains full veto authority by adding the `pm-review-required` label
  to any PR at any time.

**PM escalation triggers (unchanged — always require PM):**
- Scope disputes between agents
- More than two FAIL/fix iterations (audit trigger, §7)
- Any release merge (feature branch → base branch is automated;
  base branch → main always requires PM)
- Agent role rotation
- Any CI job that exits with the `pm-escalation` flag

### 2.10.1 Workflow state machine contract

Every PE moves through the canonical workflow state machine. The human-readable
contract is `docs/workflow/PE_STATE_MACHINE.md`; the machine-readable mirror is
`elis/workflow_state_machine.py`.

Canonical states:

| State | Meaning |
|-------|---------|
| `planning` | PE is defined, but no implementer work has started yet. |
| `implementing` | Implementer is actively coding on `elis-server`. |
| `gate-1-pending` | Implementer has finished; `HANDOFF.md` and Status Packet evidence are complete; ready for validator assignment. |
| `validating` | Validator is actively reviewing on `elis-server`. |
| `gate-2-pending` | Validator has posted evidence and verdict; awaiting formal approval or merge automation. |
| `merged` | PR merged; PE complete. |
| `blocked` | A guard failed, a runner is unavailable, or an external dependency prevents progress. |
| `superseded` | PE was replaced by a newer governance decision. |

Allowed transitions:

```text
planning -> implementing
implementing -> gate-1-pending
gate-1-pending -> validating
gate-1-pending -> blocked
validating -> gate-2-pending
gate-2-pending -> merged
gate-2-pending -> blocked
any active state -> superseded
```

Transition guards:

- Implementer completion (`implementing -> gate-1-pending`) requires `HANDOFF.md` is present and complete, Status Packet sections are complete, handoff artefacts are committed on the PE branch, and the runner observes a matching PE/branch pair.
- Validator authorisation (`gate-1-pending -> validating`) requires explicit PM authorisation is recorded, validator assignment evidence is present, and the PE remains active in `CURRENT_PE.md`.
- Review completion (`validating -> gate-2-pending`) requires REVIEW evidence is present, a formal verdict is recorded in the REVIEW file, and CI gates are not broken by validator artefacts.
- Merge approval (`gate-2-pending -> merged`) requires CI is green, required review approval is satisfied, and no `pm-review-required` veto label is present.

GitHub Actions may observe state, validate guards, post audit evidence, and
dispatch bounded workflow steps. GitHub Actions must not perform agent coding
unless the current state explicitly permits that action and the active
execution-surface policy allows it.

GitHub Actions is the control plane, not the development-agent coding substrate.
Implementer and Validator coding sessions run on the local-first `elis-server`
execution surface; GitHub-hosted workflows remain bounded to CI, guard
validation, dispatch, comments/statuses, merge automation, and audit evidence.
If complete implementer evidence is already present on the PR branch while
`CURRENT_PE.md` still records `implementing`, the dispatcher may observe
`implementing -> gate-1-pending` and then dispatch through
`gate-1-pending -> validating` in one bounded control-plane step.

### 2.11 Language standard
- All repository-facing content must use **UK English** by default.
- This applies to:
  - file contents committed to the repository
  - commit messages
  - Pull Request titles, bodies, and review comments
  - `HANDOFF.md`, `REVIEW_PE<N>.md`, audit reports, runbooks, and plan files
- Exceptions are allowed only when:
  - quoting user-provided text verbatim
  - preserving the official name of an external document, product, or source
  - the PM explicitly authorises a different language for a specific artefact
- Agents must normalise spelling and wording to UK English when drafting or editing repository-facing content unless one of the exceptions above applies.

### 2.12 Architecture Decision Records (ADRs)

An ADR (`docs/decisions/ADR-NNN-title.md`) **must** be created when:

- a structural choice is made that affects how PEs, agents, branches, or CI
  interact (e.g., worktree strategy, role alternation, merge policy)
- a previously-trialled approach is discarded in favour of a different one
  (e.g., rejecting symlinks for HANDOFF, rejecting Docker for native runtime)
- a new cross-cutting capability is introduced to the workflow
  (e.g., parallel tracks, session continuity model, ADR system itself)
- a retrospective reveals a significant undocumented design choice that has
  driven subsequent decisions

An ADR is **not** required for:

- routine PE implementation choices (file layout, variable names, test structure)
- temporary fixes or workarounds expected to be revisited within one PE
- changes fully documented in `LESSONS_LEARNED.md` that do not affect workflow
  structure

When in doubt: if the decision would be surprising or non-obvious to a new
agent reading the codebase, write an ADR.

ADR format and lifecycle are defined in `docs/decisions/README.md`.

---

## 3) Worktree lifecycle — mandatory for every PE

### 3.1 Why fixed workspaces
Fixed workspaces (persistent worktrees per role slot) prevent:
- checkout failures ("local changes would be overwritten"),
- branch contamination (PE1 edits leaking into PE2),
- agent collisions on shared files (e.g., `HANDOFF.md` / `REVIEW_PE<N>.md`),
- stale worktree accumulation (no per-PE worktree lifecycle),
- agent path confusion (each agent always knows its own fixed path).

### 3.2 When to use
Fixed workspaces are **required for every PE**. Each agent role slot has a persistent worktree:
```
/opt/elis/agent-worktrees/<role>-<slot>
```
Examples: `/opt/elis/agent-worktrees/infra-impl-b`, `/opt/elis/agent-worktrees/infra-val-a`

The main repo folder always stays on `main`. The branch checked out in each fixed workspace changes per PE; the worktree path does not.

### 3.3 Fixed workspace lifecycle
**At PE start: reset the fixed workspace to a clean state and check out the PE branch.**
After PE merge: the workspace is not removed (it is persistent). The branch is left in place until the next PE assignment, when it will be reset again.

### 3.4 Reset procedure (start of each PE)
From the fixed workspace root:

```bash
# PE START — reset fixed workspace for new PE assignment
git fetch --all --prune
git checkout <pe-branch> 2>/dev/null || git checkout -b <pe-branch> origin/$BASE
git rebase origin/$BASE 2>/dev/null || true
git status -sb  # confirm clean
```

If switching away from a previous PE branch that still has uncommitted work:
```bash
git stash  # or git reset --hard if state is disposable
git checkout <new-pe-branch>
```

### 3.4a Wrong-worktree quarantine and no-copy rules
If an agent detects it is operating from the wrong worktree:
1. Stop all file operations immediately.
2. Do not copy, move, or commit any files from the wrong worktree.
3. Report the mismatch to PM with full evidence (`pwd`, `git rev-parse --show-toplevel`, assigned path from CURRENT_PE.md).
4. PM resets the correct fixed workspace and re-dispatches.
5. Any artefacts produced from the wrong worktree are invalid.

**No-copy rule:** Agents must never copy or transfer files between worktrees. If a file from one worktree is needed in another, commit it to the canonical repo from the correct worktree, then fetch in the target worktree.

### 3.4b Fixed Workspace Binding Certificate
Before any PE work begins, the agent must produce a **Fixed Workspace Binding Certificate** from within the fixed workspace. This certificate is mandatory evidence in the opening Status Packet (§6). See `docs/governance/ELIS_PE_Operating_Protocol.md §5.1b` for the full specification.

### 3.4c Persistent vs disposable file separation
Fixed workspaces contain **disposable repo/task state** (source code, HANDOFF, REVIEW, `.elis/` PE workspace). **Persistent agent runtime/context files** (AGENTS.md, SKILLS.md, SOUL.md, tool manifests, OpenClaw/Hermes bootstrap files) must reside outside the fixed worktree.
- Do not write persistent runtime files into the fixed worktree.
- If a persistent file accidentally lands in the worktree, move it out before the worktree is reset for the next PE.
- When resetting a fixed workspace for a new PE, only disposable repo/task state is cleaned. Persistent runtime files are never modified during reset.

### 3.5 Commands
```bash
# Verify fixed workspace identity
echo "Fixed workspace: $(pwd)"
git worktree list | grep "$(pwd)"
```

---

## 4) Branch naming and PR conventions

### 4.1 Branch naming
Use one of:
- `feature/pe<id>-<short-scope>` (e.g., `feature/pe4-dedup`)
- `hotfix/pe<id>-<short-scope>` for post-merge corrective fixes
- `chore/<topic>` for non‑PE housekeeping (only if authorised by PM)

### 4.2 PR title format
- `feat(pe4): deterministic dedup + clusters (elis dedup)`
- `fix(pe6): archive validate_json.py + fix elis-validate.yml trigger`
- `chore(audit): Validator workflow audit report`

### 4.3 PR creation
```bash
# BASE=$(grep "Base branch" CURRENT_PE.md | awk '{print $NF}')
gh pr create --base $BASE --head <branch> --title "feat(pe<N>): ..." --body "$(cat <<'EOF'
## Summary
...
## Test plan
...
EOF
)"
```

---

## 5) PE lifecycle (step-by-step)

### 5.1 Implementer workflow

1. **Preflight — before any work begins:**
   - Read all canonical references (Section 1).
   - Confirm your role assignment for this PE with the PM.
   - **Produce the Fixed Workspace Binding Certificate** from inside the fixed workspace:
     ```bash
     echo "PE ID: $(grep 'PE ID' CURRENT_PE.md | head -1)"
     echo "Agent ID: <agent-surface-name>"
     echo "Fixed workspace: $(pwd)"
     echo "Git root: $(git rev-parse --show-toplevel)"
     echo "Branch: $(git branch --show-current)"
     echo "HEAD: $(git rev-parse HEAD)"
     echo "Base commit: $(git rev-parse origin/$BASE)"
     echo "Clean status: $(git status --short --untracked-files=all)"
     echo "Allowed files: <from PE_TASK.md>"
     echo "Timestamp: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
     echo "Result: PASS"
     ```
   - Paste the opening Status Packet (including the binding certificate) to the PM. No work starts before the PM acknowledges.
2. Rebase onto current `<base-branch>`:
   ```bash
   # BASE=$(grep "Base branch" CURRENT_PE.md | awk '{print $NF}')
   git fetch origin
   git rebase origin/$BASE   # on any existing branch, or:
   git checkout -b feature/pe<N>-<scope> origin/$BASE
   ```
3. Implement **only** the PE acceptance criteria (no unrelated changes).
3a. **After your first implementation commit — open a draft PR immediately:**
    ```bash
    # BASE=$(grep "Base branch" CURRENT_PE.md | awk '{print $NF}')
    git push -u origin <branch>
    gh pr create --draft \
      --head <branch> --base $BASE \
      --title "WIP: feat(<pe-id>): <description>" \
      --body "Draft — implementation in progress. Status Packet will be added in final HANDOFF commit."
    ```
    The draft PR creates a shared audit trail. PM and Validator can see commit-by-commit
    progress without waiting for implementation to finish.
4. **Pre-commit scope gate** (run before every `git commit`):
   ```bash
   # BASE=$(grep "Base branch" CURRENT_PE.md | awk '{print $NF}')
   git diff --name-status origin/$BASE..HEAD
   # Verify: only PE-scope files appear. If unrelated files show, stop and split.
   ```
5. Run quality gates:
   ```bash
   python -m black --check .
   python -m ruff check .
   python -m pytest tests/<pe-specific>.py -v
   ```
   For portable blocking gates, treat these local runs as preflight on `elis-server`.
   GitHub Actions remains the authoritative merge gate.
6. **Post milestone PR comments** on the draft PR at each significant step:
   - After implementation commit: `"feat commit <sha> — <brief summary of what changed>"`
   - After quality gates pass: `"Quality gates green — black/ruff clean, pytest N passed"`
   - After HANDOFF committed: `"HANDOFF committed — converting to ready for Validator"`
7. Update `HANDOFF.md` with:
   - summary
   - complete changed-file list
   - design decisions
   - acceptance criteria checklist (PASS/FAIL for each)
   - exact validation commands and their output (pasted verbatim — not paraphrased), or
     the corresponding GitHub Actions check names / run links for portable blocking gates
8. **Session-end check**: `git status -sb` must be clean before any push.
9. Commit `HANDOFF.md` as the **last commit** on the branch (§2.7), then convert draft to ready:
   ```bash
   gh pr ready <PR_NUMBER>
   ```
10. Deliver Status Packet to PM + explicitly ask PM to assign the Validator.
    - Preferred channel: include/refresh the Status Packet in the PR body or PR comment.

> **PM gate:** PM receives Status Packet, reviews it, and explicitly assigns the Validator.
> Validator does not start without this assignment.

#### Progress Tracking (MANDATORY)

At the start of every PE implementation, the Implementer must create and maintain a Todo list
for the full execution sequence.

| Checkpoint | When | All items |
|---|---|---|
| Initial Todos | Before any work begins | `[ ]` pending |
| Updated Todos | After each step completes | `[x]` done · `[→]` active · `[ ]` pending |
| Final Todos | Before delivering Status Packet | `[x]` all completed |

Rules:
- Exactly one step may be `[→]` at any time.
- Completed steps must be marked `[x]` immediately, with pasted command output confirming the step.
- If a step fails and is retried, keep it `[→]` until verification passes.

**GitHub write boundary reminder for Implementer:**
- Do NOT push, create PRs, or merge. These are PM/GitHub Agent operations.
- Local commits only. PM receives Status Packet and handles remote writes.
- If PM instructs push, verify the instruction came from PM explicitly. Never auto-push.

**Tool note (both agents):** use the `TodoWrite` tool to maintain this list. Set status to
`in_progress` before starting each step; set `completed` immediately after the step is
verified with pasted output. Never batch completions.

---

### 5.2 Validator workflow

1. **Wait for PM assignment.** Do not begin without explicit PM authorisation (§2.8).
   - Preferred assignment signal: PM PR comment on the active PR.
2. **Refuse if Status Packet is missing.** Notify PM and wait for a complete packet.
3. Read `HANDOFF.md` and verify scope:
   ```bash
   # BASE=$(grep "Base branch" CURRENT_PE.md | awk '{print $NF}')
   git diff --name-status origin/$BASE..HEAD
   ```
   Output must match the files declared in `HANDOFF.md`. Any mismatch is a blocking finding.
4. Validate each acceptance criterion **verbatim** from `<plan-file>`. No substitutions.
   For each AC, write and run a targeted spot-check command and paste the output verbatim
   in `REVIEW_PE<N>.md` under the relevant AC entry:
   ```bash
   # Example: exercise a function directly
   python -c "
   from scripts.module import fn
   result = fn(test_inputs)
   assert 'expected' in result
   print(result)
   print('AC-N PASS')
   "
   ```
5. Add adversarial tests covering:
   - schema rejection cases (missing fields, wrong types, boundary values)
   - determinism / idempotence
   - invalid inputs / edge cases specific to the PE
6. Run full quality gates (Section 6.3).
   Local runs on `elis-server` remain useful for preflight and targeted debugging, but
   CI is the authoritative pass/fail source for portable blocking gates.
7. Write verdict in `REVIEW_PE<N>.md` using the standard format (Section 9).
8. **Before committing the REVIEW file**, verify it passes the local check:
   ```bash
   REVIEW_FILE=docs/reviews/archive/REVIEW_PE<N>.md python scripts/check_review.py
   ```
   Required sections: `### Verdict`, `### Gate results`, `### Scope`, `### Required fixes`, `### Evidence` (must contain a fenced code block). Do not push a REVIEW file that fails this check.
9. If any newly discovered pre-existing defect is not already in §11, add it now.
10. Push validation commits to the **same branch** (validator-owned files only: `REVIEW_PE<N>.md` + adversarial tests).
11. Deliver verdict + Status Packet using a **GitHub PR review comment** (`approve` for PASS, `request-changes` for FAIL) using the standard format (Section 9).
    - Single-account fallback: if reviewer and PR author are the same GitHub account, and GitHub blocks review actions, post verdicts as plain PR comments. For FAIL, explicitly request PM attention and apply `pm-review-required`.
    - For PASS, plain PR comments are not sufficient on protected branches with required reviews; PASS requires a formal approval review from the mapped reviewer identity.
    - PM may still receive a direct summary message, but the PR review is the binding live handshake record.
    - `REVIEW_PE<N>.md` remains mandatory as the durable on-branch artifact.

> **PM gate:** PM receives verdict. If PASS → PM merges. If FAIL → PM assigns Implementer to fix (§5.3).

#### Progress Tracking (MANDATORY)

At the start of every PR validation, the Validator must create and maintain a Todo list
for the full validation sequence.

| Checkpoint | When | All items |
|---|---|---|
| Initial Todos | Before fetching/reviewing PR | `[ ]` pending |
| Updated Todos | After each validation step | `[x]` done · `[→]` active · `[ ]` pending |
| Final Todos | After `REVIEW_PE<N>.md` is committed to branch | `[x]` all completed |

Rules:
- Exactly one step may be `[→]` at any time.
- Completed steps must be marked `[x]` immediately, with pasted command output confirming the step.
- In re-validation rounds, restart Updated Todos from step 1 and include round ID.

**GitHub write boundary reminder for Validator:**
- Do NOT push, create PRs, or merge. These are PM/GitHub Agent operations.
- Validator local commits are limited to REVIEW file + adversarial tests.
- PR comments and formal GitHub reviews are authorised when explicitly assigned by PM.
- Never push implementation file changes.

**Tool note (both agents):** use the `TodoWrite` tool to maintain this list. Set status to
`in_progress` before starting each step; set `completed` immediately after the step is
verified with pasted output. Never batch completions.

---

### 5.3 Iteration loop (FAIL → fix → re-validate)

When the Validator issues a FAIL verdict:

**Implementer:**
1. Read `REVIEW_PE<N>.md` on the same branch.
2. Implement only the "Required fixes (blocking)" items — no scope creep.
3. Re-run scope gate and quality gates (§5.1 steps 4–5).
4. Update `HANDOFF.md`: mark fixed criteria PASS, paste new gate outputs.
5. Commit to the same branch (do not open a new PR).
6. Deliver updated Status Packet to PM + ask PM to re-assign the Validator.
   - Preferred channel: reply in PR thread with fix summary + commit SHA and request re-review.

> **PM gate:** PM receives updated Status Packet, reviews it, and re-assigns the Validator.

**Validator:**
1. Re-read `REVIEW_PE<N>.md` and `HANDOFF.md` to confirm fixes address all blocking findings.
2. Re-run full quality gates.
3. Update `REVIEW_PE<N>.md` with a new dated verdict section (do not overwrite prior findings).
4. Push to same branch and post an updated PR review/comment verdict + Status Packet.

Repeat until verdict is PASS. If more than two iterations occur, the PM may call an audit (§7).

---

## 6) Status Packet (mandatory in every agent update)

Paste command outputs exactly (no paraphrase). Run from the relevant worktree.
For portable blocking gates, GitHub Actions check names and run links are valid primary
evidence. Local `elis-server` command output remains valid for preflight, targeted
spot-checks, and environment-specific diagnostics.

### 6.1 Working‑tree state (catches uncommitted work)
```bash
git status -sb
git diff --name-status
git diff --stat
```
> This is distinct from the committed-diff check below. Both are required.

### 6.2 Repository state
```bash
git fetch --all --prune
git branch --show-current
git rev-parse HEAD
git log -5 --oneline --decorate
```

### 6.3 Scope evidence (against `origin/<base-branch>`)
```bash
# BASE=$(grep "Base branch" CURRENT_PE.md | awk '{print $NF}')
# The fixed workspace path MUST be the correct role+slot path:
echo "Fixed workspace: $(pwd)"
git rev-parse --show-toplevel
git diff --name-status origin/$BASE..HEAD
git diff --stat        origin/$BASE..HEAD
```

### 6.4 Quality gates
```bash
python -m black --check .
python -m ruff check .
python -m pytest -q
```
> Include PE-specific test count alongside full-suite count.
> For portable blocking gates, cite the corresponding GitHub Actions results as the
> authoritative merge evidence. Local runs on `elis-server` are the preferred preflight
> environment for maintainers and agents, but they are advisory for merge authority.

### 6.5 PR evidence (if applicable)
```bash
# BASE=$(grep "Base branch" CURRENT_PE.md | awk '{print $NF}')
# GitHub write boundary: implementer/validator run gh read-only commands only.
# Push, PR creation, merge are PM or GitHub Agent operations.
gh pr list --state open --base $BASE   # read-only — allowed for all roles
git log -1 --oneline                    # confirm current commit
```

### 6.6 GitHub write boundary checklist (pre-remote-write gate)
```bash
# Verify role is authorised for remote write
echo "Role: $(grep -i 'agent.*role' AGENTS.md 2>/dev/null || echo 'unknown')"
# If role is implementer or validator: DO NOT PUSH. Notify PM instead.
# Check CURRENT_PE.md for the authorised GitHub write operator:
grep 'github.*write\|GitHub.*operator\|push.*authorised' CURRENT_PE.md 2>/dev/null
```

---

## 7) Audit feature (AUDITS.md)

### 7.1 When audits run
Triggered by the PM when:
- repeated checkout conflicts occur,
- PR scope contamination is detected,
- agent role boundaries are breached,
- more than two FAIL/fix iterations occur on a single PE,
- or at major milestones.

### 7.2 What audits produce
Each agent writes a report in `reports/audits/` and submits it via a dedicated PR:

- `reports/audits/Audit_Report_Codex.md`
- `reports/audits/Audit_Report_Claude.md`

See `AUDITS.md` for the full audit spec and report templates.

---

## 8) Do‑not list

- Do not switch branches with local edits in the same folder (use worktrees).
- Do not leave a worktree open after its PR is merged — remove it immediately (§3.3).
- Do not start a PE without creating a dedicated worktree for its branch (§3.3).
- Do not refactor unrelated code while inside a PE.
- Do not touch `REVIEW_PE<N>.md` unless you are the Validator.
- Do not push a `REVIEW_PE<N>.md` without first running `REVIEW_FILE=docs/reviews/archive/<file> python scripts/check_review.py` and confirming it exits 0 (§5.2 step 8).
- Do not declare PASS without pasted gate outputs.
- Do not leave uncommitted implementation files when ending a session.
- Do not open a PR without running the pre-commit scope gate first.
- Do not open a final (ready) PR before `HANDOFF.md` is committed on the branch (§2.7).
- Do not convert a draft PR to ready before HANDOFF is the last commit on the branch.
- Do not mark a task-list step as completed without pasting the verification output first.
- Do not start on a PE without rebasing onto the current `origin/$BASE` (`BASE` from `CURRENT_PE.md`).
- Do not self-start as Validator without explicit PM assignment (§2.8).
- Do not paraphrase command output — paste it verbatim in the Status Packet.
- Do not commit without completing the mid-session context checkpoint (§2.9).
- Do not start any PE without reading `CURRENT_PE.md` first (Step 0).
- Do not open, read, or reference any file listed in `.agentignore`.
- Do not include secret values in Status Packets, HANDOFF.md, or any PR content.
- Do not proceed if `check_agent_scope.py` returns exit code 1.
- **Do NOT push, PR, or merge** as implementer, validator, or supervisor. Remote GitHub writes are GitHub Agent operations only, executed after explicit PM/PO approval.
- **PM must NOT write to GitHub directly.** PM coordinates and approves; only the GitHub Agent executes GitHub write operations.
- **Do NOT work outside your fixed workspace.** Verify `pwd` matches your role's assigned path before any operation. If the path is wrong, quarantine (stop all operations, do not copy files) and report to PM.
- **Do NOT copy or transfer files between worktrees.** Use the canonical repo as the intermediary via commit+fetch from the correct worktree.
- **Do NOT proceed without a PASS result on the Fixed Workspace Binding Certificate.**

---

## 9) Standard verdict and PM update format

Every agent update to the PM — whether an interim progress report or a final verdict — must use this format.

```
## Agent update — <AGENT_NAME> / <PE_ID> / <date>

### Verdict
PASS / FAIL / IN PROGRESS

### Branch / PR
Branch: feature/pe<N>-<scope>
PR: #NNN (open / merged)
Base: <base-branch-from-CURRENT_PE.md>

### Gate results
black: PASS / FAIL
ruff:  PASS / FAIL
pytest: N passed, M failed (M pre-existing — not this PE)
PE-specific tests: N/N passed

### Scope (diff vs <base-branch-from-CURRENT_PE.md>)
<paste git diff --name-status output>

### Required fixes (if FAIL)
- <minimal description of each blocking finding>

### Ready to merge
YES / NO — reason if NO

### Next
[who does what] → [next PE / action]
```

## Agent update — PM / PE-OC-20 / 2026-02-24

### Verdict
PASS — operational follow-up complete

### Branch / PR
Branch: main  
PR: #283 (merged)  
Base: main

### Gate results
black: PASS (already recorded)  
ruff: PASS  
pytest: PASS — 556 passed, 0 failed (17 warnings about `datetime.utcnow` remaining)

### Scope (diff vs main)
M	openclaw/openclaw.json  
M	docker-compose.yml

### Summary of post-merge ops
- Added `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, and `OPENCLAW_GATEWAY_TOKEN` to `~/.openclaw/.env` (host-only secret storage, not committed).  
- Ran `bash scripts/deploy_openclaw_workspaces.sh`, then `docker compose down && docker compose up -d`, to copy the sanitized config into `/app/.openclaw/openclaw.json`.  
- Verified with `python scripts/check_openclaw_config_sync.py` that all 13 declared agents are live and the container no longer rejects the schema.

### Ready to merge
N/A — already merged and this documents the operational handoff.

### Next
PM / Implementer → keep `~/.openclaw/.env` secrets protected and, once PE-OC-21 is assigned, follow the standard implementer/validator workflow with a fresh worktree, Status Packet, HANDOFF, and REVIEW.

---

## 10) Per-PE REVIEW files

Validation verdicts are written to **per-PE files** rather than a single overwritten `REVIEW.md`:

- File: `REVIEW_PE<N>.md` (e.g., `REVIEW_PE4.md`, `REVIEW_PE5.md`)
- Location: `docs/reviews/archive/`
- Owned by: Validator
- Written once per PE; never overwritten by a subsequent PE
- On re-validation after a FAIL, **append** a new dated section — do not overwrite prior findings.
- Live handshake channel: PR review comments are used for PASS/FAIL signalling and fix/re-review loops.
- Durable artifact rule: PR comments do **not** replace `REVIEW_PE<N>.md`; the file must still be committed.

The review index lives at `docs/reviews/README.md` and points to the most recent validation for quick reference.

---

## 11) Known defects register

Pre-existing issues that are tracked but do not block current PEs:

| Defect | File | Introduced | Blocking? | Owner |
|--------|------|-----------|-----------|-------|
| `datetime.utcnow()` deprecation warnings | `elis/pipeline/screen.py` | Pre-v2.0 | No | TBD |

**Rule:** Any new PE that touches `elis/cli.py` must update `tests/test_cli.py` to stay current.
Any Validator who finds a new pre-existing defect not in this table must add it here (§5.2 step 8).

---

## 12) Enforcement mechanisms

Text instructions alone cannot guarantee compliance. The following structural controls enforce the workflow without relying on agent discipline.

### 12.1 Tier 1 — Automated (cannot be bypassed)

**Branch protection on the base branch declared in `CURRENT_PE.md`** _(configure in GitHub → Settings → Branches)_:
- All CI status checks must pass before merge is allowed.
- At least 1 approving review (PM) required.
- Comment-only PASS signalling does not satisfy required-review branch protection.
- Direct pushes blocked — PRs only.

**Currently active CI checks** (`.github/workflows/ci.yml`):
- `python -m black --check .` — formatting gate.
- `python -m ruff check .` — lint gate.
- `python -m pytest -q` — full test suite.
- These GitHub Actions jobs are the authoritative execution surface for portable
  blocking gates on protected branches.

**Planned CI checks** _(not yet implemented — add to `ci.yml`)_:
- HANDOFF.md presence and section check: verify that `HANDOFF.md` contains required
  headers (`## Summary`, `## Files Changed`, `## Acceptance Criteria`, `## Validation Commands`)
  before merge is allowed.

**Planned: pre-commit hooks** (`.pre-commit-config.yaml`) _(not yet implemented)_:
- Run black, ruff, and pytest on every local `git commit`.
- Prevents "fix later" drift between commits and the final push.
- Local execution is still recommended on `elis-server` as a preflight environment,
  but merge authority remains with GitHub Actions CI.

### 12.2 Tier 2 — Structural prompting (reduces drift)

**PR template** (`.github/pull_request_template.md`) — _active_:
Every PR opens with a pre-filled Status Packet skeleton. The PM can verify at a glance
whether all required fields are present before authorising merge.

**`CLAUDE.md` for Claude Code** _(planned — not yet implemented)_:
Critical workflow rules — "update HANDOFF.md before opening PR", "Status Packet mandatory
before any work", "wait for PM assignment before validating" — duplicated in `CLAUDE.md`,
which is always loaded into Claude Code's system prompt and survives context compression.

**`HANDOFF.md` fill-in template** _(planned — not yet implemented)_:
A template file (`docs/templates/HANDOFF_template.md`) with all required sections
pre-populated. Implementers copy it rather than writing from memory.

### 12.3 Tier 3 — Human checkpoints

**PM gates (two explicit decision points per PE):**
1. **Before Validator starts** — PM receives Implementer Status Packet and explicitly assigns Validator (preferred: PR comment assignment).
2. **Before merge** — PM receives Validator verdict and Status Packet (preferred: PR review comment + `REVIEW_PE<N>.md`). Merge only on explicit GO.

**Audit trigger** (§7): Any workflow deviation observed by any party triggers an audit report.
The record creates accountability and a pattern log across PEs.

### 12.4 Single-account GitHub constraint runbook

When the repository operates with a single GitHub identity for both agents, GitHub may block
`gh pr review --request-changes` on self-authored PRs. The operational fallback and migration
paths are documented in:

- `docs/_active/GITHUB_SINGLE_ACCOUNT_VALIDATION_RUNBOOK.md`

That runbook is normative for this constraint and must be used together with §5.2.

---

## 13) Secrets isolation policy

### 13.1 What agents must never access
Both CODEX and Claude Code are prohibited from reading, referencing,
printing, logging, or including in any prompt or output:
- Any file matching patterns in `.agentignore`
- Any environment variable containing a credential, token, or key
- Any value that appears to be a secret (matches patterns: sk-*, ghp_*, xox*, etc.)

### 13.2 Structural controls
- `.gitignore` excludes all secret-pattern files from version control.
- `.agentignore` documents forbidden paths explicitly for agent reference.
- `.env.example` is the only committed env file — contains placeholders only.
- `scripts/check_agent_scope.py` runs in CI on every PR.
- IDE context (CODEX Agent mode, Claude Code extension) automatically
  includes open files — agents must not open secret-pattern files in the editor.

### 13.3 Agent responsibility
At Step 0 of every session, each agent reads `.agentignore` and confirms
that none of the listed files are open in the editor or included in context.
If a secret-pattern file is detected in context, the agent must:
1. Close the file immediately.
2. Notify the PM.
3. Not proceed until the PM confirms the exposure is contained.

### 13.4 What to do if a secret is accidentally exposed
- Do not include the value in any further output.
- Notify PM immediately with the file name only (not the value).
- PM rotates the exposed credential before the session continues.
- PM adds the incident to the defects register (§11) with status Blocking.

---

## 14) Role-Based Agent Surface Normalisation

### 14.1 Terminology

- **Workflow surface name** (also *agentId*): the compound identifier used in
  `CURRENT_PE.md` registry columns `Implementer-agentId` and
  `Validator-agentId`, e.g. `infra-impl-a`. It encodes both the
  *role* and the *slot* assigned to run it.
- **Role name**: the provider-neutral part of the surface name, obtained by
  stripping the slot suffix. The role name defines *what* the agent does;
  the slot registry records *who* runs it at a given PE.
- **Slot suffix**: the provider-neutral token appended after the final hyphen:
  `a`, `b`, or `c`.

### 14.2 Canonical surface-to-role mapping

| Workflow surface name | Role name    | Domain        | Responsibility          |
|-----------------------|--------------|---------------|-------------------------|
| `infra-impl-a`        | `infra-impl` | Infrastructure | Implementer             |
| `infra-impl-b`        | `infra-impl` | Infrastructure | Implementer             |
| `infra-val-a`         | `infra-val`  | Infrastructure | Validator               |
| `infra-val-b`         | `infra-val`  | Infrastructure | Validator               |
| `prog-impl-a`         | `prog-impl`  | Programme      | Implementer             |
| `prog-impl-b`         | `prog-impl`  | Programme      | Implementer             |
| `prog-val-a`          | `prog-val`   | Programme      | Validator               |
| `prog-val-b`          | `prog-val`   | Programme      | Validator               |
| `slr-impl-a`          | `slr-impl`   | SLR            | Implementer             |
| `slr-impl-b`          | `slr-impl`   | SLR            | Implementer             |
| `slr-val-a`           | `slr-val`    | SLR            | Validator               |
| `slr-val-b`           | `slr-val`    | SLR            | Validator               |

Current slot registry (legacy compatibility reference — CI use only):

> The labels below are accepted by `check_current_pe.py` for backward compatibility with
> historical registry rows. They must **not** appear in PE opening proposals or PM reports.
> Use agent IDs (e.g. `infra-impl-a`, `infra-val-b`) in all operational documents.

- slot `a` → engine: `codex` (legacy label: `CODEX` / `slot-a`) — **do not use in proposals**
- slot `b` → engine: `claude` (legacy label: `Claude Code` / `slot-b`) — **do not use in proposals**
- slot `c` → guest or overflow engine (for example Gemini) when explicitly authorised

Legacy model-coupled IDs remain accepted only through the committed migration
map in `config/agent_id_migration_map.json`.

One-off or guest surfaces (e.g. `gemini-cli`) do not follow this convention.
They are explicitly noted in the relevant PE row and are not subject to the
alternation rule.

### 14.3 Deriving a role name from a surface name

The derivation rule is:

1. Split the surface name on `-`.
2. Drop the last token (the slot suffix).
3. Re-join the remaining tokens with `-`.

Example: `infra-val-a` → tokens `["infra", "val", "a"]`
→ drop `"a"` → join → `"infra-val"`.

This rule is implemented in `elis/role_surface.py` and validated by
`tests/test_pe_infra_slr_01.py`.

### 14.4 Governance rules

- Acceptance criteria, HANDOFF files, and REVIEW files **must** use the full
  surface name (e.g. `infra-impl-a`) to record which slot ran the
  role, while referring to the agent's responsibility by its role name
  (e.g. "the `infra-impl` role").
- The alternation rule (§2.1) applies to *roles*, not engines.  If
  `infra-impl-a` implemented PE-N, then `infra-impl-b` must
  implement PE-N+1, regardless of which engine is active.
- Tooling that parses `CURRENT_PE.md` must accept canonical `<role>-<slot>`
  names and may accept legacy model-coupled IDs only through the explicit
  compatibility path.
- New surface names require PM authorisation and a corresponding row in the
  mapping table above.

---

End of AGENTS.md
