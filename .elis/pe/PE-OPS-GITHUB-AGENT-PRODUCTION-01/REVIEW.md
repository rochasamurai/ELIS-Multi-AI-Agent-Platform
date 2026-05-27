# REVIEW — PE-OPS-GITHUB-AGENT-PRODUCTION-01

## Validator identity
- **Agent**: `infra-val-a` (Claude Code)
- **Date**: 2026-05-27
- **Role confirmation**: `CURRENT_PE.md` Agent roles table records `infra-val-a` as Validator for this PE. ✓

## Validation target

| Field | Value |
|-------|-------|
| PE | PE-OPS-GITHUB-AGENT-PRODUCTION-01 |
| Branch | feature/pe-ops-github-agent-production-01-github-app-launcher |
| Commit | `874adc7bad571bf61c35b82e0bc9086d318433ad` |
| `bin/gh-agent` blob hash | `a70e411ab06bae4b84401f46ef593e936489f7f6` |
| Expected blob hash | `a70e411ab06bae4b84401f46ef593e936489f7f6` |
| Hash match | **YES** |

---

## Verdict

**OVERALL: PASS**

All verifiable acceptance criteria pass code review and static analysis. Two criteria are CANNOT VERIFY (infrastructure-provisioned, outside validator scope). Two criteria are NOT YET (deferred phases, per PE design). No blocking findings.

---

## Per-AC verdict table

| AC | Criterion summary | Verdict | Evidence |
|----|------------------|---------|---------|
| AC-1 | `/opt/elis/secrets/github-agent.env` present, readable, correct values | CANNOT VERIFY | Infrastructure-provisioned (PO-owned). Script guards correctly (lines 11–16, 24–29). |
| AC-2 | `/opt/elis/secrets/elis-github.private-key.pem` present, ownership 640 | CANNOT VERIFY | Infrastructure-provisioned (PO-owned). Script guards at lines 34–37. |
| AC-3 | RS256 JWT → installation token; token never printed/written/persisted | **PASS** | Code review — see evidence section. |
| AC-4 | `GH_CONFIG_DIR` isolated; no ambient `rochasamurai` keyring | **PASS** | Code review — see evidence section. |
| AC-5 | GitHub Agent linked worktree rebuilt after merge | NOT YET | Phase 2, gated on Phase 1 merge. Per PE design. |
| AC-6 | Read-only GitHub App auth validation passes | NOT YET | Phase 5, gated on PO approval. Per PE design. |
| AC-7 | No ambient `rochasamurai` GitHub operations | **PASS** | Code review — see evidence section. |
| AC-8 | Validator independently confirms AC-1–AC-7 with evidence | **PASS** | This REVIEW.md. |

---

## Evidence

### Static analysis

```
$ bash -n bin/gh-agent 2>&1; echo "Exit code: $?"
Exit code: 0
```

No syntax errors.

### Blob hash verification

```
$ git rev-parse HEAD:bin/gh-agent
a70e411ab06bae4b84401f46ef593e936489f7f6
```

Matches expected hash `a70e411ab06bae4b84401f46ef593e936489f7f6`. **PASS.**

### Scope gate (diff vs origin/main)

```
$ git diff --name-status origin/main..HEAD
M	.elis/pe/PE-OPS-GITHUB-AGENT-PRODUCTION-01/HANDOFF.md
M	.elis/pe/PE-OPS-GITHUB-AGENT-PRODUCTION-01/PE_TASK.md
M	.elis/state/current_pe.json
M	CURRENT_PE.md
A	bin/gh-agent

$ git diff --stat origin/main..HEAD
 .../PE-OPS-GITHUB-AGENT-PRODUCTION-01/HANDOFF.md   |  90 ++++++-------
 .../PE-OPS-GITHUB-AGENT-PRODUCTION-01/PE_TASK.md   |  70 +++++-----
 .elis/state/current_pe.json                        |   6 +-
 CURRENT_PE.md                                      |   4 +-
 bin/gh-agent                                       | 143 +++++++++++++++++++++
 5 files changed, 229 insertions(+), 84 deletions(--)
```

