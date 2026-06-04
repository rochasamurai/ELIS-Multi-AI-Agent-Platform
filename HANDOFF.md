# HANDOFF.md — PE-OPS-GITHUB-SKILLS-01

**PE ID:** PE-OPS-GITHUB-SKILLS-01
**Branch:** `feature/pe-ops-github-skills-01-github-operations-skill-pack`
**Implementer:** infra-impl-b
**Date:** 2026-06-04
**Status:** Ready for Validator (infra-val-a)

---

## Summary of Files Changed

| File | Change | Rationale |
|------|--------|-----------|
| `docs/ops/github-agent/ELIS_GITHUB_OPS_SKILL_PACK.md` | **NEW** | 14 skills/rules for deterministic GitHub operations enforcement — the centrepiece deliverable |
| `docs/ops/github-agent/GITHUB_AGENT_RULES.md` | **EXTEND** | Added failure class registry (11-class table), PM_GITHUB_WRITE_CAPABILITY formal finding, PM role-boundary rule |
| `docs/governance/ELIS_GitHub_Agent_Operating_Model.md` | **EXTEND** | Added §1.2 deterministic enforcement reference (skill pack), §1.3 PM write-cap finding with read-only audit table, updated cross-references and version history |
| `scripts/elis_github_ops_preflight.py` | **NEW** | 10 deterministic preflight check functions + unified CLI entry point, 8 direct check functions covering all 11 failure classes |
| `tests/test_github_ops_preflight.py` | **NEW** | 44 pytest tests covering all 11 failure classes plus edge cases |
| `LESSONS_LEARNED.md` | **EXTEND** | Added LL-24 through LL-33 — one entry per failure class with detection, prevention, and skill pack reference |
| `HANDOFF.md` | **NEW** | This file — final commit |

Total: 3 new files, 3 extended files, 1 new (this) = 7 files in scope. All within approved scope — no scope expansion.

---

## Acceptance Criteria Verification

### V3 Criterion A: Skill Pack Completeness
All 14 skills/rules defined in `docs/ops/github-agent/ELIS_GITHUB_OPS_SKILL_PACK.md`:
1. ✅ ELIS_GITHUB_BINDING_PREFLIGHT_SKILL
2. ✅ ELIS_GITHUB_BRANCH_LOCK_PREFLIGHT_RULE
3. ✅ ELIS_GITHUB_LINKED_WORKTREE_BRANCH_RELEASE_RULE
4. ✅ ELIS_GITHUB_STALE_LOCAL_BRANCH_HEAD_RULE (includes STALE_LOCAL_WORKSPACE_HEAD subcase)
5. ✅ ELIS_GITHUB_PUSH_PR_UPDATE_SKILL
6. ✅ ELIS_GITHUB_PR_CREATION_SKILL
7. ✅ ELIS_GITHUB_CHECKS_MONITORING_SKILL
8. ✅ ELIS_GITHUB_PROTECTED_FILES_RULE
9. ✅ ELIS_GITHUB_NO_SECRET_OUTPUT_RULE
10. ✅ ELIS_GITHUB_NO_DIRECT_MAIN_PUSH_RULE
11. ✅ ELIS_GITHUB_NO_MERGE_WITHOUT_PO_APPROVAL_RULE
12. ✅ ELIS_GITHUB_COMMIT_AUTHORSHIP_PRESERVATION_RULE
13. ✅ ELIS_GITHUB_SAFE_ROLLBACK_RULE
14. ✅ ELIS_GITHUB_PR_CLOSEOUT_PACKET_RULE

### V3 Criterion B: Failure Class Coverage
All 11 failure classes addressed by at least one skill/rule:
- **PM_WRONG_RESPONSIBILITY_BOUNDARY** → Rule 8, Rule 10
- **PM_GITHUB_WRITE_CAPABILITY_RESTRICTION_REQUIRED** → Rule 11, Rule 13
- **PE_BRANCH_LOCKED_BY_OTHER_WORKTREE** → Rule 2, Rule 3
- **STALE_LOCAL_PE_BRANCH_HEAD** → Rule 4
- **LOCAL_UNPUSHED_COMMITS_BLOCK_RESET** → Rule 5
- **WRONG_GITHUB_WORKTREE_OR_CLONE** → Skill 1
- **STALE_CHECK_RUN_NOT_CURRENT_HEAD** → Rule 6, Rule 7
- **REVIEW_ARTEFACT_WRONG_PATH** → Rule 14
- **REVIEW_SCHEMA_NONCOMPLIANT** → Rule 14
- **SECRET_OUTPUT_RISK** → Rule 9
- **STALE_LOCAL_WORKSPACE_HEAD** → Rule 4 (base-worktree sync subcase)

