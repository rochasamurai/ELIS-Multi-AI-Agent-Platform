# REVIEW — PE-OPS-A2A-PRODUCTION-02 — Gate 2A

> Canonical path: `.elis/pe/PE-OPS-A2A-PRODUCTION-02/REVIEW_PE-OPS-A2A-PRODUCTION-02.md`
> Validator surface: `infra-val-b`
> Gate: 2A — code + test + ELIS runtime workspace directory creation
> Date: 2026-05-30

---

## DISPATCH_PROVENANCE_PROOF_V1

```
DISPATCH_PROVENANCE_PROOF_V1
requested_agent_id:          infra-val-b
actual_agent_id:             infra-val-b
actual_session_id:           agent:infra-val-b:subagent:c522ad29-f236-46ae-b34e-22aa099d9346
actual_cwd:                  /opt/elis/agent-worktrees/infra-val-b
actual_worktree:             /opt/elis/agent-worktrees/infra-val-b
branch:                      detached HEAD — commit d43b7dbeca6307d287255d1edc9a973b6e9df9d4
head:                        d43b7dbeca6307d287255d1edc9a973b6e9df9d4
git_identity:                infra-val-b / infra-val-b@openclaw.local
model_provider_profile:      claude-cli/claude-sonnet-4-6
dispatch_method:             sessions_spawn.agentId
openclaw_config_agent_match: PASS (actual_worktree /opt/elis/agent-worktrees/infra-val-b matches openclaw.json workspace for infra-val-b)
acp_command_not_used:        PASS
pm_worktree_not_used:        PASS (actual_worktree != /opt/elis/agent-worktrees/pm)
dispatch_timestamp:          2026-05-30T19:39:00+01:00
```

All three boolean fields: PASS. Validation proceeds.

---

## Step 0 — Fixed Workspace Binding Certificate

### Evidence

```
$ pwd
/opt/elis/agent-worktrees/infra-val-b

$ git rev-parse HEAD
d43b7dbeca6307d287255d1edc9a973b6e9df9d4

$ git status -sb
## HEAD (no branch)

$ git config --worktree user.name
infra-val-b

$ git config --worktree user.email
infra-val-b@openclaw.local
```

Working directory is confirmed as `/opt/elis/agent-worktrees/infra-val-b`. HEAD matches the Gate 2A commit. Tree is clean. Identity is `infra-val-b`.

---

## Step 1 — Role Confirmation

CURRENT_PE.md confirms:

| Field | Value |
|-------|-------|
| PE | PE-OPS-A2A-PRODUCTION-02 |
| Implementer | infra-impl-a |
| Validator | infra-val-b |

This session is running as `infra-val-b`. Role assignment matches. Proceeding.

---

## Step 2 — Validation Evidence

### 2.1 — Scope Gate

#### Evidence

```
$ git diff --name-status 2217d4e784c34ee302624a1e1707ed490a222f09..d43b7dbeca6307d287255d1edc9a973b6e9df9d4
M       .elis/pe/PE-OPS-A2A-PRODUCTION-02/HANDOFF.md
M       scripts/a2a_local_transport.py
M       tests/test_a2a_local_transport.py
```

Exactly three files. All are expected:
- `.elis/pe/PE-OPS-A2A-PRODUCTION-02/HANDOFF.md` — Implementer deliverable ✓
- `scripts/a2a_local_transport.py` — approved implementation file ✓
- `tests/test_a2a_local_transport.py` — approved implementation file ✓

No unrelated files. **PASS.**

---

### 2.2 — No PE-OPS-A2A-PRODUCTION-01 commit reuse

#### Evidence

```
$ git log 2217d4e784c34ee302624a1e1707ed490a222f09..d43b7dbeca6307d287255d1edc9a973b6e9df9d4 --oneline
d43b7dbe feat(PE-OPS-A2A-PRODUCTION-02): Gate 2A — production mailbox structure, disabled sentinel, Phase 1 agent tests
```

Exactly one commit. No cherry-picks from PE-OPS-A2A-PRODUCTION-01. Commit message contains the correct PE ID. **PASS.**

---

### 2.3 — scripts/a2a_local_transport.py code review

#### Evidence

Full file read at `/opt/elis/agent-worktrees/infra-val-b/scripts/a2a_local_transport.py`.

**A. Constants (lines 33–35):**

