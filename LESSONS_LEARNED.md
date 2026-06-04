# LESSONS_LEARNED.md — Agent Error Log

Both agents read this file at Step 0 (after `AGENTS.md`).
Each entry records an error pattern observed during PE work,
the rule added to prevent recurrence, and how it was detected.

---

## LL-01 — PR opened before HANDOFF committed

| Field | Value |
|---|---|
| First seen | PE-OC-08 |
| Agent | CODEX |
| AGENTS.md rule | §2.7 — HANDOFF.md must be committed before `git push` and PR creation |

**Error:** PR was opened on the feature branch before `HANDOFF.md` was committed. Gate 1 CI fired on a branch with no Status Packet.

**Root cause:** Implementer pushed after implementation commits but before writing HANDOFF, treating HANDOFF as an afterthought rather than a required deliverable.

**Detection:** Gate 1 `check_status_packet.py` failed — `## Status Packet` section absent.

**Rule added:** §2.7 and §8 do-not: *"Do not open a final (ready) PR before HANDOFF.md is committed on the branch."*

---

## LL-02 — Fabricated test counts — no pasted output

| Field | Value |
|---|---|
| First seen | PE-OC-13 |
| Agent | CODEX |
| AGENTS.md rule | §2.4 — every claim must be supported by pasted command output |

**Error:** HANDOFF claimed "+8 new tests" with no corresponding new test files. Test count in Status Packet did not match actual pytest output.

**Root cause:** Long session context drift — agent generated plausible-sounding numbers without running the command.

**Detection:** Validator ran `pytest` independently; count did not match HANDOFF claim. No new test files in scope diff.

**Rule added:** §2.4 evidence-first: *"Within a session, each step must be confirmed with pasted command output before marking it complete."*

---

## LL-03 — Duplicate YAML job key (last-wins silent drop)

| Field | Value |
|---|---|
| First seen | PE-OC-13 |
| Agent | CODEX |
| AGENTS.md rule | §5.1 — scope gate before every commit |

**Error:** `ci.yml` contained two `slr-quality-check:` job keys. GitHub Actions (js-yaml) uses last-wins semantics — the first job definition was silently dropped, meaning the CI job ran from the wrong definition.

**Root cause:** Iterative edits appended a second job block without removing the first. Scope gate was not run before committing.

**Detection:** Validator ran `grep -c "slr-quality-check:" .github/workflows/ci.yml` — returned 2.

**Rule added:** Pre-commit scope gate in §5.1; mid-session checkpoint §2.9.

---

## LL-04 — Stale HANDOFF HEAD SHA

| Field | Value |
|---|---|
| First seen | PE-OC-13 |
| Agent | CODEX |
| AGENTS.md rule | §6.2 — Status Packet §6.2 must show `git rev-parse HEAD` output |

**Error:** HANDOFF §6.2 showed a HEAD SHA that did not match the actual branch tip. Validator could not reconcile reported state with actual commit history.

**Root cause:** HANDOFF was written from memory / earlier session state rather than from live command output.

**Detection:** Validator ran `git rev-parse HEAD` on the branch — SHA did not match HANDOFF §6.2.

**Rule added:** Status Packet §6.2 must paste verbatim output of `git rev-parse HEAD` and `git log -5`.

---

## LL-05 — PE skipped in registry

| Field | Value |
|---|---|
| First seen | PE-OC-13 → PE-OC-14 transition |
| Agent | PM (registry maintenance error) |
| AGENTS.md rule | §5.1 — CURRENT_PE.md must be updated before agents start |

**Error:** After PE-OC-13 merged, CURRENT_PE.md was advanced directly to PE-OC-15, skipping PE-OC-14 entirely. PE-OC-15 depended on PE-OC-14, so the dependency chain was broken.

**Root cause:** PM incremented PE number without checking the plan's dependency table.

**Detection:** PM review of plan identified PE-OC-14 as a prerequisite for PE-OC-15 with no registry entry.

**Rule added:** Check plan dependency table before updating Current PE field in CURRENT_PE.md.

---

## LL-06 — New AGENTS.md rules not followed mid-session

| Field | Value |
|---|---|
| First seen | PE-OC-14 → PE-OC-15 transition |
| Agent | CODEX |
| AGENTS.md rule | §5.1 Progress Tracking — TodoWrite rule applies to both agents |