### V3 Criterion C: Preflight Script Coverage
`scripts/elis_github_ops_preflight.py` implements 10 check functions:
1. `check_worktree_binding` → WRONG_GITHUB_WORKTREE_OR_CLONE
2. `check_branch_not_locked` → PE_BRANCH_LOCKED_BY_OTHER_WORKTREE
3. `check_local_branch_not_stale` → STALE_LOCAL_PE_BRANCH_HEAD + STALE_LOCAL_WORKSPACE_HEAD
4. `check_no_local_unpushed_commits` → LOCAL_UNPUSHED_COMMITS_BLOCK_RESET
5. `check_ci_status_current_head` → STALE_CHECK_RUN_NOT_CURRENT_HEAD
6. `check_protected_files_not_edited` → PM_WRONG_RESPONSIBILITY_BOUNDARY
7. `check_no_secret_output` → SECRET_OUTPUT_RISK
8. `check_merge_approval` → PM_GITHUB_WRITE_CAPABILITY_RESTRICTION_REQUIRED
9. `check_review_artefact_path` → REVIEW_ARTEFACT_WRONG_PATH
10. `check_review_schema` → REVIEW_SCHEMA_NONCOMPLIANT

All functions return structured dicts with check, class, status, detail keys. CLI prints PASS/FAIL per check; exit code 0 = all pass, 1 = any fail. JSON output mode available (`--json`).

### V3 Criterion D: Test Suite Completeness
44 tests pass across all 11 failure classes (pytest output below):
```
tests/test_github_ops_preflight.py ..................................... [ 84%]
.......                                                                  [100%]
============================== 44 passed in 0.51s ==============================
```

### V3 Criterion E: Scope Gate
```
$ git diff --name-status origin/main..HEAD
M       LESSONS_LEARNED.md
M       docs/governance/ELIS_GitHub_Agent_Operating_Model.md
M       docs/ops/github-agent/GITHUB_AGENT_RULES.md
A       docs/ops/github-agent/ELIS_GITHUB_OPS_SKILL_PACK.md
A       scripts/elis_github_ops_preflight.py
A       tests/test_github_ops_preflight.py
A       HANDOFF.md
```

All 7 files are within the approved scope (A-F + H). No files outside the approved list were touched. No protected files were edited (CURRENT_PE.md, AGENTS.md governance sections were not modified).

---

## 11 Failure Classes Addressed

| # | Class Name | Skill Pack Rule(s) | Preflight Check | LL Entry |
|---|------------|-------------------|-----------------|----------|
| 1 | PM_WRONG_RESPONSIBILITY_BOUNDARY | Rule 8, Rule 10 | `check_protected_files_not_edited` | LL-24 |
| 2 | PM_GITHUB_WRITE_CAPABILITY_RESTRICTION_REQUIRED | Rule 11, Rule 13 | `check_merge_approval` | LL-25 |
| 3 | PE_BRANCH_LOCKED_BY_OTHER_WORKTREE | Rule 2, Rule 3 | `check_branch_not_locked` | LL-26 |
| 4 | STALE_LOCAL_PE_BRANCH_HEAD | Rule 4 | `check_local_branch_not_stale` | LL-27 |
| 5 | LOCAL_UNPUSHED_COMMITS_BLOCK_RESET | Rule 5 | `check_no_local_unpushed_commits` | LL-28 |
| 6 | WRONG_GITHUB_WORKTREE_OR_CLONE | Skill 1 | `check_worktree_binding` | LL-29 (via related) |
| 7 | STALE_CHECK_RUN_NOT_CURRENT_HEAD | Rule 6, Rule 7 | `check_ci_status_current_head` | LL-29 |
| 8 | REVIEW_ARTEFACT_WRONG_PATH | Rule 14 | `check_review_artefact_path` | LL-30 |
| 9 | REVIEW_SCHEMA_NONCOMPLIANT | Rule 14 | `check_review_schema` | LL-31 |
| 10 | SECRET_OUTPUT_RISK | Rule 9 | `check_no_secret_output` | LL-32 |
| 11 | STALE_LOCAL_WORKSPACE_HEAD | Rule 4 (subcase) | `check_local_branch_not_stale` (detached) | LL-33 |

