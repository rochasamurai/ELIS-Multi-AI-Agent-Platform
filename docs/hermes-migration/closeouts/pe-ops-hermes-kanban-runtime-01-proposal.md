# PE-OPS-HERMES-KANBAN-RUNTIME-01 — Proposal
## Enable Kanban for ELIS Agent Operations

**Author:** ELIS Supervisor (Hermes Platform Monitor)
**Date:** 2026-06-05
**Status:** Awaiting PO approval — DO NOT IMPLEMENT

---

## 1. Executive Summary

Hermes Kanban is **already partially operational** on elis-server. The dispatcher is running
inside the gateway, the kanban.db is initialised, the dashboard tab is registered, and the
dashboard is reachable via Tailscale. The board is simply empty — no tasks have been created.

The "runtime gating" reports from earlier PE sessions were **misleading**: the dashboard tab
always loads. The actual gating applies to the **kanban_* Python tools** (available to agents),
not to CLI operations or dashboard visibility. The Supervisor can already use `hermes kanban`
CLI commands to create and manage tasks.

The minimum viable pilot requires **zero config changes** to the Supervisor or production
profiles. The PO can observe the full coordination layer today.

---

## 2. Architecture: How Kanban Works

### 2.1 Three interaction surfaces

| Surface | Who uses it | How it works |
|---|---|---|
| **Dashboard** (WebUI) | PO / human operator | Reads kanban.db directly, drag-drop, real-time events via WebSocket |
| **CLI** (`hermes kanban`) | Human operator, Supervisor agent | Python kanban_db layer, same code paths as dashboard |
| **Kanban tools** (`kanban_*`) | Worker agents, orchestrator agents | Python functions in the agent's tool schema |

All three surfaces write to the same SQLite database (`~/.hermes/kanban.db`), so changes from
any surface are immediately visible everywhere.

### 2.2 Dispatcher

The dispatcher is a long-lived loop that:
- Runs **inside the gateway** (`kanban.dispatch_in_gateway: true`, default)
- Sweeps **every 60 seconds** (`kanban.dispatch_interval_seconds: 60`)
- Promotes ready tasks, atomically claims them, spawns worker profiles
- After `failure_limit` (default 2) consecutive spawn failures, auto-blocks the task
- Reclaims stale claims after `dispatch_stale_timeout_seconds` (default 4h)

**Current state on elis-server:** Dispatcher is ACTIVE (gateway running, dispatch_in_gateway on).

### 2.3 Worker lifecycle

When the dispatcher spawns a worker:
1. Sets `HERMES_KANBAN_TASK=<task_id>` in the child's environment
2. This env var gates the `kanban_*` toolset — only present when set
3. The worker auto-loads the `kanban-worker` skill (dispatcher injects `--skills kanban-worker`)
4. The worker's system prompt gets `KANBAN_GUIDANCE` (~835 tokens) injected
5. Worker calls `kanban_show()` to read its task, works, then calls `kanban_complete()` or `kanban_block()`

### 2.4 Tool gating explained

The `kanban_*` Python tools are gated by `_check_kanban_mode()` in `tools/kanban_tools.py`:

```python
def _check_kanban_mode() -> bool:
    # 1. HERMES_KANBAN_TASK env var set → worker spawned by dispatcher
    if os.environ.get("HERMES_KANBAN_TASK"):
        return True
    # 2. "kanban" in profile's toolsets config → orchestrator profile
    return _profile_has_kanban_toolset()

def _profile_has_kanban_toolset() -> bool:
    cfg = load_config()
    return "kanban" in cfg.get("toolsets", [])
```

**Two tool tiers:**

| Tier | Condition | Tools available |
|---|---|---|
| **Worker** | `HERMES_KANBAN_TASK` set | `kanban_show`, `kanban_complete`, `kanban_block`, `kanban_heartbeat`, `kanban_comment`, `kanban_create` |
| **Orchestrator** | `"kanban"` in profile toolsets AND no `HERMES_KANBAN_TASK` | All of the above + `kanban_list`, `kanban_unblock`, `kanban_link` |

This means:
- **Supervisor (default profile)**: Has `toolsets: [hermes-cli]` — NO kanban tools. Can use CLI.
- **Workers**: Get worker-tier tools automatically via `HERMES_KANBAN_TASK` env.
- **Orchestrators**: Need `"kanban"` explicitly in their toolsets.

### 2.5 Dashboard kanban tab

The kanban dashboard plugin (`plugins/kanban/dashboard/manifest.json`) registers a tab at
`/kanban` positioned after the Skills tab. The dashboard **always** discovers and mounts this
tab — it reads `kanban.db` directly. The tab shows:
- Board columns: Triage → Todo → Ready → Running → Blocked → Done
- Dispatcher status indicator
- Task cards with assignee, priority, comments
- Drag-and-drop between columns
- Auto-decompose toggle (uses `kanban.auto_decompose` + `auxiliary.kanban_decomposer` model)

