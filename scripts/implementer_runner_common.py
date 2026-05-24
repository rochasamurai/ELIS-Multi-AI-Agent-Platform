"""Shared helpers for PE-AUTO-04 implementer runners."""

from __future__ import annotations

import os
import re
import shlex
import subprocess
import sys
import time
from datetime import datetime, timezone
from dataclasses import dataclass
from pathlib import Path

from elis.agent_id import engine_from_agent_id
from elis.reviewer_identity import ReviewerIdentityError, review_login_for_engine
from elis.workflow_state_machine import ensure_canonical_state


PE_SECTION_RE = r"### {pe_id}\b"
PE_ROW_RE = re.compile(r"^\|\s*PE\s*\|\s*(PE-[A-Z0-9-]+-[0-9]+)\s*\|$", re.MULTILINE)
FIELD_ROW_RE = re.compile(r"^\|\s*(?P<field>[^|]+?)\s*\|\s*(?P<value>[^|]+?)\s*\|$")
AGENT_ROW_RE = re.compile(
    r"^\|\s*(?P<label>CODEX|Claude Code)\s*\|\s*(?P<role>Implementer|Validator)\s*\|$",
    re.MULTILINE,
)
REGISTRY_ROW_RE = re.compile(
    r"^\|\s*(?P<pe>PE-[A-Z0-9-]+-[0-9]+)\s*\|\s*(?P<domain>[^|]+?)\s*\|"
    r"\s*(?P<implementer>[^|]+?)\s*\|\s*(?P<validator>[^|]+?)\s*\|"
    r"\s*(?P<branch>[^|]+?)\s*\|\s*(?P<status>[^|]+?)\s*\|"
    r"\s*(?P<updated>[^|]+?)\s*\|$",
    re.MULTILINE,
)


@dataclass(frozen=True)
class CurrentPEContext:
    pe_id: str
    branch: str
    base_branch: str
    plan_file: str
    plan_location: str
    status: str
    implementer_agent: str
    validator_agent: str
    implementer_engine: str
    validator_engine: str


@dataclass(frozen=True)
class RunnerInputs:
    pe_id: str
    branch: str
    base_branch: str
    plan_file: str
    engine: str
    max_commits: int
    timeout_seconds: int


class RunnerError(RuntimeError):
    """Raised when the runner cannot proceed safely."""


def _extract_table_value(content: str, heading: str, field: str) -> str:
    lines = content.splitlines()
    in_heading = False
    for line in lines:
        if line.strip() == heading:
            in_heading = True
            continue
        if in_heading and line.startswith("## ") and line.strip() != heading:
            break
        match = FIELD_ROW_RE.match(line.strip())
        if match and match.group("field").strip() == field:
            return match.group("value").strip()
    raise RunnerError(f"Missing '{field}' in section '{heading}'.")


def _engine(agent_id: str) -> str:
    try:
        return engine_from_agent_id(agent_id)
    except ValueError as exc:
        raise RunnerError(str(exc)) from exc


def parse_current_pe(path: Path) -> CurrentPEContext:
    content = path.read_text(encoding="utf-8")
    pe_id = _extract_table_value(content, "## Current PE", "PE")
    branch = _extract_table_value(content, "## Current PE", "Branch")
    base_branch = _extract_table_value(content, "## Release context", "Base branch")
    plan_file = _extract_table_value(content, "## Release context", "Plan file")
    plan_location = _extract_table_value(content, "## Release context", "Plan location")

    registry_match = None
    for match in REGISTRY_ROW_RE.finditer(content):
        if match.group("pe").strip() == pe_id:
            registry_match = match
            break
    if registry_match is None:
        raise RunnerError(
            f"Current PE '{pe_id}' is not present in the Active PE Registry."
        )

    implementer_agent = registry_match.group("implementer").strip()
    validator_agent = registry_match.group("validator").strip()
    status = registry_match.group("status").strip().lower()
    try:
        ensure_canonical_state(status)
    except ValueError as exc:
        raise RunnerError(str(exc)) from exc

    if registry_match.group("branch").strip() != branch:
        raise RunnerError(
            "Current PE branch does not match the Active PE Registry row."
        )

    return CurrentPEContext(
        pe_id=pe_id,
        branch=branch,
        base_branch=base_branch,
        plan_file=plan_file,
        plan_location=plan_location,
        status=status,
        implementer_agent=implementer_agent,
        validator_agent=validator_agent,
        implementer_engine=_engine(implementer_agent),
        validator_engine=_engine(validator_agent),
    )


