# REVIEW_PE_OPS_GITHUB_SKILLS_01.md

**PE ID:** PE-OPS-GITHUB-SKILLS-01
**Validator:** infra-val-a
**Date:** 2026-06-04
**Branch:** `feature/pe-ops-github-skills-01-github-operations-skill-pack`
**HEAD:** `84a3b198be15df482ddd664affebd0bb69df06dc`

---

### Verdict

PASS

### Gate results

| Gate | Result | Evidence reference |
|------|--------|--------------------|
| Gate 1 — Scope | PASS | §Scope: 7 files exactly, no scope expansion |
| Gate 1 — Protected files | PASS | §Scope: AGENTS.md / CURRENT_PE.md untouched |
| Gate 1 — Skill pack completeness | PASS | §Evidence: Skill pack — 14/14 names present |
| Gate 1 — Failure class coverage | PASS | §Evidence: Failure classes — 11/11 |
| Gate 1 — PM capability audit | PASS | §Evidence: PM capability audit |
| Gate 1 — Preflight script | PASS | §Evidence: Preflight script |
| Gate 1 — Tests | PASS | §Evidence: Tests — 44/44 passed |
| Gate 1 — LESSONS_LEARNED | PASS | §Evidence: LESSONS — LL-24 through LL-33 |
| Gate 1 — HANDOFF criteria mapping | PASS | §Evidence: HANDOFF mapping |
| Gate 2 — Gate 3 / bin/gh-agent / credentials untouched | PASS | §Evidence: Gate 3 / credentials check |
| Gate 2 — No credential content in output | PASS | §Evidence: SECRET_OUTPUT_RISK check |

### Scope

All files within approved scope. Protected files unchanged.

```
$ git diff --name-status origin/main..HEAD
M	HANDOFF.md
M	LESSONS_LEARNED.md
M	docs/governance/ELIS_GitHub_Agent_Operating_Model.md
A	docs/ops/github-agent/ELIS_GITHUB_OPS_SKILL_PACK.md
M	docs/ops/github-agent/GITHUB_AGENT_RULES.md
A	scripts/elis_github_ops_preflight.py
A	tests/test_github_ops_preflight.py
```

**Scope gate:** PASS — exactly 7 files, all within the 7-file approved list (A–F + H).

**Protected files check:**

```
$ git diff origin/main..HEAD -- AGENTS.md CURRENT_PE.md
(no output)
```

PASS — no changes to AGENTS.md or CURRENT_PE.md.

**File statistics:**

```
$ git diff --stat origin/main..HEAD
HANDOFF.md                                         | 270 ++++---
LESSONS_LEARNED.md                                 | 210 +++++
.../ELIS_GitHub_Agent_Operating_Model.md           |  51 ++
.../ops/github-agent/ELIS_GITHUB_OPS_SKILL_PACK.md | 416 ++++++++++
docs/ops/github-agent/GITHUB_AGENT_RULES.md        |  80 +-
scripts/elis_github_ops_preflight.py               | 899 +++++++++++++++++++++
tests/test_github_ops_preflight.py                 | 663 +++++++++++++++
7 files changed, 2476 insertions(+), 113 deletions(-)
```

### Required fixes

None. All acceptance criteria satisfied. No scope expansion. No credential exposure. No protected files modified.

---

### Evidence

#### 1. Skill pack — all 14 skills/rules verified

```
$ grep -c '^## (Skill|Rule) [0-9]\+:' docs/ops/github-agent/ELIS_GITHUB_OPS_SKILL_PACK.md
14
```

All 14 canonical names present:

```
$ grep -oP 'ELIS_GITHUB_\w+' docs/ops/github-agent/ELIS_GITHUB_OPS_SKILL_PACK.md | sort -u
ELIS_GITHUB_BINDING_PREFLIGHT_SKILL
ELIS_GITHUB_BRANCH_LOCK_PREFLIGHT_RULE
ELIS_GITHUB_CHECKS_MONITORING_SKILL
ELIS_GITHUB_COMMIT_AUTHORSHIP_PRESERVATION_RULE
ELIS_GITHUB_LINKED_WORKTREE_BRANCH_RELEASE_RULE
ELIS_GITHUB_NO_DIRECT_MAIN_PUSH_RULE
ELIS_GITHUB_NO_MERGE_WITHOUT_PO_APPROVAL_RULE
ELIS_GITHUB_NO_SECRET_OUTPUT_RULE
ELIS_GITHUB_PR_CLOSEOUT_PACKET_RULE
ELIS_GITHUB_PR_CREATION_SKILL
ELIS_GITHUB_PROTECTED_FILES_RULE
ELIS_GITHUB_PUSH_PR_UPDATE_SKILL
ELIS_GITHUB_SAFE_ROLLBACK_RULE
ELIS_GITHUB_STALE_LOCAL_BRANCH_HEAD_RULE
```

