"""Resolve CURRENT_PE.md into workflow_dispatch inputs for PE-AUTO-04.

The current PE must already be rooted in the trusted canonical baseline.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Ensure repository root is importable when executed as
# `python scripts/dispatch_implementer_runner.py` in CI.
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from elis.workflow_state_machine import implementer_dispatch_allowed  # noqa: E402
from scripts.implementer_runner_common import (  # noqa: E402
    RunnerError,
    parse_current_pe,
)


def main() -> int:
    try:
        current_pe_path = Path(os.environ.get("CURRENT_PE_PATH", "CURRENT_PE.md"))
        context = parse_current_pe(current_pe_path)
        should_dispatch = implementer_dispatch_allowed(context.status)
        lines = [
            f"should_dispatch={'true' if should_dispatch else 'false'}",
            f"pe_id={context.pe_id}",
            f"branch={context.branch}",
            f"engine={context.implementer_engine}",
            f"plan_file={context.plan_file}",
            f"base_branch={context.base_branch}",
        ]
        output_path = os.environ.get("GITHUB_OUTPUT")
        if output_path:
            with open(output_path, "a", encoding="utf-8") as handle:
                handle.write("\n".join(lines) + "\n")
        else:
            print("\n".join(lines))
        return 0
    except RunnerError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