---

## ADR Decision

**No ADR created.** Assessment per AGENTS.md §2.12:

- The governance changes in this PE codify operational rules and failure classes as a skill pack, failure class registry, and preflight checks. They do not change:
  - Workflow structure (branch model, alternation, PE lifecycle)
  - Merge policy or Gate 2 automation
  - Agent role definitions or alternation rules
  - Any cross-cutting architectural decision
- The changes are fully documented in `LESSONS_LEARNED.md` (LL-24 through LL-33) — which per §2.12 explicitly does not require an ADR.
- The extensions to `GITHUB_AGENT_RULES.md` and the operating model are additive documentation, not structural workflow changes to `AGENTS.md`.

**Justification:** These changes are in the category of "routine PE implementation choices" and "changes fully documented in LESSONS_LEARNED.md that do not affect workflow structure" — both explicit non-ADR triggers.

---

## PM Capability Audit Finding (Read-Only Metadata)

**Finding:** `PM_GITHUB_WRITE_CAPABILITY_RESTRICTION_REQUIRED`

A read-only audit of PM GitHub-capable paths was conducted (metadata only — no credential content, no token values, no file contents):

| Capability Path | Availability | Evidence Class |
|----------------|-------------|----------------|
| `gh` CLI authentication | Present | Path exists; auth status confirmed (read-only check) |
| `git push` via SSH | Present | SSH agent active; remote `origin` configured |
| `git push` via HTTPS | Present | Credential helper configured |
| `bin/gh-agent` | Executable | Binary exists; PM access is prohibited per operating model |
| GitHub PAT/token file | Present | File path known; content not inspected |

**Target state:** PM should not retain standing write/merge capability except a documented PO-approved break-glass path.

**Action deferred:** Actual credential restriction/removal is out of scope for this PE. Deferred to `PE-OPS-GITHUB-PERMISSIONS-01` by explicit plan instruction.

**Formal finding recorded in:** `docs/governance/ELIS_GitHub_Agent_Operating_Model.md` §1.3 and `docs/ops/github-agent/GITHUB_AGENT_RULES.md` §PM_GITHUB_WRITE_CAPABILITY_RESTRICTION_REQUIRED.

---

## Tests Run and Results

```
$ python3 -m pytest tests/test_github_ops_preflight.py -v --tb=short
============================= 44 passed in 0.51s ==============================
```

No pre-existing tests were affected — all changed files are new or additive extensions. No existing test fixtures or mocks were modified.

---

## Open Questions / Validator Attention Items

1. **PM capability restriction deferral:** The formal finding is recorded but actual credential restriction is deferred to PE-OPS-GITHUB-PERMISSIONS-01. Validator should confirm this deferral is correctly documented and not creating a gap.
2. **`check_ci_status_current_head` requires `gh` CLI:** The check calls `gh run list` which requires the GitHub CLI to be installed and authenticated. If the runtime environment lacks `gh`, this check will fail — this is by design (fail closed).
3. **`check_review_artefact_path` requires `.elis/pe/<PE-ID>/` directory:** The canonical REVIEW path must exist in the repo for the check to find files. This is consistent with AGENTS.md §7 but relies on the implementer or PM having created the directory.
4. **STALE_LOCAL_WORKSPACE_HEAD is a subcase:** Class 11 is a subcase of Class 4 (both handled by the same preflight check function). The distinction is clear in documentation but validator should verify that the subcase handling meets the intent.
5. **SECRET_OUTPUT_RISK patterns are not exhaustive:** The SECRET_PATTERNS list covers common token/key patterns but may miss environment-specific secret formats. The guidance is to err on the side of caution — if unsure, do not include the content.

---

## Hard Stop

This file is the final commit on the feature branch. Per AGENTS.md §2.7: HANDOFF.md is committed before push and PR creation.