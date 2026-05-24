# PE-OPS-DISPATCH-PATH-REPAIR-01 — PE Task

## Objective
Repair deterministic PM dispatch path reliability without changing runtime/configuration behaviour.

## Current branch and HEAD
- Branch: `feature/pe-ops-dispatch-path-repair-01-deterministic-pm-dispatch-reliability`
- HEAD: `19cf0c9de707bbfdb562c265695c7ec4b7d4c138`

## Implementation scope
- `scripts/check_dispatch_binding.py`
- `tests/test_check_dispatch_binding.py`

## Validation scope
- Targeted Python tests for dispatch binding guards
- Validator binding check from `/opt/elis/agent-worktrees/infra-val-a`
- No config changes, no service restarts, no dispatch actions

## Hard stops
- Do not change `CURRENT_PE.md`
- Do not change config
- Do not restart or reload services
- Do not run `sessions_spawn`
- Do not run `sessions_send`
- Do not open a PR
- Do not merge
- Do not resume PM execution

## Notes
This artefact is added because the PE repair branch lacked the canonical `PE_TASK.md` required by dispatch binding checks.
