# MEMORY.md — ELIS PM Agent Operational Memory

This file records the durable corrections that must survive session drift.

---

## Current Invariants

- Read governance through workspace entrypoints, not ad-hoc host paths.
- `CURRENT_PE.md` is the source for active PE and release metadata.
- `PLAN_CURRENT.md` is the source for active plan details.
- If `/opt/elis/repo` is dirty, PM PE-status answers must be read from `origin/main:CURRENT_PE.md`, not the local working copy.
- Worktrees must be reported only from `git -C /opt/elis/repo worktree list`.
- PR status must be reported only from `gh pr`.
- Registry branch names do not prove worktrees exist — always verify with `git worktree list`.
- Full PE registry in Discord: compact bullet format (one line per PE), max 25 entries per message, labeled (1/N). Never the raw 7-column table.
- Sequencer pause state lives in `config/pm_loop_control.json`; `!pe veto` and `!pe pause`
  must set it, and `!pe resume` must clear it.
- `!pe auth-check` reports only safe status words such as `OK` / `unavailable`; never print
  token values or derived secrets.
- The observability dashboard is posted hourly to `#pe-status` from
  `scripts/generate_pe_status_report.py`; it must stay sourced from `CURRENT_PE.md`,
  the active plan, review files, and `LESSONS_LEARNED.md`.
- PE start does not require a direct implementer chat session. PM starts assigned PEs by moving status to `implementing` on `main` and verifying dispatcher evidence (`ci-current-pe` -> `implementer-runner`).
- **PM owns implementer and validator dispatch.** The PM-owned authorised dispatch path is `openclaw agent --agent <agent-id>`. PM executes it directly; it is NOT Supervisor-routed. Documented at `docs/governance/ELIS_Agent_Dispatch_Binding_and_Validation_Rules.md` §PM_DISPATCH_OWNERSHIP_RULE.
- **Supervisor is exception/escalation only**, not the routine dispatcher. If PM believes the PM-owned dispatch path is unavailable, classify it as a platform configuration defect, not permission to route through Supervisor. Documented at `docs/governance/ELIS_Agent_Dispatch_Binding_and_Validation_Rules.md` §SUPERVISOR_ESCALATION_ONLY_RULE.
- **GitHub Actions self-hosted runner is not active** on elis-server. `gh workflow run validator-runner.yml` and `gh workflow run implementer-runner.yml` are inactive until a PO-approved runner PE installs and governs the runner.
- **Raw `sessions_spawn` is prohibited** for all PE implementer and validator work. Tool availability is not authorisation.
- **Always use unique `--session-key`** with `openclaw agent` dispatches. Format: `agent:<agent-id>:<unique-suffix>`. Never reuse the agent's `main` session. Documented at `docs/governance/ELIS_Agent_Dispatch_Binding_and_Validation_Rules.md` §DISPATCH_SESSION_KEY_RULE.

---

## Session Reset Rule

If `SOUL.md`, `AGENTS.md`, `MEMORY.md`, workspace entrypoints, or PM exec policy changed,
the current PM session is untrusted until reset.

Do not claim new prompt behavior is active until a fresh session starts.

---

## Never Reintroduce

- hardcoded `PLAN_v1_5.md` as the active plan path
- direct `/opt/elis/repo/...` reads as the normal Discord flow
- worktree answers inferred from registry branch names
- stale copied files used silently when entrypoints fail
- full 7-column Active PE Registry table rendered in Discord
- `sessions_send` as the default validator dispatch path
- Supervisor-routed dispatch as a normal PM dispatch path
- PR-comment-only validator assignment without a PM-owned dispatch attempt
- `openclaw agent` calls without a unique `--session-key`

---

*ELIS PM Agent · MEMORY.md · v1.2 · 2026-06-03*