```python
_A2A_RUNTIME_ROOT = Path("/opt/elis/a2a")
_MAILBOX_ROOT = _A2A_RUNTIME_ROOT / "mailboxes"
_ENABLED_SENTINEL = _A2A_RUNTIME_ROOT / ".enabled"
```

- `_A2A_RUNTIME_ROOT = Path("/opt/elis/a2a")` — PRESENT ✓
- `_MAILBOX_ROOT = _A2A_RUNTIME_ROOT / "mailboxes"` — PRESENT (correct path) ✓
- `_ENABLED_SENTINEL = _A2A_RUNTIME_ROOT / ".enabled"` — PRESENT ✓

**FAIL — stale `/tmp/elis_a2a` reference in module docstring:**

```
Line 17:   - Mailbox root: /tmp/elis_a2a/
```

The module-level docstring at line 17 still references the old `/tmp/elis_a2a/` path. The acceptance criterion explicitly states: "`/tmp/elis_a2a` does NOT appear anywhere in the file." The string appears in the module docstring. The actual constants are correct; this is stale documentation that was not updated during the migration. **FAIL on this sub-criterion.**

```
$ grep -n "tmp/elis_a2a" scripts/a2a_local_transport.py
17:  - Mailbox root: /tmp/elis_a2a/
```

**B. A2ATransportDisabledError (lines 38–39):**

```python
class A2ATransportDisabledError(RuntimeError):
    """Raised when the ELIS A2A transport is used before it has been enabled."""
```

- Subclass of `RuntimeError` ✓
- Docstring describes disabled transport error ✓
- **PASS.**

**C. A2ATransport.__init__ (lines 155–166):**

```python
def __init__(
    self,
    mailbox_root: Path = _MAILBOX_ROOT,
    *,
    skip_enabled_check: bool = False,
) -> None:
    self._root = Path(mailbox_root)
    if not skip_enabled_check and not _ENABLED_SENTINEL.exists():
        raise A2ATransportDisabledError(
            f"ELIS A2A transport is disabled. "
            f"Enable marker not found: {_ENABLED_SENTINEL}"
        )
```

- `skip_enabled_check: bool = False` keyword-only parameter ✓
- Checks `_ENABLED_SENTINEL.exists()` when not skipped ✓
- Raises `A2ATransportDisabledError` when absent and not skipped ✓
- **PASS.**

**D. _mailbox() method (lines 168–173):**

```python
def _mailbox(self, recipient: str) -> Path:
    inbox = self._root / recipient / "inbox"
    inbox.mkdir(parents=True, exist_ok=True)
    (self._root / recipient / "processed").mkdir(parents=True, exist_ok=True)
    (self._root / recipient / "dead").mkdir(parents=True, exist_ok=True)
    return inbox
```

- Creates `inbox/`, `processed/`, `dead/` subdirectories ✓
- Returns `inbox` path ✓
- **PASS.**

**E. receive() method (lines 188–209):**

```python
def receive(self, recipient: str) -> list[A2AMessage]:
    inbox = self._root / recipient / "inbox"
    ...
    for path in sorted(inbox.iterdir()):
        try:
            ...
            path.rename(processed / path.name)   # success → processed/
        except (json.JSONDecodeError, KeyError):
            path.rename(dead / path.name)         # corrupt → dead/
```

- Reads from `inbox/` ✓
- Moves successfully parsed files to `processed/` ✓
- Moves corrupt/unparseable files to `dead/` (not silently deleted) ✓
- **PASS.**

**F. list_messages() method (lines 212–228):**

```python
def list_messages(self, recipient: str) -> list[A2AMessage]:
    inbox = self._root / recipient / "inbox"
    if not inbox.is_dir():
        return []
    ...
    for path in sorted(inbox.iterdir()):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            messages.append(A2AMessage.from_dict(data))
        except (json.JSONDecodeError, KeyError):
            pass
    return messages
```

- Reads from `inbox/` only ✓
- Non-destructive (no moves) ✓
- **PASS.**

---

### 2.4 — tests/test_a2a_local_transport.py review

#### Evidence

Full file read at `/opt/elis/agent-worktrees/infra-val-b/tests/test_a2a_local_transport.py`.

**A. `transport` fixture (lines 36–38):**

```python
@pytest.fixture()
def transport(tmp_path):
    """Return an A2ATransport backed by a temporary directory (sentinel check bypassed)."""
    return A2ATransport(mailbox_root=tmp_path, skip_enabled_check=True)
```

