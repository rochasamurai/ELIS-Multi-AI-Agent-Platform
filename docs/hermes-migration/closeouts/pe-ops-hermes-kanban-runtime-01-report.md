# PE-OPS-HERMES-KANBAN-RUNTIME-01 — Pilot Report

**Status:** PASS ✓ — Full lifecycle verified  
**Date:** 2026-06-05 16:04 BST  
**Executor:** ELIS Supervisor (Hermes Platform Monitor)

---

## 1. Audit Baseline (Confirmed)

| Component | Status |
|---|---|
| kanban.db | 112 KB, initialised, WAL mode |
| Dispatcher | Active (`dispatch_in_gateway: true`, interval 60s) |
| Dashboard | Running (`systemctl --user`, port 9119, Tailscale `100.84.95.38`) |
| Existing profiles | 2: `default` (Supervisor), `elis-advisor` (Advisor) — untouched |
| Board | Empty — 0 tasks in all columns |
| Gateway | Running (PID 218808, default profile) |

---

## 2. Profiles Created

| Profile | Path | Model | Provider | Toolsets |
|---|---|---|---|---|
| `elis-kanban-orch` | `~/.hermes/profiles/elis-kanban-orch/` | `deepseek/deepseek-v4-pro` | `openrouter` | `kanban, terminal, file` |
| `elis-kanban-worker-a` | `~/.hermes/profiles/elis-kanban-worker-a/` | `deepseek/deepseek-v4-pro` | `openrouter` | `terminal, file, web` |
| `elis-kanban-worker-b` | `~/.hermes/profiles/elis-kanban-worker-b/` | `deepseek/deepseek-v4-pro` | `openrouter` | `terminal, file, web` |

**API keys:** Each profile symlinks `~/.hermes/.env` for OpenRouter key inheritance.

**Exact commands:**
```bash
hermes profile create elis-kanban-orch --description "ELIS Kanban orchestrator — decomposes goals into worker tasks for the ELIS platform"
hermes profile create elis-kanban-worker-a --description "ELIS Kanban test worker A — research and reporting tasks"
hermes profile create elis-kanban-worker-b --description "ELIS Kanban test worker B — implementation and verification tasks"

hermes -p elis-kanban-orch config set model.default deepseek/deepseek-v4-pro
hermes -p elis-kanban-orch config set model.provider openrouter
hermes -p elis-kanban-orch config set toolsets kanban,terminal,file

hermes -p elis-kanban-worker-a config set model.default deepseek/deepseek-v4-pro
hermes -p elis-kanban-worker-a config set model.provider openrouter
hermes -p elis-kanban-worker-a config set toolsets terminal,file,web

hermes -p elis-kanban-worker-b config set model.default deepseek/deepseek-v4-pro
hermes -p elis-kanban-worker-b config set model.provider openrouter
hermes -p elis-kanban-worker-b config set toolsets terminal,file,web

ln -s /home/samurai/.hermes/.env /home/samurai/.hermes/profiles/elis-kanban-orch/.env
ln -s /home/samurai/.hermes/.env /home/samurai/.hermes/profiles/elis-kanban-worker-a/.env
ln -s /home/samurai/.hermes/.env /home/samurai/.hermes/profiles/elis-kanban-worker-b/.env
```

---

## 3. Test Task Lifecycle

**Task ID:** `t_c2fa7e98`  
**Title:** "Pilot test: verify kanban lifecycle"  
**Assignee:** `elis-kanban-worker-a`  
**Created:** 2026-06-05 ~16:04 BST (Unix 1780671851)

**Create command:**
```bash
hermes kanban create "Pilot test: verify kanban lifecycle" \
  --assignee elis-kanban-worker-a \
  --body "ELIS Kanban pilot test task. Confirm the kanban lifecycle is functional by writing a one-line summary to a file in your workspace named pilot-result.txt. The file should contain: 'ELIS Kanban pilot: lifecycle verified — create, assign, dispatch, run, complete.' Then mark the task done." \
  --json
```

### Lifecycle Events

| Timestamp (Unix) | Event | Detail |
|---|---|---|
| 1780671851 | **created** | status=`ready`, assignee=`elis-kanban-worker-a` |
| 1780671864 | **claimed** | lock=`elis-server:218808`, run_id=1 |
| 1780671864 | **spawned** | PID=219258 |
| 1780671868 | **heartbeat** | Worker confirmed alive |
| 1780671889 | **completed** | Summary: "Pilot test passed — wrote pilot-result.txt with verification message confirming full lifecycle: create, assign, dispatch, run, complete." |

**Total elapsed:** 38 seconds (create → done)  
**Dispatch latency:** 13 seconds (create → claim, within 60s interval)  
**Worker runtime:** 25 seconds (claim → complete)

### Worker Output
```json
{
  "run_id": 1,
  "outcome": "completed",
  "summary": "Pilot test passed — wrote pilot-result.txt with verification message confirming full lifecycle: create, assign, dispatch, run, complete.",
  "metadata": {
    "changed_files": ["pilot-result.txt"],
    "lifecycle_verified": true,
    "worker_session_id": "20260605_160425_639b01"
  }
}
```

---

## 4. Dashboard Evidence

- **URL:** `http://100.84.95.38:9119/kanban` (Tailscale)
- **KANBAN tab:** Visible in sidebar (Plugins section)
- **Board:** "Default · 1" — 1 task
- **Done column:** 1 — "Pilot test: verify kanban lifecycle — t_c2fa7e98 — done"
- **Task card shows:** title, assignee `@elis-kanban-worker-a`, age
- **Gateway:** Running (confirmed in sidebar)

---

## 5. Board State (Final)

```
triage      0
todo        0
scheduled   0
ready       0
running     0
blocked     0
done        1  (elis-kanban-worker-a)
```

---

## 6. What Was NOT Touched

✅ `default` (Supervisor) profile — unchanged  
✅ `elis-advisor` profile — unchanged  
✅ OpenClaw config (`/opt/elis/`) — unchanged  
✅ Discord routing/channel bindings — unchanged  
✅ GitHub — no writes  
✅ PE workflow — untouched  
✅ No `API_SERVER_ENABLED`  
✅ No `0.0.0.0` bindings  
✅ Memory not trimmed  
✅ No `hermes doctor --fix`

---

## 7. Rollback Commands

```bash
# Archive test task
hermes kanban archive t_c2fa7e98

# Delete pilot profiles (removes config, skills, wrapper scripts)
hermes profile delete elis-kanban-orch
hermes profile delete elis-kanban-worker-a
hermes profile delete elis-kanban-worker-b

# No config.yaml changes to revert — production profiles untouched
# No kanban.db changes to revert — task is archived, board returns to empty
```

---

## 8. Verdict

**PASS.** The Hermes Kanban infrastructure is fully operational on elis-server. The pilot demonstrated:

1. ✅ Profile creation with model/provider/toolsets
2. ✅ Task creation via CLI (`hermes kanban create`)
3. ✅ Automatic dispatch (13s latency within 60s interval)
4. ✅ Worker spawn with `HERMES_KANBAN_TASK` env
5. ✅ Worker heartbeat
6. ✅ Task completion with summary + metadata
7. ✅ Dashboard visibility (Kanban tab, board, card in Done column)
8. ✅ Zero impact to production profiles or PE workflow

The Kanban coordinator layer is ready for PO review. Next step per proposal scope: PO reviews dashboard, then approves production agent migration.

---

## 9. Token Budget

Pilot calls remained well under the 25k threshold. No TOKEN_OVERLOAD events observed.