**Current state:** Dashboard running on `100.84.95.38:9119` (Tailscale). Kanban tab present
but board is empty (no tasks created).

---

## 3. Current State on elis-server

### Confirmed operational
| Component | Status | Evidence |
|---|---|---|
| `kanban.db` | Initialised | `/home/samurai/.hermes/kanban.db` (114 KB) |
| Gateway dispatcher | Active | `kanban.dispatch_in_gateway: true`, gateway PID 215408 |
| Dashboard | Running | `systemctl --user` shows active, port 9119 bound to `100.84.95.38` |
| Board | Empty | `hermes kanban list` → "(no matching tasks)" |
| Profiles | 2 | `default` (deepseek-v4-pro), `elis-advisor` (gpt-5.4-mini) |
| Kanban tools | Not loaded | Supervisor profile uses `toolsets: [hermes-cli]`, no `kanban` |

### What's missing
1. No tasks on the board
2. No worker profiles (the 2 existing profiles are production — Supervisor and Advisor)
3. No orchestrator profile
4. No test evidence that dispatch → spawn → execute → complete works end-to-end

---

## 4. Minimum Viable Pilot Design

### 4.1 Goal

Demonstrate the full kanban lifecycle (create → dispatch → execute → complete) visible to the
PO in the dashboard, **without touching any production profile or PE workflow**.

### 4.2 Proposed roles

| Profile | Purpose | Toolsets | Model |
|---|---|---|---|
| `elis-kanban-orch` | PO's orchestrator — decomposes goals into tasks | `[kanban, terminal, file]` | `deepseek/deepseek-v4-pro` (same as Supervisor) |
| `elis-kanban-worker-a` | Test worker #1 — simple research/reporting tasks | `[terminal, file, web]` (kanban tools auto-injected) | `deepseek/deepseek-v4-pro` |
| `elis-kanban-worker-b` | Test worker #2 — simple implementation tasks | `[terminal, file, web]` (kanban tools auto-injected) | `deepseek/deepseek-v4-pro` |

**Why these profiles:**
- `elis-kanban-orch` has `kanban` in toolsets → gets orchestrator-level kanban tools
- Workers get kanban tools automatically via `HERMES_KANBAN_TASK` env set by dispatcher
- All use the same model/provider as Supervisor (avoids new API key configuration)
- All use global `.env` for API keys (no per-profile secrets needed)

**What the profiles do NOT do:**
- Do not touch `/opt/elis/` or OpenClaw
- Do not interact with Discord routing
- Do not write to GitHub
- Do not manage PE workflow
- Are not `elis-advisor` or `default` (Supervisor)

### 4.3 Pilot test scenario

1. **Create profiles** (3 profiles, ~5 minutes)
2. **Create a test task** via CLI: `hermes kanban create "Research: summarise Hermes Kanban architecture" --assignee elis-kanban-worker-a`
3. **Promote task** to ready: `hermes kanban promote <id>`
4. **Watch dispatcher** pick it up (within 60 seconds)
5. **Observe in dashboard**: task moves from `ready` → `running` → `done`
6. **Verify** worker's output in task comments/metadata
7. **Create a fan-out test**: orchestrator decomposes a goal into 2 parallel tasks + 1 synthesis task
8. **Observe** parent/child dependency resolution in dashboard

### 4.4 Exact config changes

**No changes to existing profiles.** All new profiles are additive.

#### Step 1 — Create `elis-kanban-orch` profile

```bash
hermes profile create elis-kanban-orch \
  --model deepseek/deepseek-v4-pro \
  --provider openrouter \
  --description "ELIS Kanban orchestrator — decomposes goals into worker tasks for the ELIS platform"
```

Then edit the profile config to add `kanban` to toolsets. The profile config will be at
`~/.hermes/profiles/elis-kanban-orch/config.yaml`. Add:

```yaml
toolsets:
  - kanban
  - terminal
  - file
```

#### Step 2 — Create worker profiles

```bash
hermes profile create elis-kanban-worker-a \
  --model deepseek/deepseek-v4-pro \
  --provider openrouter \
  --description "ELIS Kanban test worker A — research and reporting tasks"

hermes profile create elis-kanban-worker-b \
  --model deepseek/deepseek-v4-pro \
  --provider openrouter \
  --description "ELIS Kanban test worker B — implementation and verification tasks"
```

Worker profiles do NOT need `kanban` in toolsets — the dispatcher injects the `kanban-worker`
skill and sets `HERMES_KANBAN_TASK` env, which auto-activates kanban tools.

#### Step 3 — Verify