- Uses `skip_enabled_check=True` ✓
- Docstring documents this as a test-only bypass ("sentinel check bypassed") ✓
- **PASS.**

**B. TestGate2AEnabledSentinel (lines 390–411):**

```python
class TestGate2AEnabledSentinel:
    def test_transport_raises_when_sentinel_absent(self, tmp_path): ...
    def test_transport_succeeds_when_sentinel_present(self, tmp_path): ...
    def test_skip_enabled_check_bypasses_sentinel(self, tmp_path): ...
```

All three required tests present. **PASS.**

**C. TestGate2AMailboxStructure (lines 419–465):**

```python
class TestGate2AMailboxStructure:
    def test_send_writes_to_inbox(self, transport, tmp_path): ...
    def test_receive_moves_to_processed(self, transport, tmp_path): ...
    def test_corrupt_file_moves_to_dead(self, transport, tmp_path): ...
    def test_list_messages_reads_inbox_only(self, transport, tmp_path): ...
    def test_dead_dir_created_on_first_receive(self, transport, tmp_path): ...
```

All four required tests present (plus one additional: `test_dead_dir_created_on_first_receive`). **PASS.**

**D. TestGate2APhase1AgentIds (lines 471–488):**

```python
PHASE_1_AGENTS = ["pm", "infra-impl-a", "infra-impl-b", "infra-val-a", "infra-val-b"]

class TestGate2APhase1AgentIds:
    @pytest.mark.parametrize("recipient", PHASE_1_AGENTS)
    def test_send_receive_for_phase1_agent(self, transport, recipient): ...
```

Parametrised over all five Phase 1 ELIS agent IDs. **PASS.**

---

### 2.5 — Full test suite run

#### Evidence

```
$ cd /opt/elis/agent-worktrees/infra-val-b
$ python -m pytest tests/test_a2a_local_transport.py -v 2>&1

============================= test session starts ==============================
platform linux -- Python 3.12.3, pytest-9.0.3, pluggy-1.6.0
rootdir: /opt/elis/agent-worktrees/infra-val-b
configfile: pyproject.toml
collected 43 items

tests/test_a2a_local_transport.py ...................................... [ 88%]
.....                                                                    [100%]

============================== 43 passed in 0.17s ==============================
```

**43 passed, 0 failed. PASS.**

---

### 2.6 — Sentinel absent verification

#### Evidence

```
$ python -c "
import sys; sys.path.insert(0, 'scripts')
from a2a_local_transport import A2ATransport, A2ATransportDisabledError
try:
    A2ATransport()
    print('FAIL: no exception raised')
except A2ATransportDisabledError as e:
    print(f'PASS: A2ATransportDisabledError raised: {e}')
"

PASS: A2ATransportDisabledError raised: ELIS A2A transport is disabled. Enable marker not found: /opt/elis/a2a/.enabled
```

Default constructor raises `A2ATransportDisabledError` when sentinel is absent. **PASS.**

---

### 2.7 — ELIS runtime workspace verification

#### Evidence

```
$ ls -la /opt/elis/a2a/
total 16
drwxr-x---  4 samurai samurai 4096 May 30 19:29 .
drwxr-xr-x 13 samurai samurai 4096 May 30 19:29 ..
drwxr-x---  2 samurai samurai 4096 May 30 19:29 logs
drwxr-x---  7 samurai samurai 4096 May 30 19:29 mailboxes

$ ls -la /opt/elis/a2a/mailboxes/
total 28
drwxr-x--- 7 samurai samurai 4096 May 30 19:29 .
drwxr-x--- 4 samurai samurai 4096 May 30 19:29 ..
drwxr-x--- 5 samurai samurai 4096 May 30 19:29 infra-impl-a
drwxr-x--- 5 samurai samurai 4096 May 30 19:29 infra-impl-b
drwxr-x--- 5 samurai samurai 4096 May 30 19:29 infra-val-a
drwxr-x--- 5 samurai samurai 4096 May 30 19:29 infra-val-b
drwxr-x--- 5 samurai samurai 4096 May 30 19:29 pm

$ stat /opt/elis/a2a/
  File: /opt/elis/a2a/
  Size: 4096      Blocks: 8          IO Block: 4096   directory
  Access: (0750/drwxr-x---)  Uid: ( 1000/ samurai)   Gid: ( 1000/ samurai)

$ for agent in pm infra-impl-a infra-impl-b infra-val-a infra-val-b; do
    echo "=== $agent ==="; ls /opt/elis/a2a/mailboxes/$agent/
  done
=== pm ===
dead    inbox   processed
=== infra-impl-a ===
dead    inbox   processed
=== infra-impl-b ===
dead    inbox   processed
=== infra-val-a ===
dead    inbox   processed
=== infra-val-b ===
dead    inbox   processed

$ ls /opt/elis/a2a/.enabled 2>&1 || echo "PASS: .enabled absent"
ls: cannot access '/opt/elis/a2a/.enabled': No such file or directory
PASS: .enabled absent
```

