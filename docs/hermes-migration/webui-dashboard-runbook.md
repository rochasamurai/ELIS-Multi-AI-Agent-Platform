# Hermes WebUI Dashboard Runbook

**PE:** PE-OPS-HERMES-WEBUI-PILOT-01  
**Status:** Deployed and validated  
**Date:** 2026-06-05

---

## Access

| Property | Value |
|---|---|
| URL | `http://100.84.95.38:9119` |
| Network | Tailscale only (100.84.95.38 is the Tailscale IP of elis-server) |
| Authentication | None — Tailscale mesh provides network-layer auth |
| TLS | None — Tailscale WireGuard encryption is trusted for this pilot |

## Binding Rules

- **Bind:** `100.84.95.38:9119` (Tailscale IP only)
- **Never bind:** `0.0.0.0` or any public interface
- **API_SERVER_ENABLED:** Must remain unset/disabled
- No public internet exposure is permitted

## Startup

### Quick start (Tailscale, headless)

```bash
hermes dashboard --host 100.84.95.38 --port 9119 --insecure --no-open
```

Flags:
- `--host 100.84.95.38` — Tailscale IP only
- `--port 9119` — default
- `--insecure` — required for non-localhost binding
- `--no-open` — no browser on headless server

### Pre-build for faster startup

First launch runs `npm ci` + build in `~/.hermes/hermes-agent/web/`. On elis-server (i7-8559U, 15 GiB) this takes 3–5 minutes with no visible output. Pre-build once:

```bash
cd ~/.hermes/hermes-agent/web
npm ci          # one-time, 3–5 minutes
npm run build   # produces dist/

# Then skip build on subsequent launches:
hermes dashboard --host 100.84.95.38 --port 9119 --insecure --no-open --skip-build
```

## Runtime Management

```bash
hermes dashboard --status    # list running dashboard processes
hermes dashboard --stop      # stop all running dashboards
```

## Rebuild Rule

When the WebUI requires rebuilding (Hermes update, plugin change, or UI regression):

1. Stop dashboard: `hermes dashboard --stop`
2. Rebuild: `cd ~/.hermes/hermes-agent/web && npm ci && npm run build`
3. Restart: `hermes dashboard --host 100.84.95.38 --port 9119 --insecure --no-open --skip-build`

Do not rely on auto-rebuild at startup for production restarts — pre-build manually.

## Kanban Tab

The Kanban dashboard tab is always present (reads `kanban.db` directly). It does not depend on the dispatcher being active. An empty board is expected when no tasks exist — this is not a deployment failure.

## Verification

From a Tailscale-connected machine:
```bash
curl -s -o /dev/null -w "%{http_code}" http://100.84.95.38:9119/
# Expect: 200
```

On elis-server:
```bash
ss -ltnp | grep 9119
# Expect: LISTEN on 100.84.95.38:9119 (NOT 0.0.0.0)
```