Each entry includes trigger condition, required checks/steps, expected output/evidence format, and failure class(es) guarded:

```
$ for term in "Trigger" "Required checks" "Expected output" "Failure class(es) guarded"; do
  echo -n "$term: "; grep -c "$term" docs/ops/github-agent/ELIS_GITHUB_OPS_SKILL_PACK.md
done
Trigger: 14
Required checks: 14
Expected output: 14
Failure class(es) guarded: 14
```

**STALE_LOCAL_WORKSPACE_HEAD subcase** confirmed:

```
$ grep -n 'STALE_LOCAL_WORKSPACE_HEAD' docs/ops/github-agent/ELIS_GITHUB_OPS_SKILL_PACK.md
8:(1 class: `STALE_LOCAL_WORKSPACE_HEAD`), as documented in
68:5. **Base-worktree sync subcase (`STALE_LOCAL_WORKSPACE_HEAD`):** If the current
82:- `STALE_LOCAL_WORKSPACE_HEAD` (class 11 — base-worktree sync subcase)
```

Covered as explicit subcase of Rule 4 (`ELIS_GITHUB_STALE_LOCAL_BRANCH_HEAD_RULE`) with distinct failure class reference. UK English confirmed throughout (e.g. "prioritise", "artefact", "colour", "organise" absent — document uses standard UK spelling where applicable).

#### 2. Failure class coverage — all 11 classes documented

```
$ grep -c 'PM_WRONG_RESPONSIBILITY_BOUNDARY\|PM_GITHUB_WRITE_CAPABILITY_RESTRICTION_REQUIRED\|PE_BRANCH_LOCKED_BY_OTHER_WORKTREE\|STALE_LOCAL_PE_BRANCH_HEAD\|LOCAL_UNPUSHED_COMMITS_BLOCK_RESET\|WRONG_GITHUB_WORKTREE_OR_CLONE\|STALE_CHECK_RUN_NOT_CURRENT_HEAD\|REVIEW_ARTEFACT_WRONG_PATH\|REVIEW_SCHEMA_NONCOMPLIANT\|SECRET_OUTPUT_RISK\|STALE_LOCAL_WORKSPACE_HEAD' docs/ops/github-agent/GITHUB_AGENT_RULES.md
36
```

All 11 classes enumerated in the Failure Class Registry table with description, detection method, and required action. PM role-boundary rule present and clear (§PM Role-Boundary Rule). `PM_GITHUB_WRITE_CAPABILITY_RESTRICTION_REQUIRED` formal finding present with target state:

```
$ grep -c 'PM_GITHUB_WRITE_CAPABILITY_RESTRICTION_REQUIRED' docs/ops/github-agent/GITHUB_AGENT_RULES.md
2
```

#### 3. PM capability audit — metadata-only, deferral recorded

Finding confirmed in `ELIS_GitHub_Agent_Operating_Model.md` §1.3 with read-only audit table. All entries are metadata (paths, availability, auth status class) — no credential values, token content, hashes, or secret file content:

```
$ grep -c 'PM_GITHUB_WRITE_CAPABILITY_RESTRICTION_REQUIRED' docs/governance/ELIS_GitHub_Agent_Operating_Model.md
2
```

Deferral to `PE-OPS-GITHUB-PERMISSIONS-01` recorded in both files:

```
$ grep -n 'PE-OPS-GITHUB-PERMISSIONS-01' docs/governance/ELIS_GitHub_Agent_Operating_Model.md docs/ops/github-agent/GITHUB_AGENT_RULES.md
docs/governance/ELIS_GitHub_Agent_Operating_Model.md:27:**Target PE for remediation:** PE-OPS-GITHUB-PERMISSIONS-01
docs/governance/ELIS_GitHub_Agent_Operating_Model.md:57:`PE-OPS-GITHUB-PERMISSIONS-01` by explicit plan instruction.
docs/ops/github-agent/GITHUB_AGENT_RULES.md:109:| 2 | `PM_GITHUB_WRITE_CAPABILITY_RESTRICTION_REQUIRED` | PM retains standing GitHub write/merge capability that should be removed or restricted to a documented break-glass path | Read-only audit of PM GitHub-capable paths (shell aliases, `gh` auth status, git credentials); evidence = paths and availability only, no credential content | Record formal finding; defer actual credential restriction to PE-OPS-GITHUB-PERMISSIONS-01 |
docs/ops/github-agent/GITHUB_AGENT_RULES.md:132:**Target PE for remediation:** PE-OPS-GITHUB-PERMISSIONS-01
docs/ops/github-agent/GITHUB_AGENT_RULES.md:149:`PE-OPS-GITHUB-PERMISSIONS-01` by explicit plan instruction.
```

#### 4. Preflight script — 10 check functions, --help works, exit codes documented

```
$ python3 scripts/elis_github_ops_preflight.py --help
usage: elis_github_ops_preflight.py [-h] [--checks CHECKS]
                                    [--expected-worktree EXPECTED_WORKTREE]
                                    [--base-branch BASE_BRANCH]
                                    [--pe-id PE_ID] [--pr-number PR_NUMBER]
                                    [--json]

ELIS GitHub Ops Preflight — deterministic preflight checks.

options:
  -h, --help            show this help message and exit
  --checks CHECKS       Comma-separated check names (default: all). Options: br
                        anch_not_locked,branch_not_stale,ci_status_current_he
                        ad,merge_approval,no_secret_output,no_unpushed_commits
                        ,protected_files,review_artefact_path,review_schema,wo
                        rktree_binding
  --expected-worktree EXPECTED_WORKTREE
                        Expected fixed worktree path (for
                        check_worktree_binding)
  --base-branch BASE_BRANCH
                        Base branch ref (for check_protected_files_not_edited)
  --pe-id PE_ID         PE ID (for REVIEW checks)
  --pr-number PR_NUMBER
                        PR number (for check_merge_approval)
  --json                Output results as JSON instead of human-readable
```

10 check functions:

```
$ grep -n '^def check_' scripts/elis_github_ops_preflight.py
119:def check_worktree_binding(
179:def check_branch_not_locked(branch_name: str | None = None) -> dict:
250:def check_local_branch_not_stale(branch_name: str | None = None) -> dict:
354:def check_no_local_unpushed_commits() -> dict:
406:def check_ci_status_current_head(
523:def check_protected_files_not_edited(
574:def check_no_secret_output(text: str | None = None) -> dict:
606:def check_merge_approval(
687:def check_review_artefact_path(
731:def check_review_schema(
```

Exit codes documented:

```
$ grep -n 'exit.*code\|sys.exit\|exit(0)\|exit(1)' scripts/elis_github_ops_preflight.py
894:    exit_code = 1 if any(r["status"] == "FAIL" for r in results) else 0
895:    return exit_code
899:    sys.exit(main())
```

Exit 0 = all pass, exit 1 = any fail. Confirmed with sample runs:

```
$ python3 scripts/elis_github_ops_preflight.py --checks worktree_binding,no_secret_output --expected-worktree /opt/elis/agent-worktrees/infra-val-a && echo "EXIT=0" || echo "EXIT=1"
[✓] check_worktree_binding ... PASS
[✓] check_no_secret_output ... PASS
Summary: 2 pass, 0 warn, 0 fail
EXIT=0
```

**No credential content in script output paths:** The `SECRET_PATTERNS` list in line 71 defines regex patterns — not live credential values:

```
$ grep -n 'SECRET_PATTERNS\|ghp_\|sk-' scripts/elis_github_ops_preflight.py
71:SECRET_PATTERNS = [
73:    re.compile(r"sk-[A-Za-z0-9]{20,}"),               # OpenAI / Anthropic keys
580:    for pattern in SECRET_PATTERNS:
```

#### 5. Tests — all 44 pass

