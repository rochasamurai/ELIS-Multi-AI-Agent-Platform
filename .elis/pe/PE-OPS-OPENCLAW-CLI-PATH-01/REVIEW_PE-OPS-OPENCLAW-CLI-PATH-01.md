# REVIEW — PE-OPS-OPENCLAW-CLI-PATH-01

> Validator slot: infra-val-a
> Generated: 2026-06-01

## PE Identification

- **PE:** PE-OPS-OPENCLAW-CLI-PATH-01
- **Branch:** feature/pe-ops-openclaw-cli-path-01-fix-openclaw-binary-path-resolution
- **Base:** main
- **Implementer slot:** infra-impl-b
- **Validator slot:** infra-val-a

## HANDOFF Completeness

All required sections present: YES

Sections confirmed:
- PE Identification ✓
- Gate 1 Diagnosis Evidence (SYSTEMD_USER_UNIT_PATH_PRECEDENCE) ✓
- Gate 2 Supervisor Fix Evidence (PASS) ✓
- Evidence Discrepancy Reconciliation (PRE_EXISTING_CORRECTION_BEFORE_SUPERVISOR_CHECK, mtime 2026-05-31 23:40:40) ✓
- PM_ROLE_DISCOVERY_ERROR (PM_ROLE_DISCOVERY_ERROR_OPENCLAW_AGENT_LIST_IS_NOT_ELIS_ROLE_REGISTRY) ✓
- Acceptance Criteria Checklist (all items checked) ✓
- Validator Instructions ✓

## Scope Verification

Prohibited mutation checks:

| Check | Result |
|---|---|
| openclaw.json edited by this PE | NOT EDITED (file present, unmodified by PE scope) |
| Hermes config edited | NOT EDITED |
| /opt/elis/a2a/.enabled created | ABSENT |
| /opt/openclaw/bin/openclaw replaced | NOT REPLACED (bash wrapper, unchanged) |
| Gate 2B touched | NOT TOUCHED |

## Evidence

### Gateway PATH check

```
$ which openclaw
/opt/openclaw/tools/node-v22.22.0/bin/openclaw

$ openclaw --version
OpenClaw 2026.4.21 (f788c88)
```

Expected: `/opt/openclaw/bin/openclaw`, v2026.5.27
Actual: `/opt/openclaw/tools/node-v22.22.0/bin/openclaw`, v2026.4.21
Result: FAIL

### Root cause of PATH check failure

Systemd drop-in file overrides the main service file PATH:

Path: `/home/samurai/.config/systemd/user/openclaw-gateway.service.d/10-path.conf`

Content:
```
[Service]
Environment=PATH=/home/samurai/.local/bin:/home/samurai/.npm-global/bin:/home/samurai/bin:/home/samurai/.volta/bin:/home/samurai/.asdf/shims:/home/samurai/.bun/bin:/home/samurai/.nvm/current/bin:/home/samurai/.fnm/current/bin:/home/samurai/.local/share/pnpm:/usr/local/bin:/usr/bin:/bin
```

In systemd, drop-in files (`*.conf` in the `.service.d/` directory) are applied AFTER the main unit file. The Supervisor's Gate 2 fix prepended `/opt/openclaw/bin` in the main service file's `Environment=PATH=` directive. However, the drop-in `10-path.conf` overwrites `PATH` entirely (without `/opt/openclaw/bin`), so the running gateway inherited the drop-in PATH, not the fixed main-file PATH.

Running gateway PID 141458 environment PATH (confirmed via `/proc/141458/environ`):

```
PATH=/home/samurai/.local/bin:/home/samurai/.npm-global/bin:/home/samurai/bin:/home/samurai/.volta/bin:/home/samurai/.asdf/shims:/home/samurai/.bun/bin:/home/samurai/.nvm/current/bin:/home/samurai/.fnm/current/bin:/home/samurai/.local/share/pnpm:/usr/local/bin:/usr/bin:/bin
```

`/opt/openclaw/bin` is absent from the running process PATH.

### Required additional fix

The drop-in file must be updated to prepend `/opt/openclaw/bin`:

```
[Service]
Environment=PATH=/opt/openclaw/bin:/home/samurai/.local/bin:/home/samurai/.npm-global/bin:/home/samurai/bin:/home/samurai/.volta/bin:/home/samurai/.asdf/shims:/home/samurai/.bun/bin:/home/samurai/.nvm/current/bin:/home/samurai/.fnm/current/bin:/home/samurai/.local/share/pnpm:/usr/local/bin:/usr/bin:/bin
```

After this change: `systemctl --user daemon-reload && systemctl --user restart openclaw-gateway` required. Then re-run `which openclaw` and `openclaw --version` to confirm fix.

## Verdict

FAIL — gateway PATH fix incomplete. Drop-in `10-path.conf` overrides the main service file `PATH` without `/opt/openclaw/bin`. Additional Supervisor action required: update drop-in and restart gateway.