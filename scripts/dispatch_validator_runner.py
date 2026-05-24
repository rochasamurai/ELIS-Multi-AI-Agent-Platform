"""Resolve CURRENT_PE.md into workflow_dispatch inputs for PE-AUTO-05.

HANDOFF evidence is supplementary; dispatch authority comes from the current
PE state and validated live gate outputs.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

from elis.workflow_state_machine import (
    VALIDATOR_DISPATCH_SOURCE_STATE,
    VALIDATOR_DISPATCH_TARGET_STATE,
    guards_for,
    validator_dispatch_allowed_after_evidence,
)
from scripts.check_handoff import REQUIRED_SECTIONS as HANDOFF_REQUIRED_SECTIONS
from scripts.check_status_packet import (
    REQUIRED_SECTIONS as STATUS_PACKET_REQUIRED_SECTIONS,
)
from scripts.implementer_runner_common import (
    CurrentPEContext,
    RunnerError,
    parse_current_pe,
)


def _handoff_path() -> Path:
    return Path(os.environ.get("HANDOFF_PATH", "HANDOFF.md"))


def _pr_head_branch(pr_number: str) -> str:
    """Return the head branch name for the given PR number via gh CLI."""
    result = subprocess.run(
        ["gh", "pr", "view", pr_number, "--json", "headRefName"],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    if result.returncode != 0:
        raise RunnerError(result.stderr.strip() or "gh pr view failed.")
    match = re.search(r'"headRefName"\s*:\s*"([^"]+)"', result.stdout)
    if match is None:
        raise RunnerError("Could not parse headRefName from gh pr view output.")
    return match.group(1)


def _verify_sections(path: Path, required_sections: list[str], label: str) -> None:
    if not path.exists():
        raise RunnerError(f"{label} not found: {path}")
    content = path.read_text(encoding="utf-8")
    missing = [section for section in required_sections if section not in content]
    if missing:
        raise RunnerError(
            f"{label} incomplete ({path}) — missing sections: " + ", ".join(missing)
        )


def _require_ready_for_validation(context: CurrentPEContext) -> None:
    handoff_path = _handoff_path()
    _verify_sections(handoff_path, STATUS_PACKET_REQUIRED_SECTIONS, "Status Packet")
    _verify_sections(handoff_path, HANDOFF_REQUIRED_SECTIONS, "HANDOFF")

    if not validator_dispatch_allowed_after_evidence(context.status):
        required_guards = guards_for(
            VALIDATOR_DISPATCH_SOURCE_STATE,
            VALIDATOR_DISPATCH_TARGET_STATE,
        )
        guard_text = "; ".join(required_guards)
        raise RunnerError(
            f"Current PE status is '{context.status}' — validator dispatch requires "
            f"complete implementer evidence from 'implementing' or "
            f"'{VALIDATOR_DISPATCH_SOURCE_STATE}' before "
            f"'{VALIDATOR_DISPATCH_TARGET_STATE}'. Required authorisation evidence: "
            f"{guard_text}."
        )


def main() -> int:
    try:
        pr_number = os.environ.get("PR_NUMBER", "").strip()
        if not pr_number:
            print("FAIL: PR_NUMBER env var is not set.", file=sys.stderr)
            return 1

        current_pe_path = Path(os.environ.get("CURRENT_PE_PATH", "CURRENT_PE.md"))
        context = parse_current_pe(current_pe_path)
        _require_ready_for_validation(context)

        pr_branch = _pr_head_branch(pr_number)
        should_dispatch = pr_branch == context.branch

        lines = [
            f"should_dispatch={'true' if should_dispatch else 'false'}",
            f"pe_id={context.pe_id}",
            f"branch={context.branch}",
            f"engine={context.validator_engine}",
            f"plan_file={context.plan_file}",
            f"base_branch={context.base_branch}",
            f"pr_number={pr_number}",
        ]

        output_path = os.environ.get("GITHUB_OUTPUT")
        if output_path:
            with open(output_path, "a", encoding="utf-8") as handle:
                handle.write("\n".join(lines) + "\n")
        else:
            print("\n".join(lines))

        if not should_dispatch:
            print(
                f"PR #{pr_number} branch '{pr_branch}' does not match active PE "
                f"branch '{context.branch}' — skipping dispatch.",
                file=sys.stderr,
            )
        return 0
    except RunnerError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