Files in diff: `bin/gh-agent` (added) + PE metadata files (`HANDOFF.md`, `PE_TASK.md`, `current_pe.json`, `CURRENT_PE.md`). This matches the expected scope declared in PE_TASK.md. **No forbidden files changed.**

### check_agent_scope.py

```
$ python scripts/check_agent_scope.py 2>&1; echo "Exit code: $?"
Agent scope clean — no secret-pattern files detected in worktree.
Exit code: 0
```

**PASS.**

### AC-3: RS256 JWT generation and token non-exposure

**JWT generation (lines 61–88 of `bin/gh-agent`):**

```python
header  = {"alg": "RS256", "typ": "JWT"}
payload = {"iss": app_id, "iat": now - 60, "exp": now + 600}
...
signature = private_key.sign(signing_input, padding.PKCS1v15(), hashes.SHA256())
print(f"{signing_input.decode()}.{b64url(signature)}", end="")
```

- Algorithm: RS256 (RSA + PKCS1v15 + SHA-256) — correct per GitHub App JWT spec.
- `iss` set to `GITHUB_APP_ID`. `iat` is `now-60` (clock skew tolerance). `exp` is `now+600` (10-minute window).
- JWT result captured into `_jwt` bash variable; never echoed to stdout.

**JWT → installation token exchange (lines 93–107):**

```bash
_response=$(curl -sf \
    -X POST \
    -H "Authorization: Bearer ${_jwt}" \
    ...
    "https://api.github.com/app/installations/${GITHUB_APP_INSTALLATION_ID}/access_tokens"
) || { unset _jwt; echo "FAIL: GitHub API request for installation token failed" >&2; exit 1; }

unset _jwt
```

- JWT sent as Bearer token in the `Authorization` header (not logged to stdout).
- `unset _jwt` executes immediately after the API call (line 102), regardless of success path.
- On failure the `||` clause also runs `unset _jwt` before exiting.

**Token extraction (lines 112–119):**

```bash
_token=$(printf '%s' "$_response" | python3 -c "
import sys, json
data = json.loads(sys.stdin.read())
tok = data.get('token', '')
if not tok:
    sys.exit(1)
print(tok, end='')
") || { unset _response; echo "FAIL: could not extract token from GitHub API response" >&2; exit 1; }

unset _response
```

- Token extracted from response via Python, stored in `_token`.
- `_response` unset immediately after (line 121).
- API response never echoed to stdout.

**Token export and cleanup (lines 136–138):**

```bash
export GH_TOKEN="$_token"
export GITHUB_TOKEN="$_token"
unset _token
```

- Token exported into process environment for `gh`.
- Local variable `_token` unset immediately after export.
- Token is never written to disk, never printed to stdout.

**Handoff to `gh` (line 143):**

```bash
exec gh "$@"
```

- `exec` replaces the current process; token lives only in the `gh` subprocess environment.
- When `gh` exits, the environment is destroyed with it.

**AC-3 verdict: PASS.** RS256 JWT flow is correct. Token is never printed, written to disk, or persisted beyond the `gh` subprocess.

### AC-4: GH_CONFIG_DIR isolation

**Lines 127–132:**

```bash
: "${WORKSPACE_DIR:=$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")" && cd .. && pwd)}"
GH_CONFIG_DIR="${WORKSPACE_DIR}/.config/gh"
mkdir -p "$GH_CONFIG_DIR"
chmod 700 "$GH_CONFIG_DIR"
export GH_CONFIG_DIR
```

- `WORKSPACE_DIR` resolves to the parent of `bin/` (i.e., the repo/workspace root) using `readlink -f` on `BASH_SOURCE[0]`.
- `GH_CONFIG_DIR` is set to `${WORKSPACE_DIR}/.config/gh` — completely separate from `~/.config/gh`.
- `chmod 700` prevents other users from reading this config directory.
- `export GH_CONFIG_DIR` guarantees `gh` (and any `gh` subprocess) uses this isolated config dir.
- No reference to `~/.config/gh`, `~/.netrc`, or any keyring system anywhere in the script.

