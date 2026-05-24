"""Shared helpers for PE-AUTO-05 validator runners.

Resolution model:
  - Validator runner checks out the feature branch with the validator bot token.
  - Runs the validator CLI agent which writes REVIEW_PE*.md, commits, pushes,
    and posts the formal GitHub PR review.
  - Verdict is then read from the REVIEW file by the caller (workflow step).
  - On FAIL: the workflow posts a fix assignment comment via PM_BOT_TOKEN.

Imports shared utilities from implementer_runner_common to stay DRY.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from elis.reviewer_identity import (
    ReviewerIdentityError,
    review_handle_for_engine,
    review_login_for_engine,
)
from scripts.implementer_runner_common import (
    RunnerError,
    acceptance_criteria_for_pe,
    ensure_expected_login,
    parse_current_pe,
    run_cli,
    verify_canonical_repo_trust,
)

_VERDICT_RE = re.compile(r"^(PASS|FAIL|IN PROGRESS)\b")

REVIEW_ARCHIVE_DIR = Path("docs/reviews/archive")


@dataclass(frozen=True)
class ValidatorInputs:
    pe_id: str
    branch: str
    base_branch: str
    plan_file: str
    engine: str
    pr_number: str


def review_file_name(pe_id: str) -> str:
    """Return the REVIEW filename for a given PE ID.

    Example: ``PE-AUTO-05`` -> ``REVIEW_PE_AUTO_05.md``
    """
    return "REVIEW_" + pe_id.replace("-", "_") + ".md"


def review_file_path(pe_id: str) -> str:
    """Return the repo-relative REVIEW file path for a given PE ID.

    Always uses forward slashes (suitable for git commands and CI shell scripts).

    Example: ``PE-AUTO-05`` -> ``docs/reviews/archive/REVIEW_PE_AUTO_05.md``
    """
    return f"docs/reviews/archive/{review_file_name(pe_id)}"


def build_validator_prompt(
    *,
    engine: str,
    repo_root: Path,
    current_pe_path: Path,
    plan_path: Path,
    pe_id: str,
    pr_number: str,
) -> str:
    """Build the system prompt for the autonomous validator CLI agent."""
    agents_text = (repo_root / "AGENTS.md").read_text(encoding="utf-8")
    current_pe_text = current_pe_path.read_text(encoding="utf-8")
    criteria = acceptance_criteria_for_pe(plan_path, pe_id)
    criteria_block = "\n".join(f"- {criterion}" for criterion in criteria)
    review_fpath = review_file_path(pe_id)

    return (
        f"You are the ELIS {engine.upper()} Validator runner for {pe_id}.\n\n"
        "Follow AGENTS.md Section 5.2 autonomously.\n\n"
        "Steps:\n"
        "1. Read HANDOFF.md on this branch.\n"
        "2. Run quality gates: black --check, ruff check, pytest -q.\n"
        "3. Validate each acceptance criterion below against the implementation.\n"
        "Treat origin/main as the authoritative baseline; HANDOFF.md is\n"
        "operational context, not dispatch evidence.\n"
        "4. Add adversarial tests for any weaknesses found.\n"
        f"5. Write '{review_fpath}' (under docs/reviews/archive/) with sections:\n"
        "   ### Verdict (first body line must be PASS or FAIL)\n"
        "   ### Gate results\n"
        "   ### Scope\n"
        "   ### Required fixes (say 'None.' for PASS; list findings for FAIL)\n"
        "   ### Evidence (must contain at least one fenced code block)\n"
        "6. Verify the file: `REVIEW_FILE="
        + review_fpath
        + " python scripts/check_review.py`\n"
        "7. Commit the REVIEW file and any adversarial tests. Push to this branch.\n"
        f"8. Post a formal GitHub review on PR #{pr_number}:\n"
        "   `gh pr review " + pr_number + " --approve` for PASS\n"
        "   `gh pr review "
        + pr_number
        + " --request-changes --body <summary>` for FAIL\n\n"
        "Acceptance criteria to validate:\n"
        f"{criteria_block}\n\n"
        "Canonical context files follow.\n\n"
        "=== AGENTS.md ===\n"
        f"{agents_text}\n\n"
        "=== CURRENT_PE.md ===\n"
        f"{current_pe_text}\n"
    )


def read_verdict(repo_root: Path, pe_id: str) -> str:
    """Return 'PASS', 'FAIL', 'IN PROGRESS', or 'NOT_FOUND' from the REVIEW file."""
    review_path = repo_root / REVIEW_ARCHIVE_DIR / review_file_name(pe_id)
    if not review_path.exists():
        return "NOT_FOUND"
    content = review_path.read_text(encoding="utf-8")
    lines = content.splitlines()
    for i, line in enumerate(lines):
        if line.strip() == "### Verdict":
            for j in range(i + 1, len(lines)):
                candidate = lines[j].strip()
                if not candidate:
                    continue
                m = _VERDICT_RE.match(candidate)
                return m.group(1) if m else "UNKNOWN"
    return "NOT_FOUND"


def verify_review_committed(pe_id: str, base_branch: str) -> None:
    """Raise RunnerError if the REVIEW file is not in the git log vs base branch."""
    fpath = review_file_path(pe_id)
    result = subprocess.run(
        ["git", "log", "--name-only", "--format=", f"origin/{base_branch}..HEAD"],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    if result.returncode != 0:
        raise RunnerError(result.stderr.strip() or "git log failed.")
    committed = {line.strip() for line in result.stdout.splitlines() if line.strip()}
    if fpath not in committed:
        raise RunnerError(
            f"{fpath!r} not found in commits on this branch vs {base_branch}. "
            "Agent did not commit the REVIEW file."
        )


def verify_formal_review_posted(
    pr_number: str, expected_login: str | None = None
) -> None:
    """Raise RunnerError if no formal GitHub review has been posted on the PR.

    If *expected_login* is given, also verify that at least one review was posted
    by that account (i.e. the correct opposite-bot identity).
    """
    result = subprocess.run(
        ["gh", "pr", "view", pr_number, "--json", "reviews"],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    if result.returncode != 0:
        raise RunnerError(result.stderr.strip() or "gh pr view --json reviews failed.")
    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise RunnerError(f"Could not parse gh pr view output: {exc}") from exc
    reviews = data.get("reviews", [])
    if not reviews:
        raise RunnerError(
            f"No formal GitHub review found on PR #{pr_number}. "
            "Agent did not post a formal review."
        )
    if expected_login is not None:
        logins = {r.get("author", {}).get("login", "") for r in reviews}
        if expected_login not in logins:
            raise RunnerError(
                f"No formal GitHub review from '{expected_login}' on PR #{pr_number}. "
                f"Found reviewer(s): {sorted(logins)}. "
                "Agent posted review from wrong identity."
            )


def post_fail_assignment(pr_number: str, implementer_engine: str) -> None:
    """Post a fix-assignment comment on the PR for the Implementer agent.

    The caller is responsible for setting ``GH_TOKEN`` to ``PM_BOT_TOKEN``
    before invoking this so the comment is attributed to ``elis-pm-bot``.
    """
    mention = review_handle_for_engine(implementer_engine)
    body = (
        "## Fail — fix assignment\n\n"
        f"{mention} — read the REVIEW file on this branch. "
        "Fix blocking findings only. Deliver updated Status Packet."
    )
    result = subprocess.run(
        ["gh", "pr", "comment", pr_number, "--body", body],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    if result.returncode != 0:
        raise RunnerError(result.stderr.strip() or "gh pr comment failed.")


def parse_validator_inputs(argv: list[str], engine: str) -> ValidatorInputs:
    """Parse CLI arguments for the validator runner."""
    args = argv[1:]
    values: dict[str, str] = {}
    key = None
    for item in args:
        if item.startswith("--"):
            key = item[2:].replace("-", "_")
            values[key] = ""
            continue
        if key is None:
            raise RunnerError(f"Unexpected positional argument '{item}'.")
        values[key] = item
        key = None

    try:
        pe_id = values["pe_id"]
        branch = values["branch"]
        plan_file = values["plan"]
        pr_number = values["pr_number"]
    except KeyError as exc:
        raise RunnerError(
            f"Missing required argument '--{exc.args[0].replace('_', '-')}'."
        ) from exc

    base_branch = values.get("base_branch", "main")
    return ValidatorInputs(
        pe_id=pe_id,
        branch=branch,
        base_branch=base_branch,
        plan_file=plan_file,
        engine=engine,
        pr_number=pr_number,
    )


def run_validator(argv: list[str], *, engine: str) -> int:
    """Orchestrate the autonomous validator run for a single PE."""
    try:
        inputs = parse_validator_inputs(argv, engine)
        repo_root = Path.cwd()
        verify_canonical_repo_trust(repo_root)
        current_pe_path = repo_root / "CURRENT_PE.md"
        context = parse_current_pe(current_pe_path)

        if context.pe_id != inputs.pe_id:
            raise RunnerError(
                f"CURRENT_PE.md says active PE is {context.pe_id}, not {inputs.pe_id}."
            )
        if context.branch != inputs.branch:
            raise RunnerError(
                f"CURRENT_PE.md says active branch is {context.branch}, "
                f"not {inputs.branch}."
            )
        if context.validator_engine != engine:
            raise RunnerError(
                f"Active validator engine is {context.validator_engine}, not {engine}."
            )

        ensure_expected_login(engine)

        expected_reviewer = review_login_for_engine(engine)

        prompt = build_validator_prompt(
            engine=engine,
            repo_root=repo_root,
            current_pe_path=current_pe_path,
            plan_path=repo_root / inputs.plan_file,
            pe_id=inputs.pe_id,
            pr_number=inputs.pr_number,
        )
        run_cli(engine, prompt)

        verify_review_committed(inputs.pe_id, inputs.base_branch)
        verify_formal_review_posted(inputs.pr_number, expected_login=expected_reviewer)

        verdict = read_verdict(repo_root, inputs.pe_id)
        if verdict == "NOT_FOUND":
            raise RunnerError(
                f"REVIEW file {review_file_path(inputs.pe_id)!r} not found after "
                "agent run — agent did not complete correctly."
            )

        print(
            f"{engine} validator runner complete for {inputs.pe_id} — verdict: {verdict}"
        )
        return 0
    except (RunnerError, ReviewerIdentityError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