Verification:
- `/opt/elis/a2a/` exists ✓
- Owner: `samurai`, group: `samurai`, mode: `0750` (`drwxr-x---`) ✓
- `/opt/elis/a2a/mailboxes/` exists ✓
- `/opt/elis/a2a/logs/` exists ✓
- Phase 1 agent mailboxes only: `pm`, `infra-impl-a`, `infra-impl-b`, `infra-val-a`, `infra-val-b` ✓
- No SLR agents, no `github-agent`, no `prog-*` agents present ✓
- Each ELIS agent mailbox has `inbox/`, `processed/`, `dead/` ✓
- `/opt/elis/a2a/.enabled` does NOT exist ✓

**PASS.**

---

### 2.8 — OpenClaw/Hermes config unchanged verification

#### Evidence

```
$ stat /home/samurai/.openclaw/openclaw.json
  File: /home/samurai/.openclaw/openclaw.json
  Size: 10320     Blocks: 24         IO Block: 4096   regular file
  Access: (0600/-rw-------)  Uid: ( 1000/ samurai)   Gid: ( 1000/ samurai)
  Modify: 2026-05-30 14:09:25.510036331 +0100

$ python3 -c "
import json
with open('/home/samurai/.openclaw/openclaw.json') as f:
    cfg = json.load(f)
print('a2a in gateway:', 'a2a' in str(cfg.get('gateway', {})))
print('a2a_enabled in config:', any('a2a' in str(v).lower() and 'enabled' in str(v).lower() for v in cfg.values()))
"
a2a in gateway: False
a2a_enabled in config: False
```

- File was last modified at 14:09 on 2026-05-30, which is before the Implementer's Gate 2A dispatch timestamp (19:27+01:00). The modification was not caused by Gate 2A implementation work.
- No A2A routing keys present in gateway config ✓
- No `a2a_enabled` configuration present ✓

OBSERVATION: The openclaw.json modification at 14:09 today predates Gate 2A — consistent with PM dispatch setup operations, not Implementer config mutation.

Live openclaw.json workspace bindings confirmed via inspection:
- `infra-impl-a` → workspace `/opt/elis/agent-worktrees/infra-impl-a`, model `openrouter/qwen/qwen3-coder-flash`
- `infra-val-b` → workspace `/opt/elis/agent-worktrees/infra-val-b`, model `openrouter/z-ai/glm-5.1`

**No A2A routing added. PASS.**

OBSERVATION (model discrepancy): The Implementer's HANDOFF DISPATCH_PROVENANCE_PROOF_V1 reports `model_provider_profile: claude-cli/claude-sonnet-4-6`, but the live openclaw.json configures `infra-impl-a` with `openrouter/qwen/qwen3-coder-flash`. The `openclaw_config_agent_match` field in the PE_TASK.md definition checks workspace binding (not model) — workspace binding is correct, so the boolean PASS stands. The model discrepancy is unexplained and should be acknowledged by PM. It does not constitute a hard stop under the defined proof schema.

---

### 2.9 — ELIS-first terminology check (HANDOFF.md)

#### Evidence

HANDOFF.md read from `.elis/pe/PE-OPS-A2A-PRODUCTION-02/HANDOFF.md`.

Selected passages confirming ELIS-first terminology:
- "Gate 2A implements the production mailbox structure, enabled-sentinel disabled-by-default guard, and Phase 1 ELIS agent identity smoke round-trips."
- "ELIS Runtime Workspace Directories Created"
- "ELIS-First Naming Confirmation — All terminology in this HANDOFF and in the code changes uses ELIS-first naming conventions."
- "OpenClaw" appears only as concrete implementation identifiers: `~/.openclaw/openclaw.json`, `mcp__openclaw__sessions_spawn` (referenced in dispatch constraints)
- No "Claude Code", no "CODEX", no "slot-a", no "slot-b" found