```bash
hermes profile list
# Should show: default, elis-advisor, elis-kanban-orch, elis-kanban-worker-a, elis-kanban-worker-b

hermes kanban stats
# Should show: all columns at 0

# Create test task
hermes kanban create "Pilot test: verify kanban lifecycle" --assignee elis-kanban-worker-a
```

**No gateway restart needed.** The dispatcher is embedded in the gateway and will discover
new profiles on the next tick.

### 4.5 Observation surface

The PO observes the full lifecycle at: **`http://100.84.95.38:9119/kanban`** (Tailscale only).

The dashboard shows:
- All columns with task counts
- Task cards moving between columns in real-time
- Dispatcher status (online/offline indicator)
- Per-task comment threads
- Auto-decompose toggle
- Board selector (for future multi-board setups)

---

## 5. What the PO Can Do After Pilot

Once the pilot validates the lifecycle, the PO can:

1. **Create tasks** from the dashboard (Triage column → "New Task" button)
2. **Assign tasks** to workers (dropdown of available profiles)
3. **Decompose goals** into task graphs (auto-decompose or manual)
4. **Comment** on tasks to provide direction
5. **Block/reclaim** tasks that are stuck
6. **Reassign** tasks to different workers
7. **Archive** completed tasks
8. **Use the Supervisor** (via CLI) to programmatically create/monitor tasks

The kanban board becomes the **single coordination layer** for ELIS agent operations.
The PO sees every task, its state, its assignee, and its outcome — in one place.

---

## 6. Risks and Mitigations

| Risk | Severity | Mitigation |
|---|---|---|
| Worker profiles consume API tokens | Medium | Workers use the same OpenRouter key as Supervisor. Cap `max_turns` in profile config. Configure `max_in_progress_per_profile` to limit concurrency. |
| Dispatcher spawns too many workers | Low | Default `max_in_progress_per_profile` is unset (unlimited). Set to 1 during pilot. |
| Worker loops on tool failure | Low | `failure_limit: 2` auto-blocks after 2 consecutive failures. `tool_loop_guardrails` apply. |
| kanban.db corruption | Low | WAL mode. Single-process writer (dispatcher). SQLite is battle-tested. |
| Profile creation fails | Low | Profiles are additive. Can delete with `hermes profile delete`. No production impact. |
| Dashboard kanban tab not visible | Low | Already confirmed — manifest.json is present, dashboard scans it. If not visible, check `dashboard.hidden_plugins` in config. |

### Rollback

```bash
# Delete pilot profiles
hermes profile delete elis-kanban-orch
hermes profile delete elis-kanban-worker-a
hermes profile delete elis-kanban-worker-b

# Archive all test tasks
hermes kanban list --status ready,running,blocked,todo | xargs -I{} hermes kanban archive {}

# No config changes to revert — production profiles untouched
```

---

## 7. What We Do NOT Do (Scope Boundaries)

- ❌ Do NOT add `kanban` to the Supervisor's (`default`) toolsets
- ❌ Do NOT modify `elis-advisor` profile
- ❌ Do NOT create PE worker profiles (implementer, validator, etc.)
- ❌ Do NOT change OpenClaw config or Discord routing
- ❌ Do NOT enable `API_SERVER_ENABLED`
- ❌ Do NOT bind anything publicly (dashboard stays Tailscale-only)
- ❌ Do NOT migrate PM dispatch workflow to kanban
- ❌ Do NOT create systemd units for kanban (dispatcher runs inside gateway)

---

## 8. Recommendation

**PASS** — the infrastructure is fully operational. The kanban dispatcher is running,
the dashboard is reachable, and the board is ready. The pilot requires only additive
profile creation and a single test task — zero risk to production.

The "runtime gating" concern from earlier PEs was about agent tools (not available to
non-dispatched agents), not about dashboard visibility or CLI access. The dashboard
kanban tab always loads; it just shows an empty board until tasks exist.

**Recommended next step:** PO approves this proposal → Supervisor executes the 3 profile
creations + 1 test task → PO verifies in dashboard → report results.

---

## 9. References

- `kanban_tools.py` lines 49-90: `_profile_has_kanban_toolset()` + `_check_kanban_mode()`
- `config.yaml` line 616-627: `kanban:` section — `dispatch_in_gateway: true`, interval 60s
- `plugins/kanban/dashboard/manifest.json`: Dashboard tab registration
- `skills/devops/kanban-worker/SKILL.md`: Worker lifecycle and pitfalls
- `skills/devops/kanban-orchestrator/SKILL.md`: Orchestrator decomposition playbook
- `skills/devops/hermes-dashboard-tailscale-deploy/SKILL.md`: Dashboard deployment on elis-server
- Dashboard: `http://100.84.95.38:9119/` (Tailscale), kanban tab at `/kanban`