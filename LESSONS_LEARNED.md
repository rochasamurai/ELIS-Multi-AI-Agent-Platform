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