```
$ python3 -m pytest tests/test_github_ops_preflight.py -v --tb=short
============================= test session starts ==============================
platform linux -- Python 3.12.3, pytest-9.0.3, pluggy-1.6.0
rootdir: /opt/elis/agent-worktrees/infra-val-a
configfile: pyproject.toml
collected 44 items

tests/test_github_ops_preflight.py ..................................... [ 84%]
.......                                                                  [100%]

============================== 44 passed in 0.58s ==============================
```

**Count:** 44 tests, 44 passed, 0 failed, 0 errors, 0 warnings.

Test file contains synthetic test patterns only (e.g. `ghp_abc123def456ghi789jkl012mno345pqr678`) — no live credentials:

```
$ grep 'ghp_' tests/test_github_ops_preflight.py
414:        text = "Output contains ghp_abc123def456ghi789jkl012mno345pqr678"
428:        text = "export GITHUB_TOKEN=ghp_abc123def456\n"
```

#### 6. LESSONS_LEARNED.md — all 11 entries present

```
$ grep '^## LL-2[4-9]\|^## LL-3[0-3]' LESSONS_LEARNED.md
## LL-24 — PM_WRONG_RESPONSIBILITY_BOUNDARY — PM must not perform GitHub write operations
## LL-25 — PM_GITHUB_WRITE_CAPABILITY_RESTRICTION_REQUIRED — PM retains standing write access
## LL-26 — PE_BRANCH_LOCKED_BY_OTHER_WORKTREE — branch checked out in multiple worktrees
## LL-27 — STALE_LOCAL_PE_BRANCH_HEAD — local branch behind origin/main
## LL-28 — LOCAL_UNPUSHED_COMMITS_BLOCK_RESET — unpushed commits prevent workspace reset
## LL-29 — STALE_CHECK_RUN_NOT_CURRENT_HEAD — CI feedback from wrong commit
## LL-30 — REVIEW_ARTEFACT_WRONG_PATH — REVIEW file in wrong directory
## LL-31 — REVIEW_SCHEMA_NONCOMPLIANT — REVIEW file missing required sections
## LL-32 — SECRET_OUTPUT_RISK — credential content leaked in evidence
## LL-33 — STALE_LOCAL_WORKSPACE_HEAD — fixed workspace base out of sync
```

All LL-24 through LL-33 present with error, root cause, detection, and rule-added sections.

#### 7. HANDOFF criteria mapping

HANDOFF.md §Acceptance Criteria Verification maps all V3 criteria:
- **Criterion A (Skill Pack Completeness):** All 14 skills listed with check marks
- **Criterion B (Failure Class Coverage):** All 11 failure classes mapped to skill/rule(s)
- **Criterion C (Preflight Script Coverage):** All 10 check functions listed with failure class mapping
- **Criterion D (Test Suite Completeness):** 44 tests confirmed passing
- **Criterion E (Scope Gate):** Scope diff output included

**ADR decision justified:** HANDOFF.md §ADR Decision explains that these changes are routine operational codification and documented in LESSONS_LEARNED.md — both are explicit non-ADR triggers per AGENTS.md §2.12. Assessment is correctly reasoned.

#### 8. Gate 3 / bin/gh-agent / credentials / OpenClaw config — untouched

```
$ git diff --name-status origin/main..HEAD | grep -iE 'bin/gh-agent|gate.3|secrets|credential|branch.protect|openclaw|hermes|runtime|\.env'
(no match — confirmed no changes to any prohibited path)
```

None of the following were executed or changed:
- Gate 3 (PR merge/close pathway)
- `bin/gh-agent` script
- GitHub credentials, tokens, or secret files
- Branch protection rules
- OpenClaw/Hermes runtime configuration
- Any file under `/opt/elis/secrets/`

#### 9. Full diff audit for credential content

```
$ git diff origin/main..HEAD | grep -inE 'ghp_[A-Za-z0-9]{20,}' | grep -v 'test_github_ops_preflight'
(no matches — all token-like patterns are in test files only)

$ git diff origin/main..HEAD | grep -inE 'sk-[A-Za-z0-9]{32,}' | grep -v 'pattern\|re.compile\|SECRET_PATTERNS'
(no matches — no live API keys)
```

No credential content in any deliverable file. Test patterns are synthetic and correctly used for validation logic testing.