Implementer surface referred to by role name (`infra-impl-a`) not engine name. **PASS.**

---

## Findings

| ID | Check | Result | Detail |
|----|-------|--------|--------|
| F-01 | Scope gate — 3 files only | PASS | Exactly HANDOFF.md, a2a_local_transport.py, test_a2a_local_transport.py |
| F-02 | Single commit, no PE-PROD-01 cherry-picks | PASS | One commit: d43b7dbe |
| F-03 | Constants: `_A2A_RUNTIME_ROOT`, `_MAILBOX_ROOT`, `_ENABLED_SENTINEL` | PASS | All three present and correct at lines 33–35 |
| F-04 | `/tmp/elis_a2a` absent from file | **FAIL** | Appears at line 17 of module docstring: `- Mailbox root: /tmp/elis_a2a/`. Stale documentation not updated during migration. Actual constants are correct. |
| F-05 | `A2ATransportDisabledError` class | PASS | Present, subclass of RuntimeError, has docstring |
| F-06 | `__init__` sentinel check | PASS | `skip_enabled_check` kwarg, sentinel check, raises correct exception |
| F-07 | `_mailbox()` creates inbox/processed/dead | PASS | All three subdirectories created |
| F-08 | `receive()` inbox → processed / dead | PASS | Correct routing for success and corrupt files |
| F-09 | `list_messages()` reads inbox only | PASS | Non-destructive, inbox only |
| F-10 | `transport` fixture uses `skip_enabled_check=True` | PASS | Documented as bypass in fixture docstring |
| F-11 | `TestGate2AEnabledSentinel` — 3 tests | PASS | All three present and correct |
| F-12 | `TestGate2AMailboxStructure` — 4 required tests | PASS | All four present (plus one additional) |
| F-13 | `TestGate2APhase1AgentIds` — 5 agent IDs parametrised | PASS | pm, infra-impl-a, infra-impl-b, infra-val-a, infra-val-b |
| F-14 | Full test suite: 43 tests pass | PASS | 43 passed, 0 failed |
| F-15 | Sentinel absent raises `A2ATransportDisabledError` | PASS | Verified by live execution |
| F-16 | ELIS runtime workspace structure and permissions | PASS | /opt/elis/a2a/ with correct owner/mode/subdirs |
| F-17 | Phase 1 agent mailboxes only | PASS | pm, infra-impl-a, infra-impl-b, infra-val-a, infra-val-b only |
| F-18 | `.enabled` sentinel absent | PASS | Not created — A2A remains disabled |
| F-19 | OpenClaw config — no A2A routing added | PASS | No a2a keys in gateway config |
| F-20 | HANDOFF.md ELIS-first terminology | PASS | Correct ELIS naming throughout |
| OBS-01 | openclaw.json modified at 14:09 today | OBSERVATION | Predates Gate 2A (19:27); consistent with PM dispatch setup; no A2A keys added |
| OBS-02 | Implementer model discrepancy | OBSERVATION | HANDOFF reports `claude-cli/claude-sonnet-4-6`; live config shows `openrouter/qwen/qwen3-coder-flash` for infra-impl-a. Workspace binding is correct (boolean PASS). Model used at runtime is unexplained. PM should acknowledge. |

---

## Verdict

**F-04 is the sole FAIL**: the string `/tmp/elis_a2a` appears at line 17 of the module docstring in `scripts/a2a_local_transport.py`. The acceptance criterion explicitly states this string must not appear anywhere in the file. The actual constants and all runtime behaviour are correct; this is a documentation-only defect.

All other checks: PASS. Test suite: 43/43. Runtime workspace: correct structure, permissions, sentinel absent. Hard stops: all confirmed.

Given that the defect is confined to a module docstring (not executable code), all tests pass, and runtime behaviour is correct, a CONDITIONAL_PASS is appropriate.

### Condition for PASS upgrade

The `infra-impl-a` surface must update line 17 of `scripts/a2a_local_transport.py` to replace the stale `- Mailbox root: /tmp/elis_a2a/` line with the correct path (`/opt/elis/a2a/mailboxes/`) or remove it. The fix must be committed to the PE branch and verified by a fresh scope gate check.

### Verdict

```
CONDITIONAL_PASS
```

Condition: update stale `/tmp/elis_a2a` reference in module docstring (line 17 of `scripts/a2a_local_transport.py`) before Gate 2B proceeds.

Gate 2B readiness: **HOLD** — pending condition resolution.