**Error:** AGENTS.md was updated with draft PR, milestone comments, and TodoWrite rules (PR #277). CODEX's next session did not follow them because the "Tool note" label read "Claude Code" only, and CODEX interpreted it as not applying to itself.

**Root cause:** Label `Tool note — Claude Code:` was too narrow; CODEX correctly (but unfortunately) excluded itself.

**Detection:** PM observed CODEX's todo list showing all tasks as `pending` while actively working; no draft PR opened at first commit.

**Rule added:** Label changed to `Tool note (both agents):` in §5.1 and §5.2 Progress Tracking.

---

## LL-07 — Host prerequisites assumed but not scoped

| Field | Value |
|---|---|
| First seen | PE-OC-15 |
| Agent | Plan (scoping omission) |
| AGENTS.md rule | §3.4 — verify host prerequisites before running discovery probes |

**Error:** PE-OC-15 required `docker pull ghcr.io/openclaw/openclaw:latest` as a discovery probe. Docker Desktop was not installed on the host machine. The probe timed out (124 s, then 184 s) and the PE was initially classified as `BLOCKED (env)`.

**Root cause:** The plan assumed Docker Desktop as a pre-existing prerequisite, like `git` or `Python`, without explicitly listing it or verifying it at PE start.

**Detection:** `where.exe docker` returned not found; `docker pull` timed out.

**Rule added:** `docs/openclaw/DOCKER_SETUP.md` updated with explicit host prerequisites section. Discovery probes must verify tool availability before running.

---

## LL-08 — `channels add` without `--account <BOT_ID>` causes permanent token:none

| Field | Value |
|---|---|
| First seen | PE-OC-17 post-merge ops (2026-02-26) |
| Agent | CODEX (initial setup) + Claude Code (diagnosis) |
| AGENTS.md rule | §3.4 — verify channel status after every config change |

**Error:** `openclaw channels add --channel telegram --token <TOKEN>` was run without
`--account <BOT_ID>`. The token was stored under account name `"default"`. The binding's
`match.accountId` was a numeric Telegram bot ID. The gateway searched for an account
matching the numeric ID and found none → `token:none` on every startup.

**Root cause:** The `--account` flag is not documented prominently; omitting it silently
creates a `"default"` account that never matches a numeric binding accountId. The
gateway reports `token:none` rather than `account not found`, making the root cause hard
to trace.

**Detection:** `channels status` showed `token:none` despite `channels.telegram.botToken`
being present in the config. Only after reading `channels add --help` was the `--account`
flag discovered.

**Rule added:** When registering a Telegram bot, always use:
`channels add --channel telegram --token <TOKEN> --account <BOT_ID>`
where `BOT_ID` = numeric prefix of the token (digits before the first colon).
The binding's `match.accountId` must equal `BOT_ID`.

---

## LL-09 — Docker Compose `environment:` overrides `env_file:` with empty strings

| Field | Value |
|---|---|
| First seen | PE-OC-17 post-merge ops (2026-02-26) |
| Agent | CODEX (docker-compose.yml author) |
| AGENTS.md rule | §3.4 — verify container env after every compose change |

**Error:** `docker-compose.yml` listed `TELEGRAM_BOT_TOKEN: ${TELEGRAM_BOT_TOKEN}` in
the `environment:` block. The same variable was also supplied by `env_file`. Docker
Compose resolves `${VAR}` in `environment:` from the **host shell**, not from
`env_file`. Because the host PowerShell session did not export `TELEGRAM_BOT_TOKEN`,
Compose substituted an empty string. The `environment:` entry then **overrode** the
correct value from `env_file`, so the container received an empty token.

**Root cause:** Docker Compose precedence: `environment:` > `env_file:`. Listing a
variable in both places with a host-shell expansion in `environment:` silently wins
with an empty value when the host shell has no export.

**Detection:** `channels status` showed `token:none`. Checking container env (existence
only, not value) confirmed `TELEGRAM_BOT_TOKEN` was set but the gateway rejected it.

**Rule added:** Do not list secrets in both `env_file:` and `environment:`. Use
`env_file:` exclusively for all secrets. Only non-secret, hardcoded constants (like
`OPENCLAW_STATE_DIR`) belong in `environment:`.

---

## LL-10 — Agent must never run commands that print secret values

| Field | Value |
|---|---|
| First seen | PE-OC-17 post-merge ops (2026-02-26) |
| Agent | Claude Code |
| AGENTS.md rule | §13 Secrets isolation |

**Error:** Claude Code ran `docker exec openclaw printenv | grep -E 'TELEGRAM|OPENAI|ANTHROPIC'`
as a diagnostic step. The command printed the full values of `TELEGRAM_BOT_TOKEN`,
`OPENAI_API_KEY`, and `ANTHROPIC_API_KEY` into the conversation context.

**Root cause:** The diagnostic intent was to verify that secrets were present in the
container. A filtered `printenv` was chosen over a safe existence check. Even though
the filter was narrow, the output contained full secret values.

**Detection:** User interrupted the session and requested a hard rule be registered.

**Rule added (user-mandated):** Agents must NEVER run any command that prints, reads,
or exposes secret values. Use existence checks only:
- Shell: `[ -n "$VAR" ] && echo set || echo unset`
- Docker: `MSYS_NO_PATHCONV=1 docker exec <c> /bin/sh -c '[ -n "$(printenv VAR)" ] && echo set || echo unset'`
- Python: `bool(os.environ.get("VAR"))`

Do not use `printenv`, `env`, `cat .env`, `Get-Content .env`, or any grep/filter on
env output — even filtered output can expose values. Recorded in Claude Code memory.

---

## LL-11 — Token rotation requires `channels add` + second container restart

| Field | Value |
|---|---|
| First seen | Secret rotation (2026-02-26) |
| Agent | Claude Code |

After rotating the Telegram bot token, restarting the container alone is not enough.
The state dir's `channels.telegram.accounts.<BOT_ID>.botToken` still holds the old
(revoked) token. The symptom is `token:config, error:Call to 'getMe' failed! (401: Unauthorized)`.

**Root cause (two-step):**
1. `channels add` must be re-run explicitly to update the channels section in
   `~/.openclaw/openclaw.json` with the new token.
2. After `channels add` rewrites the config file, the gateway process in memory still
   holds the old token. A second restart (`docker compose restart`) flushes it.

**Fix:**
```
1. Update ~/.openclaw/.env with new token
2. docker compose down && docker compose up -d   ← loads new env
3. channels add --channel telegram --token <NEW> --account <BOT_ID>  ← updates config file
4. docker compose restart   ← flushes in-memory state
5. channels status → enabled, configured, running, mode:polling, token:config
```

On Windows PowerShell, pass the token via a variable (never print it):
```powershell
$t = (Select-String '^TELEGRAM_BOT_TOKEN=' "$env:USERPROFILE\.openclaw\.env").Line -replace '^TELEGRAM_BOT_TOKEN=',''
docker exec openclaw node openclaw.mjs channels add --channel telegram --token $t --account <BOT_ID>
```

PO pairing survives token rotation — no re-pairing is needed.

---

## LL-12 — ADR coverage claim must match delivered scope exactly

| Field | Value |
|---|---|
| First seen | PE-GHA-02 (2026-04-22) |
| Agent | Claude Code (Implementer) |
| AGENTS.md rule | §2.9 — mid-session checkpoint: confirm scope before every commit |

**Error:** ADR-012 stated "every workflow file carries a `# Classification:` comment on its first line" but only 6 of 35 workflow files had the header when the PR was opened. CODEX issued a FAIL verdict specifically because the ADR's universal claim was not satisfied.

**Root cause:** ADR was written to describe the intended final state; implementation only addressed the workflows the Implementer touched directly, leaving 29 files unclassified.

**Detection:** Validator ran `head -1` on all workflow files and compared against the ADR claim.

**Rule added:** Before committing an ADR (or any document that makes a universal claim about repo state), verify the claim is true by checking every instance. "Every X has Y" means every X — not "the ones I touched."

---

## LL-13 — HANDOFF AC status must reflect actual implementation state

| Field | Value |
|---|---|
| First seen | PE-GHA-02 (2026-04-22) |
| Agent | Claude Code (Implementer) |
| AGENTS.md rule | §2.7 — HANDOFF.md must accurately represent the delivered state |

**Error:** HANDOFF marked AC-6 (branch protection) as `PARTIAL` while other ACs were `PASS`. CODEX issued a FAIL because the HANDOFF stated a known incomplete state without a PM-authorised re-scope. The Validator correctly required either full implementation or explicit PM re-scope before issuing PASS.

**Root cause:** Implementer treated PARTIAL as an acceptable HANDOFF state. It is not — every AC must be either PASS, explicitly re-scoped by PM (with evidence), or BLOCKED with a named dependency.

**Detection:** Validator read the AC table and cross-checked against actual repo state.

**Rule added:** Never mark an AC as PARTIAL in a final HANDOFF. Use PASS (fully met), BLOCKED (named external dependency with PM acknowledgement), or open a PM re-scope before submitting the HANDOFF.

---

## LL-14 — Black and pytest fail on stale temp dirs on Windows

| Field | Value |
|---|---|
| First seen | PE-GHA-02 (2026-04-22) |
| Agent | Claude Code |
| AGENTS.md rule | §6.4 — quality gate commands must produce clean, trustworthy output |

**Error:** Running `python -m black --check .` and `python -m pytest` on the full repo from a Windows working directory raised `PermissionError: [WinError 5] Access is denied` on stale pytest temp directories (`.pytest-temp-*`, `tmp*`), causing the commands to exit non-zero even when all Python files and tests were valid.

**Root cause:** Previous PE sessions left temp directories in the repo root that Windows file locking prevented black and pytest from scanning.

**Detection:** PermissionError lines in command output pointing to `.pytest-temp-*` and `tmp*` directories.

**Fix (Windows only):**
- Black: `python -m black --check --include "\.py$" elis/ tests/ scripts/` — target Python source directories directly.
- Pytest: `python -m pytest tests/ --basetemp=.tmp/pe-<id> --tb=no` — redirect temp output to a fresh path.

These workarounds are not needed on elis-server (Ubuntu).

---

## LL-15 — Branch protection updates require admin PAT; bot accounts return 404

| Field | Value |
|---|---|
| First seen | PE-GHA-02 (2026-04-22) |
| Agent | Claude Code |
| AGENTS.md rule | §3.4 — verify prerequisites and access rights before attempting privileged operations |

**Error:** Claude Code and CODEX (elis-claude-bot, elis-codex-bot) both received HTTP 404 when attempting `gh api repos/.../branches/main/protection --method PUT`. The operation silently appeared to fail rather than returning 403.

**Root cause:** Bot accounts have write collaborator access but not admin rights. The GitHub branch protection API returns 404 (not 403) for non-admin tokens, masking the true cause.

**Detection:** HTTP 404 response from the branch protection endpoint.

**Rule added:** Any operation touching branch protection rules requires the PO/admin account. Bot accounts cannot read or write branch protection settings — 404 from this endpoint always means insufficient privilege, not a missing resource. Document such operations as PM actions and provide the exact command for the PO to run.

---

## LL-16 — REVIEW Evidence section must contain a fenced code block

| Field | Value |
|---|---|
| First seen | PE-GHA series (2026-04-22) |
| Agent | Claude Code (Validator) |
| AGENTS.md rule | §5.2 — Validator verdict delivery; `check_review.py` must pass before pushing |

**Error:** `check_review.py` rejected a REVIEW file because the `### Evidence` section contained only prose and inline code, with no fenced code block (` ``` `). The script requires at least one fenced block in that section.

**Root cause:** Validator wrote evidence as descriptive text without wrapping command output in a fenced block.

**Detection:** `python scripts/check_review.py` exits non-zero with message indicating missing fenced block in Evidence.

**Rule added:** Always run `REVIEW_FILE=REVIEW_PE_<ID>.md python scripts/check_review.py` before pushing the REVIEW file. The `### Evidence` section must contain at least one fenced code block enclosing actual command output — prose description alone is not sufficient.

---

## LL-17 — Mandatory Dispatch Reset Gate before every agent dispatch

| Field | Value |
|---|---|
| First seen | PE-OPS-A2A-PRODUCTION-02 (2026-05-31) |
| Classification | PM_DISPATCH_MISSING_TARGET_AGENT_RESET |
| AGENTS.md rule | §2 — evidence-first; new rule added to `docs/governance/ELIS_Agent_Dispatch_Binding_and_Validation_Rules.md` |

**Error:** PM dispatched infra-val-b for a new validation round without resetting or acknowledging the agent's stale session (88k+ input tokens, prior PE context). The agent ran in its old context, rendering the validation evidence unreliable.

**Root cause:** No formal pre-dispatch reset requirement existed. PM assumed the agent would start clean on a new dispatch.

**Rule added:** Before every agent dispatch, the target agent must produce a 14-field reset/binding acknowledgement: `agent_id`, `pe_id`, `role_task`, `session_key`, `worktree`, `git_root`, `branch`, `head`, `git_status`, `git_identity`, `runtime_model`, `prior_context_discarded`, `authorised_write_scope`, `timestamp`. Sessions exceeding 50k tokens must be reset via `--session-key` before dispatch. The PM must receive and accept the ack before authorising the substantive task. Documented in `ELIS_Agent_Dispatch_Binding_and_Validation_Rules.md` §Dispatch Reset Gate.

---

## LL-18 — Three-layer model registry check: L1/L2/L3

| Field | Value |
|---|---|
| First seen | PE-OPS-A2A-PRODUCTION-02 (2026-05-31) |
| Agent | Claude Code (PM / Implementer) |
| AGENTS.md rule | §2.4 — evidence-first; new governance artefact |

**Error:** Initial model registry check (Gate 2A) only verified `openclaw.json` per-agent model fields (L1). It missed the global allowlist (`agents.defaults.models` — L2) and per-agent `models.json` catalogues (L3), leaving model drift undetected.

**Rule added:** `scripts/check_agent_model_registry.py` implements a three-layer check:
- L1: `openclaw.json → agents.list[].model` — agent exists with non-empty model field
- L2: `openclaw.json → agents.defaults.models` — model appears in global allowlist (exact or provider-wildcard match)
- L3: `~/.openclaw/agents/<agentId>/agent/models.json` — model registered in per-agent runtime catalogue

All three layers must PASS for an infra agent to be considered model-registry-compliant. L3 failures for programme agents are tracked separately as known drift.

---

## LL-19 — `--sync-agent-catalogue` as controlled L3 repair fallback

| Field | Value |
|---|---|
| First seen | PE-OPS-A2A-PRODUCTION-02 (2026-05-31) |
| Agent | Claude Code (Implementer) |
| AGENTS.md rule | §2.3 — file ownership; no unilateral config mutation |

**Error:** After discovering infra-val-b L3 FAIL (model absent from `models.json`), there was no governed path to repair the per-agent catalogue without touching `openclaw.json` or performing an uncontrolled file edit.

**Rule added:** `--sync-agent-catalogue --approve --agent <agentId>` mode added to `check_agent_model_registry.py`. Requirements: `--approve` flag must be explicit (prevents accidental mutation); `--agent` must name exactly one agent; creates a timestamped backup (`models.json.bak.<YYYYMMDDTHHMMSSZ>`) before mutation; appends a minimal model entry to the matching provider block; validates JSON; re-runs the three-layer check. Never touches `openclaw.json`. This is the only authorised path for L3 repair without a full OpenClaw config change.

---

## LL-20 — OpenClaw CLI PATH/version mismatch

| Field | Value |
|---|---|
| First seen | PE-OPS-A2A-PRODUCTION-02 (2026-05-31) |
| Agent | Claude Code (PM) |
| AGENTS.md rule | §2.4 — evidence must be from authoritative source |

**Error:** The PATH-resolved `openclaw` binary (`/opt/openclaw/tools/node-v22.22.0/bin/openclaw`, v2026.4.21) lacked the `--session-key` flag and had a gateway protocol mismatch with the running v2026.5.27 gateway. Commands appeared to run but produced unreliable or blocked output.

**Root cause:** PATH contains an older openclaw binary. The canonical current binary is `/opt/openclaw/bin/openclaw` (v2026.5.27).

**Rule added:** Always invoke the full path `/opt/openclaw/bin/openclaw` for agent dispatch, `--session-key`, and any flag introduced after v2026.4.21. Never rely on PATH-resolved `openclaw` for production dispatch. The `--local` flag is an approved fallback for gateway protocol mismatches but must be noted in the Status Packet as an execution path deviation. Resolve the PATH mismatch as a follow-up PE.

---

## LL-21 — Model provenance via executionTrace/agentMeta, not agent self-report

| Field | Value |
|---|---|
| First seen | PE-OPS-A2A-PRODUCTION-02 (2026-05-31) |
| Agent | Claude Code (PM/Validator) |
| AGENTS.md rule | §2.4 — evidence-first; authoritative source for model identity |

**Error:** Initial model-resilient validation attempts used `sessions_spawn` with an explicit `model` parameter. The spawn returned `modelApplied: true` but the actual runtime model remained the caller's model (claude-sonnet). `MODEL_DIFFERS` was falsely YES based on self-report, not execution evidence.

**Root cause:** `sessions_spawn` inherits the caller's model context regardless of the `model` parameter. `modelApplied: true` reflects the parameter being accepted, not the model actually being used.

**Rule added:** For ELIS model-resilience validation, the authoritative model evidence is `executionTrace.winnerProvider` + `executionTrace.winnerModel` from the DISPATCH_PROVENANCE_PROOF_V1 schema, or the `agentMeta` field in session output — not the agent's self-reported model string. A `MODEL_DIFFERS: YES` claim in a REVIEW file is only valid if backed by one of these authoritative fields. PM-spawned sub-agents are not a reliable path for cross-model validation; use direct OpenClaw agent dispatch (`/opt/openclaw/bin/openclaw agent run ... --session-key`) with a fresh session.

---

## LL-22 — Token/context overload requires compact validation mode

| Field | Value |
|---|---|
| First seen | PE-OPS-A2A-PRODUCTION-02 (2026-05-31) |
| Agent | Claude Code (PM/Validator) |
| AGENTS.md rule | §2.5 — session boundaries; stale context invalidates evidence |

**Error:** infra-val-b accumulated 88k+ input tokens across prior PE sessions. A dispatch attempt resulted in exit 137 (OOM kill). The validation run was lost and had to be restarted with a fresh session key.

**Root cause:** No mechanism existed to detect or prevent dispatch to an agent whose context exceeded safe limits. The 50k-token reset threshold was not formalised.

**Rule added (interim):** Sessions exceeding 50k input tokens must be reset before dispatch (see LL-17 Dispatch Reset Gate). A follow-up PE should implement compact validation mode: a stateless, read-only validation path that loads only the target files and test suite, with no accumulated conversational context. This mode is particularly important for validators that run after multiple prior sessions on the same agent surface.

---

## LL-23 — OpenClaw CLI/API-first rule: no direct config file mutation

| Field | Value |
|---|---|
| First seen | PE-OPS-A2A-PRODUCTION-02 (2026-05-31) |
| Agent | Claude Code (PM) |
| AGENTS.md rule | §2 — PM must not edit openclaw.json; route via gateway/Supervisor |

**Error:** During model registry remediation, there was pressure to directly edit `openclaw.json` or agent `models.json` files to fix L2/L3 failures quickly. Direct mutation without a governed path risks JSON corruption, undocumented drift, and loss of backup/audit trail.

**Rule added:** All OpenClaw runtime config changes must go through the OpenClaw CLI or API (e.g. `gateway config.schema.patch`, `--sync-agent-catalogue`). Direct file edits to `openclaw.json` are prohibited without explicit PM/Supervisor authorisation and a backup. The `--sync-agent-catalogue` mode was created specifically to satisfy this rule for L3 repairs. A follow-up PE should document this as a formal OpenClaw CLI/API-first rule in `AGENTS.md` or a dedicated governance document.

---

## LL-24 — PM_WRONG_RESPONSIBILITY_BOUNDARY — PM must not perform GitHub write operations

| Field | Value |
|---|---|
| First seen | PR #471 (2026-06-04) |
| Agent | Multiple (PM, GitHub Agent, implementers) |
| AGENTS.md rule | §4.3 — PM coordinates; GitHub Agent executes |
| Skill Pack rule | ELIS_GITHUB_PROTECTED_FILES_RULE (Rule 8); ELIS_GITHUB_NO_DIRECT_MAIN_PUSH_RULE (Rule 10) |

**Error:** PM performed GitHub write operations (push, PR ops, merge actions) that belong to the GitHub Agent role. Agents edited governance files (`CURRENT_PE.md`, `AGENTS.md` governance sections) that are reserved for PM/PO editing.

**Root cause:** The role boundary between PM coordination and GitHub Agent execution was documented but not yet enforced by deterministic preflight checks. Protected files had no automated scope-gate enforcement to detect non-PM edits.

**Detection:** Scope diff (`git diff --name-status`) plus actor identity cross-reference; GitHub audit log for actor mismatch.

**Prevention rule:** Any agent operating on files outside its role boundary must be blocked by scope-gate enforcement. PM must not execute git push, PR creation, merge, or label operations. Protected files list enforced via `check_protected_files_not_edited()` in the preflight script.

**Reference:** `docs/ops/github-agent/ELIS_GITHUB_OPS_SKILL_PACK.md` §Rule 8, Rule 10; `scripts/elis_github_ops_preflight.py` check_protected_files_not_edited()

---

## LL-25 — PM_GITHUB_WRITE_CAPABILITY_RESTRICTION_REQUIRED — PM retains standing write access

| Field | Value |
|---|---|
| First seen | PR #471 (2026-06-04) |
| Agent | PM / Infrastructure |
| AGENTS.md rule | §4.3 — PM must not write to GitHub directly |
| Skill Pack rule | ELIS_GITHUB_NO_MERGE_WITHOUT_PO_APPROVAL_RULE (Rule 11); ELIS_GITHUB_SAFE_ROLLBACK_RULE (Rule 13) |

**Error:** PM retains standing GitHub write/merge capability via `gh` CLI auth and `git push` SSH access, despite the operating model stating PM must not write to GitHub directly. This creates a structural risk: a PM session could inadvertently push, merge, or create PRs outside the governed GitHub Agent path.

**Root cause:** The PM identity was set up with full write credentials during initial GitHub integration. No dedicated PE was scoped to restrict PM capability to a documented break-glass path.

**Detection:** Read-only audit of PM GitHub-capable paths: `gh auth status`, `git remote get-url origin`, and SSH key existence. Evidence limited to paths and command availability — no credential content.

**Prevention rule:** Record formal finding. Actual credential restriction/removal is deferred to PE-OPS-GITHUB-PERMISSIONS-01. The preflight script's `check_merge_approval()` detects PM capability paths and flags them.

**Reference:** `docs/ops/github-agent/ELIS_GITHUB_OPS_SKILL_PACK.md` §Rule 11; `docs/governance/ELIS_GitHub_Agent_Operating_Model.md` §1.3; `scripts/elis_github_ops_preflight.py` check_merge_approval()

---

## LL-26 — PE_BRANCH_LOCKED_BY_OTHER_WORKTREE — branch checked out in multiple worktrees

| Field | Value |
|---|---|
| First seen | PR #471 (2026-06-04) |
| Agent | Multiple (GitHub Agent, implementers) |
| AGENTS.md rule | §3 — Worktree lifecycle; one PE = one branch |
| Skill Pack rule | ELIS_GITHUB_BRANCH_LOCK_PREFLIGHT_RULE (Rule 2); ELIS_GITHUB_LINKED_WORKTREE_BRANCH_RELEASE_RULE (Rule 3) |

**Error:** A branch needed for checkout was already checked out in a different Git worktree, preventing the checkout from succeeding. The linked worktree model means branches are exclusive to one worktree at a time.

**Root cause:** No preflight check ran before `git checkout` to verify the target branch was not locked in another worktree. When multiple agents or the GitHub Agent need the same branch, the locking worktree must release it first.

**Detection:** `git worktree list` shows the branch in a non-current worktree.

**Prevention rule:** Run `check_branch_not_locked()` before every checkout. If locked, release via `ELIS_GITHUB_LINKED_WORKTREE_BRANCH_RELEASE_RULE` with PM/PO approval.

**Reference:** `docs/ops/github-agent/ELIS_GITHUB_OPS_SKILL_PACK.md` §Rule 2, Rule 3; `scripts/elis_github_ops_preflight.py` check_branch_not_locked()

---

## LL-27 — STALE_LOCAL_PE_BRANCH_HEAD — local branch behind origin/main

| Field | Value |
|---|---|
| First seen | PR #471 (2026-06-04) |
| Agent | Multiple |
| AGENTS.md rule | §2.6 — rebase after every base-branch merge |
| Skill Pack rule | ELIS_GITHUB_STALE_LOCAL_BRANCH_HEAD_RULE (Rule 4) |

**Error:** The local PE feature branch was behind `origin/main`, meaning any push or PR creation would have incorporated stale code. Diverged branches (both ahead and behind) require rebase.

**Root cause:** After another PR merged to `main`, the active feature branch was not rebased. No preflight check detected the staleness before push/PR operations.

**Detection:** `git fetch origin` followed by `git rev-list --count --left-right origin/main..HEAD` shows behind count > 0.

**Prevention rule:** Before any push or PR creation, fetch and check ahead/behind. If behind or diverged, rebase onto `origin/main` before proceeding. The preflight script's `check_local_branch_not_stale()` enforces this.

**Reference:** `docs/ops/github-agent/ELIS_GITHUB_OPS_SKILL_PACK.md` §Rule 4; `scripts/elis_github_ops_preflight.py` check_local_branch_not_stale()

---

## LL-28 — LOCAL_UNPUSHED_COMMITS_BLOCK_RESET — unpushed commits prevent workspace reset

| Field | Value |
|---|---|
| First seen | PR #471 (2026-06-04) |
| Agent | Multiple |
| AGENTS.md rule | §2.5 — clean tree before context switch |
| Skill Pack rule | ELIS_GITHUB_PUSH_PR_UPDATE_SKILL (Rule 5) |

**Error:** Local commits existed on a branch that were not present on the remote, blocking workspace reset for a new PE. The agent could not switch contexts because unpushed changes would be lost.

**Root cause:** Commits were made locally (as required) but not pushed before a reset was needed. The push step is PM/GitHub Agent-gated, creating a coordination gap: the implementer commits but cannot push, and the GitHub Agent may not push before the implementer signals readiness.

**Detection:** `git log origin/<branch>..HEAD` returns non-empty.

**Prevention rule:** Before workspace reset, check for unpushed commits. If present, either push (via GitHub Agent) or stash/archive the branch. The preflight script's `check_no_local_unpushed_commits()` detects this state.

**Reference:** `docs/ops/github-agent/ELIS_GITHUB_OPS_SKILL_PACK.md` §Rule 5; `scripts/elis_github_ops_preflight.py` check_no_local_unpushed_commits()

---

## LL-29 — STALE_CHECK_RUN_NOT_CURRENT_HEAD — CI feedback from wrong commit

| Field | Value |
|---|---|
| First seen | PR #471 (2026-06-04) |
| Agent | Multiple (GitHub Agent, implementers, validators) |
| AGENTS.md rule | §2.4 — evidence-first; stale runs are not valid evidence |
| Skill Pack rule | ELIS_GITHUB_CHECKS_MONITORING_SKILL (Rule 7); ELIS_GITHUB_PR_CREATION_SKILL (Rule 6) |

**Error:** CI check runs existed but corresponded to an older commit SHA, not the current HEAD. A PR was created or a merge was evaluated based on stale CI feedback, giving a false sense of CI health.

**Root cause:** CI runs are tied to the SHA at push time. After a rebase or force-push (by GitHub Agent), the old CI runs still show in the run list but are no longer relevant. The agent looked at the most recent runs without verifying they matched the current HEAD SHA.

**Detection:** `gh run list --branch <branch>` filtered by SHA does not include current HEAD.

**Prevention rule:** Before PR creation or merge evaluation, verify CI check runs are for the current HEAD SHA. The preflight script's `check_ci_status_current_head()` reports stale vs current runs.

**Reference:** `docs/ops/github-agent/ELIS_GITHUB_OPS_SKILL_PACK.md` §Rule 6, Rule 7; `scripts/elis_github_ops_preflight.py` check_ci_status_current_head()

---

## LL-30 — REVIEW_ARTEFACT_WRONG_PATH — REVIEW file in wrong directory

| Field | Value |
|---|---|
| First seen | PR #471 (2026-06-04) |
| Agent | Implementer / Validator |
| AGENTS.md rule | §7 — file ownership by canonical paths |
| Skill Pack rule | ELIS_GITHUB_PR_CLOSEOUT_PACKET_RULE (Rule 14) |

**Error:** A REVIEW file was placed in a directory that did not match the governing standard (e.g. at repo root instead of inside `.elis/pe/<PE-ID>/`). This caused automated closeout tools to miss the artefact.

**Root cause:** The canonical REVIEW path (`.elis/pe/<PE-ID>/REVIEW.md`) was documented but not enforced by any validation check. Agents placed REVIEW files where they were convenient rather than where the governance expects them.

**Detection:** File path pattern match against `REVIEW_PE<N>.md` in the expected location vs actual location.

**Prevention rule:** Before closeout, verify REVIEW files are at the canonical path. The preflight script's `check_review_artefact_path()` enforces this.

**Reference:** `docs/ops/github-agent/ELIS_GITHUB_OPS_SKILL_PACK.md` §Rule 14; `scripts/elis_github_ops_preflight.py` check_review_artefact_path()

---

## LL-31 — REVIEW_SCHEMA_NONCOMPLIANT — REVIEW file missing required sections

| Field | Value |
|---|---|
| First seen | PR #471 (2026-06-04) |
| Agent | Validator |
| AGENTS.md rule | §2.4.1 — REVIEW must contain Evidence section with inline content |
| Skill Pack rule | ELIS_GITHUB_PR_CLOSEOUT_PACKET_RULE (Rule 14) |

**Error:** A REVIEW file was missing required sections (`### Evidence`, `### Verdict`, `### Failure classes addressed`) or had content that did not satisfy the governing schema. The missing Evidence section made the verdict unsupported and invalid per AGENTS.md §2.4.1.

**Root cause:** The REVIEW schema requirements existed in AGENTS.md (§2.4.1) but were not checked by any automated validation. Validator could submit a noncompliant REVIEW that passed human review but failed structural checks.

**Detection:** Schema validation check (grep for required headings) in the REVIEW file.

**Prevention rule:** Before closeout, validate REVIEW files have all required headings and inline evidence. The preflight script's `check_review_schema()` enforces this.

**Reference:** `docs/ops/github-agent/ELIS_GITHUB_OPS_SKILL_PACK.md` §Rule 14; `scripts/elis_github_ops_preflight.py` check_review_schema()

---

## LL-32 — SECRET_OUTPUT_RISK — credential content leaked in evidence

| Field | Value |
|---|---|
| First seen | PR #471 (2026-06-04) |
| Agent | Multiple |
| AGENTS.md rule | §13 — Secrets isolation; never print secret values |
| Skill Pack rule | ELIS_GITHUB_NO_SECRET_OUTPUT_RULE (Rule 9) |

**Error:** Evidence, diagnostic output, or status packets contained credential content, tokens, secret keys, or private key material. Even filtered output (e.g. `grep` on env vars) can expose full secret values.

**Root cause:** Agents used diagnostic commands (`printenv`, `cat`, `gh auth status` with verbose output) that included credential content. No automated scan was in place to detect secrets before output was committed or sent.

**Detection:** Pattern scan for `ghp_*`, `sk-*`, `BEGIN.*PRIVATE KEY`, file content from `/opt/elis/secrets/` paths.

**Prevention rule:** Never include credential content in any output. Use existence checks only (`[ -n "$VAR" ] && echo set || echo unset`). The preflight script's `check_no_secret_output()` scans text for secret patterns before release.

**Reference:** `docs/ops/github-agent/ELIS_GITHUB_OPS_SKILL_PACK.md` §Rule 9; `scripts/elis_github_ops_preflight.py` check_no_secret_output()

---

## LL-33 — STALE_LOCAL_WORKSPACE_HEAD — fixed workspace base out of sync

| Field | Value |
|---|---|
| First seen | Phase 1 discovery (PE-OPS-GITHUB-SKILLS-01, 2026-06-04) |
| Agent | Multiple (fixed workspace agents) |
| AGENTS.md rule | §2.6 — rebase after every base-branch merge; §3 — worktree lifecycle |
| Skill Pack rule | ELIS_GITHUB_STALE_LOCAL_BRANCH_HEAD_RULE (Rule 4 — base-worktree sync subcase) |

**Error:** The fixed agent workspace had a detached HEAD that was behind `origin/main`, causing base misalignment for any PE branch. When the workspace base is stale, feature branches rebased onto it carry the staleness forward.

**Root cause:** The fixed workspace (e.g. `/opt/elis/agent-worktrees/infra-impl-b`) uses a detached HEAD to follow `main` without being on a branch. After a merge to `main`, the detached HEAD was not synced. This is a subcase of `STALE_LOCAL_PE_BRANCH_HEAD` specific to base worktrees.

**Detection:** `git rev-list --count HEAD..origin/main` in detached HEAD state shows behind count > 0.

**Prevention rule:** Before any PE work, check if the fixed workspace detached HEAD is current with `origin/main`. If behind, run `git switch --detach origin/main` to sync. Then rebase the PE feature branch. The preflight script's `check_local_branch_not_stale()` detects this state when HEAD is detached.

**Reference:** `docs/ops/github-agent/ELIS_GITHUB_OPS_SKILL_PACK.md` §Rule 4 (base-worktree sync subcase); `scripts/elis_github_ops_preflight.py` check_local_branch_not_stale()"}]