def verify_canonical_repo_trust(repo_root: Path) -> None:
    """Refuse to dispatch if the canonical repository is stale or dirty."""
    canonical_root = Path("/opt/elis/repo").resolve()
    if repo_root.resolve() != canonical_root:
        return
    if not (repo_root / ".git").exists():
        return

    local_origin_main = subprocess.check_output(
        ["git", "rev-parse", "origin/main"], cwd=repo_root, text=True
    ).strip()
    remote_result = subprocess.run(
        ["git", "ls-remote", "origin", "refs/heads/main"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    remote_line = (
        remote_result.stdout.strip().splitlines()[0]
        if remote_result.stdout.strip()
        else ""
    )
    remote_origin_main = remote_line.split()[0] if remote_line else ""
    if remote_result.returncode != 0 or not remote_origin_main:
        raise RunnerError("Canonical repo origin/main cannot be resolved from remote.")
    if local_origin_main != remote_origin_main:
        raise RunnerError(
            "Canonical repo origin/main is stale; fetch origin before dispatch."
        )

    dirty = subprocess.run(
        ["git", "status", "--short"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    if dirty.returncode != 0:
        raise RunnerError("Canonical repo status could not be read.")
    if dirty.stdout.strip():
        raise RunnerError(
            "Canonical repo is dirty or untrusted; clean it or quarantine it before dispatch."
        )


def acceptance_criteria_for_pe(plan_path: Path, pe_id: str) -> list[str]:
    content = plan_path.read_text(encoding="utf-8")
    section_match = re.search(
        PE_SECTION_RE.format(pe_id=re.escape(pe_id)),
        content,
        re.MULTILINE,
    )
    if section_match is None:
        raise RunnerError(f"Could not find plan section for {pe_id} in {plan_path}.")

    section = content[section_match.start() :]
    stop_match = re.search(r"^---\s*$", section, re.MULTILINE)
    if stop_match:
        section = section[: stop_match.start()]

    ac_rows = re.findall(r"^\|\s*AC-[0-9]+\s*\|\s*(.+?)\s*\|$", section, re.MULTILINE)
    if not ac_rows:
        raise RunnerError(f"No acceptance criteria table found for {pe_id}.")
    return ac_rows


def build_prompt(
    *,
    engine: str,
    repo_root: Path,
    current_pe_path: Path,
    plan_path: Path,
    pe_id: str,
) -> str:
    agents_text = (repo_root / "AGENTS.md").read_text(encoding="utf-8")
    current_pe_text = current_pe_path.read_text(encoding="utf-8")
    criteria = acceptance_criteria_for_pe(plan_path, pe_id)
    criteria_block = "\n".join(f"- {criterion}" for criterion in criteria)

    return (
        f"You are the ELIS {engine.upper()} Implementer runner for {pe_id}.\n\n"
        "Follow AGENTS.md Section 5.1 autonomously.\n"
        "Implement only the active PE acceptance criteria, keep scope minimal,\n"
        "run quality gates, update the namespaced handoff file in handoffs/,\n"
        "regenerate the root HANDOFF.md with `python scripts/copy_handoff.py`,\n"
        "and commit all changes with HANDOFF.md as the last commit.\n"
        "Do not open, refresh, or ready the PR yourself. The runner opens or\n"
        "readies the PR only after it verifies a clean tree and HANDOFF.md as\n"
        "the last commit. Treat origin/main as the authoritative baseline;\n"
        "HANDOFF.md is operational context, not dispatch evidence.\n\n"
        f"Active plan: {plan_path.name}\n\n"
        "=== ACTIVE PLAN ACCEPTANCE CRITERIA ===\n"
        f"{criteria_block}\n\n"
        "Canonical context files follow.\n\n"
        "=== AGENTS.md ===\n"
        f"{agents_text}\n\n"
        "=== CURRENT_PE.md ===\n"
        f"{current_pe_text}\n"
    )


def ensure_budget(
    commit_count: int,
    max_commits: int,
    *,
    started_at: float,
    now: float,
    timeout_seconds: int,
) -> None:
    if commit_count > max_commits:
        raise RunnerError(
            f"Commit budget exceeded: {commit_count} commits > MAX_COMMITS={max_commits}."
        )
    if now - started_at > timeout_seconds:
        raise RunnerError(
            f"Runner timeout exceeded: {int(now - started_at)}s > {timeout_seconds}s."
        )


def expected_login(engine: str) -> str:
    try:
        return review_login_for_engine(engine)
    except ReviewerIdentityError as exc:
        raise RunnerError(str(exc)) from exc


def gh_login() -> str:
    result = subprocess.run(
        ["gh", "api", "user"],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    if result.returncode != 0:
        raise RunnerError(f"gh api user failed: {result.stderr.strip()}")
    match = re.search(r'"login"\s*:\s*"([^"]+)"', result.stdout)
    if match is None:
        raise RunnerError("Could not parse GitHub login from gh api user output.")
    return match.group(1)


def ensure_expected_login(engine: str) -> None:
    login = gh_login()
    expected = expected_login(engine)
    if login != expected:
        raise RunnerError(
            f"GitHub identity mismatch: expected '{expected}', got '{login}'."
        )


def branch_commit_count(base_branch: str) -> int:
    result = subprocess.run(
        ["git", "rev-list", "--count", f"origin/{base_branch}..HEAD"],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    if result.returncode != 0:
        raise RunnerError(result.stderr.strip() or "git rev-list failed.")
    return int(result.stdout.strip())


def last_commit_touches(path: str) -> bool:
    result = subprocess.run(
        ["git", "show", "--name-only", "--format=", "HEAD"],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    if result.returncode != 0:
        raise RunnerError(result.stderr.strip() or "git show failed.")
    touched = {line.strip() for line in result.stdout.splitlines() if line.strip()}
    return path in touched


def working_tree_clean() -> bool:
    result = subprocess.run(
        ["git", "status", "--short"],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    if result.returncode != 0:
        raise RunnerError(result.stderr.strip() or "git status failed.")
    return not result.stdout.strip()


def ensure_handoff_ready_for_pr() -> None:
    """Refuse PR operations until the runner handoff contract is satisfied."""

    if not working_tree_clean():
        raise RunnerError(
            "Working tree is dirty after agent run; refusing to open or ready PR."
        )
    if not last_commit_touches("HANDOFF.md"):
        raise RunnerError(
            "HANDOFF.md is not part of the last commit; refusing to open or ready PR."
        )


def pr_number(branch: str, base_branch: str) -> str | None:
    result = subprocess.run(
        [
            "gh",
            "pr",
            "list",
            "--head",
            branch,
            "--base",
            base_branch,
            "--json",
            "number",
        ],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    if result.returncode != 0:
        raise RunnerError(result.stderr.strip() or "gh pr list failed.")
    match = re.search(r'"number"\s*:\s*([0-9]+)', result.stdout)
    return match.group(1) if match else None


def create_draft_pr(branch: str, base_branch: str, pe_id: str) -> None:
    title = f"feat({pe_id.lower()}): implement autonomous runner"
    body = (
        f"## Summary\n"
        f"- Implementing {pe_id}\n\n"
        "## Test plan\n"
        "- quality / tests / validate\n"
    )
    result = subprocess.run(
        [
            "gh",
            "pr",
            "create",
            "--draft",
            "--head",
            branch,
            "--base",
            base_branch,
            "--title",
            title,
            "--body",
            body,
        ],
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    if result.returncode != 0 and "already exists" not in result.stderr.lower():
        raise RunnerError(result.stderr.strip() or "gh pr create failed.")


def mark_pr_ready(branch: str, base_branch: str) -> None:
    if not last_commit_touches("HANDOFF.md"):
        raise RunnerError(
            "HANDOFF.md is not part of the last commit; refusing gh pr ready."
        )
    number = pr_number(branch, base_branch)
    if number is None:
        raise RunnerError("Cannot mark PR ready because no draft PR exists yet.")
    result = subprocess.run(
        ["gh", "pr", "ready", number],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    if (
        result.returncode != 0
        and "pull request is already marked as ready" not in result.stderr.lower()
    ):
        raise RunnerError(result.stderr.strip() or "gh pr ready failed.")


def default_cli_command(engine: str, prompt: str) -> list[str]:
    if engine == "codex":
        # script(1) allocates a pseudo-TTY so codex exec does not fail with
        # "stdin is not a terminal". The prompt is passed via $CODEX_PROMPT
        # (set by run_cli) to avoid shell-quoting issues with long markdown.
        # DEVNULL stdin → PTY EOF → codex exec interprets as Ctrl-D and exits
        # cleanly after completing the task instead of looping for more input.
        # -q: suppress "Script started" banner  -e: propagate codex exit code.
        return [
            "script",
            "-q",
            "-e",
            "-c",
            'codex exec --skip-git-repo-check --dangerously-bypass-approvals-and-sandbox "$CODEX_PROMPT"',
            "/dev/null",
        ]
    if engine == "claude":
        return ["claude", "-p", prompt, "--dangerously-skip-permissions"]
    raise RunnerError(f"Unsupported engine '{engine}'.")


def cli_command(engine: str, prompt: str) -> list[str]:
    template = os.environ.get("AGENT_RUNNER_TEMPLATE", "").strip()
    if not template:
        return default_cli_command(engine, prompt)
    prompt_file = Path("runner_prompt.txt").resolve()
    prompt_file.write_text(prompt, encoding="utf-8")
    rendered = template.format(prompt=prompt, prompt_file=str(prompt_file))
    return shlex.split(rendered)


def run_cli(engine: str, prompt: str, *, timeout: int | None = None) -> None:
    cmd = cli_command(engine, prompt)
    env = {**os.environ, "CODEX_PROMPT": prompt} if engine == "codex" else None
    result = subprocess.run(
        cmd,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        timeout=timeout,
        env=env,
        check=False,
    )
    if result.returncode != 0:
        stderr = result.stderr.strip() or result.stdout.strip()
        raise RunnerError(f"{engine} runner invocation failed: {stderr}")


def parse_runner_inputs(argv: list[str], engine: str) -> RunnerInputs:
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
    except KeyError as exc:
        raise RunnerError(
            f"Missing required argument '--{exc.args[0].replace('_', '-')}'."
        ) from exc

    base_branch = values.get("base_branch", "main")
    max_commits = int(values.get("max_commits", os.environ.get("MAX_COMMITS", "20")))
    timeout_seconds = int(
        values.get(
            "timeout_seconds",
            os.environ.get("RUNNER_TIMEOUT_SECONDS", str(4 * 60 * 60)),
        )
    )
    return RunnerInputs(
        pe_id=pe_id,
        branch=branch,
        base_branch=base_branch,
        plan_file=plan_file,
        engine=engine,
        max_commits=max_commits,
        timeout_seconds=timeout_seconds,
    )


def runner_started_at(now: float | None = None) -> float:
    raw = os.environ.get("RUNNER_STARTED_AT", "").strip()
    if not raw:
        return time.time() if now is None else now

    try:
        return float(raw)
    except ValueError:
        pass

    try:
        normalised = raw.replace("Z", "+00:00")
        return datetime.fromisoformat(normalised).astimezone(timezone.utc).timestamp()
    except ValueError:
        return time.time() if now is None else now


def run_implementer(argv: list[str], *, engine: str) -> int:
    try:
        inputs = parse_runner_inputs(argv, engine)
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
                f"CURRENT_PE.md says active branch is {context.branch}, not {inputs.branch}."
            )
        if context.implementer_engine != engine:
            raise RunnerError(
                f"Active implementer engine is {context.implementer_engine}, not {engine}."
            )

        started_at = runner_started_at()
        ensure_expected_login(engine)
        ensure_budget(
            branch_commit_count(inputs.base_branch),
            inputs.max_commits,
            started_at=started_at,
            now=time.time(),
            timeout_seconds=inputs.timeout_seconds,
        )

        prompt = build_prompt(
            engine=engine,
            repo_root=repo_root,
            current_pe_path=current_pe_path,
            plan_path=repo_root / inputs.plan_file,
            pe_id=inputs.pe_id,
        )
        run_cli(engine, prompt, timeout=inputs.timeout_seconds)

        ensure_budget(
            branch_commit_count(inputs.base_branch),
            inputs.max_commits,
            started_at=started_at,
            now=time.time(),
            timeout_seconds=inputs.timeout_seconds,
        )

        ensure_handoff_ready_for_pr()
        create_draft_pr(inputs.branch, inputs.base_branch, inputs.pe_id)
        mark_pr_ready(inputs.branch, inputs.base_branch)
        print(f"{engine} implementer runner PASS for {inputs.pe_id}")
        return 0
    except RunnerError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
