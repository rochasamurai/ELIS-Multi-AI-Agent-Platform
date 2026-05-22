#!/usr/bin/env python3
"""check_dispatch_binding.py — validate PE dispatch binding preconditions.

Verifies the agent worktree is on the correct branch, at the expected HEAD,
and has no tracked dirty files. Supports failure-class classification for
blocked dispatch scenarios.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

AGENT_WORKTREE_MAP = {
    "pm": "/opt/elis/agent-worktrees/pm",
    "infra-impl-a": "/opt/elis/agent-worktrees/infra-impl-a",
    "infra-impl-b": "/opt/elis/agent-worktrees/infra-impl-b",
    "infra-val-a": "/opt/elis/agent-worktrees/infra-val-a",
    "infra-val-b": "/opt/elis/agent-worktrees/infra-val-b",
    "github-agent": "/opt/elis/agent-worktrees/github-agent",
    "infra-impl-claude": "/opt/elis/agent-worktrees/infra-impl-b",
    "infra-val-claude": "/opt/elis/agent-worktrees/infra-val-a",
    "infra-impl-codex": "/opt/elis/agent-worktrees/infra-impl-a",
    "infra-val-codex": "/opt/elis/agent-worktrees/infra-val-b",
    "advisor": "/opt/elis/agent-worktrees/advisor",
}

_PRESERVED_CONTEXT_FILES = {
    "AGENTS.md",
    "HEARTBEAT.md",
    "IDENTITY.md",
    "SOUL.md",
    "TOOLS.md",
    "USER.md",
}

# Failure-class taxonomy for dispatch blocking scenarios
FAILURE_CLASSES = {
    "DISPATCH_BLOCKED": "General dispatch blocking condition",
    "WRONG_BRANCH": "Agent worktree is on an unexpected branch",
    "WRONG_HEAD": "Agent worktree HEAD does not match expected baseline",
    "DIRTY_WORKTREE": "Agent worktree has tracked dirty files",
    "MISSING_ORIGIN_REMOTE": "Repo checkout has no origin remote",
    "STALE_FETCH": "origin/main is not reachable; fetch required",
    "CANONICAL_REPO_DIRTY_STATE_MASKING_ORIGIN": "Canonical repo is dirty or untrusted",
    "DETACHED_HEAD": "Agent worktree is in detached HEAD state (implementer)",
    "EXPECTED_DETACHED_HEAD": "Validator worktree is on a branch instead of detached",
    "WORKTREE_MISSING": "Agent worktree path does not exist",
    "MISSING_PE_TASK": "PE_TASK.md not found at .elis/pe/<PE-ID>/",
    "DISPATCH_PATH_BLOCKED": "All dispatch routes are blocked",
    "DISPATCH_RECOVERY_BLOCKED": "Dispatch recovery also blocked; no fallback available",
    "IMPLEMENTER_EXECUTION_BLOCKED": "Implementer execution failed before clean commit",
    "MISSING_RESET_ACK": "Reset/binding acknowledgement missing before dispatch",
    "SELF_FIX_ROUTING": "Agent attempted to route work to itself",
    "UNCOMMITTED_MISREPORTED": "Uncommitted artefacts misreported as complete",
}


def classify_failure(code: str) -> str:
    """Return the failure-class classification label for a blocking scenario."""
    label = FAILURE_CLASSES.get(code, "UNKNOWN_FAILURE")
    return f"{code} / {label}"


def git(cmd: list[str], cwd: Path) -> str:
    return subprocess.check_output(["git", *cmd], cwd=cwd, text=True).strip()


def _is_pe_specific_runtime(path: str) -> bool:
    parts = Path(path).parts
    return any(part.startswith("PE-") for part in parts)


def _is_untracked_or_dirty(path: str) -> tuple[bool, str]:
    rel = Path(path)
    if str(rel) == ".openclaw" or str(rel).startswith(".openclaw/"):
        return True, "preserved runtime/context root"
    if rel.name in _PRESERVED_CONTEXT_FILES and len(rel.parts) == 1:
        return True, "preserved runtime/context file"
    return False, "not protected"


FIXED_WORKTREE_FORBIDDEN = {
    ".openclaw",
    "HEARTBEAT.md",
    "IDENTITY.md",
    "SOUL.md",
    "TOOLS.md",
    "USER.md",
}


def _check_forbidden_files_in_worktree(worktree: Path) -> list[str]:
    """Check for forbidden runtime/bootstrap files inside the Git worktree.
    Returns a list of forbidden files found."""
    found: list[str] = []
    for f in FIXED_WORKTREE_FORBIDDEN:
        candidate = worktree / f
        if candidate.exists():
            found.append(f)
        if (worktree / ".elis" / f).exists():
            found.append(f".elis/{f}")
    return found


def _legacy_agent_check(agent: str) -> int:
    print(f"Agent: {agent}")
    worktree = AGENT_WORKTREE_MAP.get(agent)
    if not worktree:
        print(f"Unknown agent ID: {agent}")
        return 1
    if not Path(worktree).exists():
        return 1
    return 0


def main() -> int:
    p = argparse.ArgumentParser(
        description="Check PE dispatch binding and classify failures"
    )
    p.add_argument("--repo", default=".")
    p.add_argument("--agent")
    p.add_argument("--pe-id")
    p.add_argument("--branch")
    p.add_argument("--head")
    p.add_argument("--worktree")
    p.add_argument(
        "--mode", choices=["implementer", "validator"], default="implementer"
    )
    p.add_argument(
        "--classify",
        metavar="CODE",
        help="Return the failure-class label for a blocking code",
    )
    args = p.parse_args()

    if args.classify:
        label = classify_failure(args.classify)
        print(label)
        # All failure-class codes are blocking scenarios
        return 1

    if args.agent:
        return _legacy_agent_check(args.agent)

    if not args.pe_id or not args.head or not args.worktree:
        p.error("the following arguments are required: --pe-id, --head, --worktree")

    repo = Path(args.repo).resolve()
    worktree = Path(args.worktree).resolve()

    if not repo.exists():
        print("WORKTREE_MISSING: repo path does not exist", file=sys.stderr)
        return 1
    if not worktree.exists():
        print("WORKTREE_MISSING: worktree path does not exist", file=sys.stderr)
        return 1

    try:
        if git(["rev-parse", "--show-toplevel"], repo) != str(repo):
            print("WORKTREE_MISMATCH: repo root mismatch", file=sys.stderr)
            return 2
    except subprocess.CalledProcessError:
        print("WORKTREE_MISMATCH: repo is not a git repository", file=sys.stderr)
        return 2

    try:
        git(["remote", "get-url", "origin"], repo)
    except subprocess.CalledProcessError:
        print("MISSING_ORIGIN_REMOTE", file=sys.stderr)
        return 8

    try:
        local_origin_main = git(["rev-parse", "origin/main"], repo)
    except subprocess.CalledProcessError:
        print("STALE_FETCH", file=sys.stderr)
        return 8

    remote_result = subprocess.run(
        ["git", "ls-remote", "origin", "refs/heads/main"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
    )
    remote_line = remote_result.stdout.strip().splitlines()[0] if remote_result.stdout.strip() else ""
    remote_origin_main = remote_line.split()[0] if remote_line else ""
    if remote_result.returncode != 0 or not remote_origin_main:
        print("STALE_FETCH", file=sys.stderr)
        return 8
    if local_origin_main != remote_origin_main:
        print("STALE_FETCH", file=sys.stderr)
        return 8

    repo_dirty = git(["status", "--short"], repo)
    if repo_dirty:
        print("CANONICAL_REPO_DIRTY_STATE_MASKING_ORIGIN", file=sys.stderr)
        return 9

    try:
        current_branch = git(["branch", "--show-current"], worktree)
    except (subprocess.CalledProcessError, FileNotFoundError):
        current_branch = ""
        if args.mode == "implementer":
            print("WORKTREE_MISSING: cannot read worktree branch", file=sys.stderr)
            return 1
    if args.mode == "implementer":
        if not args.branch:
            print("MISSING_BRANCH", file=sys.stderr)
            return 3
        if current_branch != args.branch:
            print("WRONG_BRANCH", file=sys.stderr)
            return 3
    else:
        if current_branch:
            print("EXPECTED_DETACHED_HEAD", file=sys.stderr)
            return 3

    try:
        current_head = git(["rev-parse", "HEAD"], worktree)
    except (subprocess.CalledProcessError, FileNotFoundError):
        current_head = ""
    if current_head != args.head:
        print("WRONG_HEAD", file=sys.stderr)
        return 4

    # Check for forbidden runtime/bootstrap files inside the Git worktree
    forbidden_found = _check_forbidden_files_in_worktree(worktree)
    if forbidden_found:
        print(
            f"FORBIDDEN_IN_WORKTREE:{','.join(forbidden_found)}",
            file=sys.stderr,
        )
        return 7

    try:
        dirty = git(["status", "--short", "--untracked-files=no"], worktree)
    except (subprocess.CalledProcessError, FileNotFoundError):
        dirty = ""
    if dirty:
        print("DIRTY_WORKTREE", file=sys.stderr)
        return 5

    pe_task = repo / ".elis" / "pe" / args.pe_id / "PE_TASK.md"
    if not pe_task.exists():
        print("MISSING_PE_TASK", file=sys.stderr)
        return 6

    print(f"OK {args.pe_id} {args.branch} {args.head}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