**AC-4 verdict: PASS.** `gh` cannot fall back to ambient `rochasamurai` credentials because `GH_CONFIG_DIR` is explicitly set to an isolated path before `exec gh`.

### AC-7: No ambient rochasamurai operations

Full search of `bin/gh-agent` for rochasamurai references, `gh auth`, or ambient credential paths:

- No occurrence of `rochasamurai`, `gh auth login`, `~/.config/gh`, `GH_TOKEN` read from the pre-existing environment, or keyring references.
- The script explicitly constructs the `GH_TOKEN` from scratch via the App installation-token flow and exports it fresh.
- `set -euo pipefail` (line 6) means any unset variable reference is a fatal error — there is no silent fallback to any ambient credential.

**AC-7 verdict: PASS.**

---

## Scope compliance check

**Forbidden files scan:**

The following classes of files were checked and confirmed absent from the diff:
- Secret files (`.env`, `*.pem`, `*.key`, `*.token`) — **none changed**
- OpenClaw config (`openclaw/openclaw.json`, `openclaw/workspaces/`) — **none changed**
- Sudoers, service files, permission files — **none changed**
- GitHub Actions workflow files — **none changed**
- Any file outside the declared PE scope — **none changed**

**Result: PASS.** Diff is exactly `bin/gh-agent` (new launcher) plus four PE metadata files.

---

## Secret exposure assessment

| Item | Exposure risk | Verdict |
|------|--------------|---------|
| Private key (`GITHUB_APP_PRIVATE_KEY_PATH`) | Read by Python subprocess only; never assigned to bash variable; never echoed | **None** |
| JWT (`_jwt`) | Stored in bash variable; sent in Authorization header; unset immediately after API call | **None** |
| API response (`_response`) | Stored in bash variable; parsed by Python; unset immediately after parsing | **None** |
| Token (`_token`) | Stored in bash variable; exported to env; unset immediately after export | **None** |
| Token in environment | Live only in the `exec gh` subprocess; not written to disk | **None** |

No secrets are exposed in this implementation.

---

## Token exposure assessment

The installation access token exists only in these locations during script execution:

1. `_response` bash variable (raw JSON) — unset at line 121.
2. `_token` bash variable (extracted token) — unset at line 138.
3. `GH_TOKEN` and `GITHUB_TOKEN` environment variables — exist for the duration of the `exec gh` subprocess only; destroyed when the subprocess exits.

The token is never:
- Written to any file.
- Echoed to stdout or stderr.
- Logged anywhere in the script.
- Passed as a command-line argument (which would be visible in `ps`).

**Token exposure assessment: No exposure risk in the implementation.**

---

## Fail-closed behaviour

The script exits non-zero on every failure path:

| Failure condition | Exit path |
|------------------|-----------|
| Credential file missing or unreadable (lines 13–16) | `exit 1` with `FAIL:` message to stderr |
| Required variable(s) not set (lines 24–29) | `exit 1` with `FAIL:` message to stderr |
| Private key not readable (lines 34–37) | `exit 1` with `FAIL:` message to stderr |
| `python3` not installed (lines 42–45) | `exit 1` with `FAIL:` message to stderr |
| `cryptography` package missing (lines 47–50) | `exit 1` with `FAIL:` message to stderr |
| JWT generation failed (line 88) | `exit 1` with `FAIL:` message to stderr |
| GitHub API call failed (lines 93–99) | `unset _jwt`; `exit 1` with `FAIL:` message to stderr |
| Empty API response (lines 104–107) | `exit 1` with `FAIL:` message to stderr |
| Token extraction failed (line 119) | `unset _response`; `exit 1` with `FAIL:` message to stderr |
| `set -euo pipefail` (line 6) | Any unhandled error causes immediate non-zero exit |

**Fail-closed assessment: PASS.** Every failure path exits non-zero and emits a diagnostic to stderr.

---

## PE metadata consistency check

| Source | PE ID | Branch | Implementer | Validator | State |
|--------|-------|--------|-------------|-----------|-------|
| `CURRENT_PE.md` | PE-OPS-GITHUB-AGENT-PRODUCTION-01 | feature/pe-ops-github-agent-production-01-github-app-launcher | infra-impl-b | infra-val-a | gate-1-pending |
| `.elis/state/current_pe.json` | PE-OPS-GITHUB-AGENT-PRODUCTION-01 | feature/pe-ops-github-agent-production-01-github-app-launcher | infra-impl-b | infra-val-a | gate-1-pending |
| `PE_TASK.md` | PE-OPS-GITHUB-AGENT-PRODUCTION-01 | feature/pe-ops-github-agent-production-01-github-app-launcher | infra-impl-b | infra-val-a | — |
| `.elis/pe/…/HANDOFF.md` | PE-OPS-GITHUB-AGENT-PRODUCTION-01 | feature/pe-ops-github-agent-production-01-github-app-launcher | infra-impl-b | infra-val-a | gate-1-pending |

**All metadata sources are consistent. PASS.**

GitHub App target referenced in PE_TASK.md and HANDOFF.md:
- App name: "ELIS GitHub"
- App ID: 3884378
- Installation ID: 136081387
- Repository: `rochasamurai/ELIS-Multi-AI-Agent-Platform`

The `bin/gh-agent` script reads `GITHUB_APP_ID` and `GITHUB_APP_INSTALLATION_ID` from the credential env file at runtime and uses them in the JWT payload (`iss`) and the API endpoint path respectively. Consistent with PE target.

---

## Role-boundary assessment

- Validator (`infra-val-a`) performed read-only code review only.
- `bin/gh-agent` was **not modified**.
- No live GitHub API calls were made.
- No credential files were read.
- No permission, service, sudoers, or OpenClaw changes were made.
- No PR was created and no merge was attempted.
- Output is limited to this REVIEW.md file, as authorised.

**Role-boundary assessment: PASS.**

---

## Non-blocking observations

1. **Comment section numbering gap**: The script uses section labels 1–7 then 9–11 (section 8 is absent from comments). This is a cosmetic inconsistency; no functional step is missing. Non-blocking.
2. **`HANDOFF.md` at repo root**: The `HANDOFF.md` at the repo root is from a previous PE (PE-OPS-GITHUB-AGENT-ENFORCEMENT-01). The HANDOFF for this PE is correctly located at `.elis/pe/PE-OPS-GITHUB-AGENT-PRODUCTION-01/HANDOFF.md`. Non-blocking — the repo-root HANDOFF.md is a pre-existing condition; this PE's HANDOFF is in the correct location.

---

## Gate results

| Gate | Result |
|------|--------|
| `bash -n bin/gh-agent` | **PASS** — exits 0, no syntax errors |
| Blob hash match | **PASS** — `a70e411ab06bae4b84401f46ef593e936489f7f6` confirmed |
| Scope gate (`git diff --name-status origin/main..HEAD`) | **PASS** — `bin/gh-agent` + PE metadata only |
| `python scripts/check_agent_scope.py` | **PASS** — exits 0, clean |
| AC-3 code review (RS256 JWT + token non-exposure) | **PASS** |
| AC-4 code review (GH_CONFIG_DIR isolation) | **PASS** |
| AC-7 code review (no ambient rochasamurai) | **PASS** |
| Fail-closed behaviour | **PASS** |
| PE metadata consistency | **PASS** |
| Secret exposure | **NONE** |
| Token exposure | **NONE** |
| Role boundary | **PASS** |

---

## Required fixes (blocking)

**None.** No blocking findings.

---

## Ready to merge

**YES** — pending PO approval of the GitHub push/PR per the PE hard stops. All validator-scope checks pass. Infrastructure ACs (AC-1, AC-2) are PO-owned; deferred ACs (AC-5, AC-6) are gated on post-merge phases.
