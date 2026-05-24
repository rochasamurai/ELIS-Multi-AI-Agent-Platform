from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def run(cmd, cwd, env=None):
    env2 = os.environ.copy()
    env2.update(
        {
            "GIT_AUTHOR_NAME": "Test",
            "GIT_AUTHOR_EMAIL": "test@example.com",
            "GIT_COMMITTER_NAME": "Test",
            "GIT_COMMITTER_EMAIL": "test@example.com",
        }
    )
    if env:
        env2.update(env)
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True, env=env2)


def init_repo(tmp_path: Path):
    run(["git", "init"], tmp_path)
    (tmp_path / ".elis/pe/PE-OPS-SKILLS-01").mkdir(parents=True)
    (tmp_path / ".openclaw").mkdir()
    for name in ["HEARTBEAT.md", "IDENTITY.md", "SOUL.md", "TOOLS.md", "USER.md"]:
        (tmp_path / name).write_text(name)
    (tmp_path / "README.md").write_text("root")
    run(["git", "add", "."], tmp_path)
    run(["git", "commit", "-m", "init"], tmp_path)
    base_head = run(["git", "rev-parse", "HEAD"], tmp_path).stdout.strip()
    run(["git", "update-ref", "refs/remotes/origin/main", base_head], tmp_path)
    return tmp_path


def script(name):
    return REPO / "scripts" / name


def test_dispatch_binding_ok(tmp_path):
    repo = init_repo(tmp_path)
    branch = "feature/test"
    run(["git", "checkout", "-b", branch], repo)
    (repo / ".elis/pe/PE-OPS-SKILLS-01/PE_TASK.md").write_text("x")
    run(["git", "add", ".elis/pe/PE-OPS-SKILLS-01/PE_TASK.md"], repo)
    # Remove runtime bootstrap files that belong in the runtime workspace, not the Git worktree
    for name in ["HEARTBEAT.md", "IDENTITY.md", "SOUL.md", "TOOLS.md", "USER.md"]:
        (repo / name).unlink(missing_ok=True)
    import shutil

    shutil.rmtree(repo / ".openclaw", ignore_errors=True)
    run(["git", "add", "-A"], repo)
    run(["git", "commit", "-m", "remove-runtime-files"], repo)
    head = run(["git", "rev-parse", "HEAD"], repo).stdout.strip()
    proc = run(
        [
            sys.executable,
            str(script("check_dispatch_binding.py")),
            "--pe-id",
            "PE-OPS-SKILLS-01",
            "--branch",
            branch,
            "--head",
            head,
            "--worktree",
            str(repo),
        ],
        repo,
    )
    assert proc.returncode == 0, proc.stderr
    assert "OK PE-OPS-SKILLS-01" in proc.stdout


def test_dispatch_binding_wrong_branch(tmp_path):
    repo = init_repo(tmp_path)
    (repo / ".elis/pe/PE-OPS-SKILLS-01/PE_TASK.md").write_text("x")
    run(["git", "add", ".elis/pe/PE-OPS-SKILLS-01/PE_TASK.md"], repo)
    run(["git", "commit", "-m", "task"], repo)
    head = run(["git", "rev-parse", "HEAD"], repo).stdout.strip()
    proc = run(
        [
            sys.executable,
            str(script("check_dispatch_binding.py")),
            "--pe-id",
            "PE-OPS-SKILLS-01",
            "--branch",
            "other",
            "--head",
            head,
            "--worktree",
            str(repo),
        ],
        repo,
    )
    assert proc.returncode != 0
    assert "WRONG_BRANCH" in proc.stderr


def test_dispatch_binding_validator_mode_accepts_detached_head(tmp_path):
    repo = init_repo(tmp_path)
    run(
        [
            "git",
            "checkout",
            "-b",
            "feature/pe-ops-skills-01-harden-agent-skills-and-dispatch-validation-gates",
        ],
        repo,
    )
    (repo / ".elis/pe/PE-OPS-SKILLS-01/PE_TASK.md").write_text("x")
    run(["git", "add", ".elis/pe/PE-OPS-SKILLS-01/PE_TASK.md"], repo)
    # Remove runtime bootstrap files that belong in the runtime workspace, not the Git worktree
    for name in ["HEARTBEAT.md", "IDENTITY.md", "SOUL.md", "TOOLS.md", "USER.md"]:
        (repo / name).unlink(missing_ok=True)
    import shutil

    shutil.rmtree(repo / ".openclaw", ignore_errors=True)
    run(["git", "add", "-A"], repo)
    run(["git", "commit", "-m", "remove-runtime-files"], repo)
    head = run(["git", "rev-parse", "HEAD"], repo).stdout.strip()
    run(["git", "checkout", "--detach", "HEAD"], repo)
    proc = run(
        [
            sys.executable,
            str(script("check_dispatch_binding.py")),
            "--pe-id",
            "PE-OPS-SKILLS-01",
            "--branch",
            "feature/pe-ops-skills-01-harden-agent-skills-and-dispatch-validation-gates",
            "--head",
            head,
            "--worktree",
            str(repo),
            "--mode",
            "validator",
        ],
        repo,
    )
    assert proc.returncode == 0, proc.stderr
    assert "OK PE-OPS-SKILLS-01" in proc.stdout


def test_implementation_readiness_dirty_worktree(tmp_path):
    repo = init_repo(tmp_path)
    run(
        [
            "git",
            "checkout",
            "-b",
            "feature/pe-ops-skills-01-harden-agent-skills-and-dispatch-validation-gates",
        ],
        repo,
    )
    (repo / ".elis/pe/PE-OPS-SKILLS-01/GOVERNANCE.md").write_text("x")
    run(["git", "add", ".elis/pe/PE-OPS-SKILLS-01/GOVERNANCE.md"], repo)
    run(["git", "commit", "-m", "scope"], repo)
    (repo / "README.md").write_text("dirty")
    proc = run(
        [
            sys.executable,
            str(script("check_implementation_readiness.py")),
            "--repo",
            str(repo),
            "--pe-id",
            "PE-OPS-SKILLS-01",
            "--branch",
            "feature/pe-ops-skills-01-harden-agent-skills-and-dispatch-validation-gates",
            "--head",
            run(["git", "rev-parse", "HEAD"], repo).stdout.strip(),
            "--worktree",
            str(repo),
        ],
        repo,
    )
    assert proc.returncode != 0
    assert "DIRTY_WORKTREE" in proc.stderr


def test_implementation_readiness_validator_mode_accepts_detached_head_and_optional_context(
    tmp_path,
):
    repo = init_repo(tmp_path)
    # Remove runtime bootstrap files that belong in the runtime workspace, not the Git worktree
    for name in ["HEARTBEAT.md", "IDENTITY.md", "SOUL.md", "TOOLS.md", "USER.md"]:
        (repo / name).unlink(missing_ok=True)
    import shutil

    shutil.rmtree(repo / ".openclaw", ignore_errors=True)
    run(["git", "add", "-A"], repo)
    run(["git", "commit", "-m", "remove-runtime-files"], repo)
    run(
        [
            "git",
            "checkout",
            "-b",
            "feature/pe-ops-skills-01-harden-agent-skills-and-dispatch-validation-gates",
        ],
        repo,
    )
    pe_dir = repo / ".elis/pe/PE-OPS-SKILLS-01"
    pe_dir.mkdir(parents=True, exist_ok=True)
    for name in [
        "GOVERNANCE.md",
        "SKILLS_PM.md",
        "SKILLS_IMPLEMENTERS.md",
        "SKILLS_VALIDATORS.md",
    ]:
        (pe_dir / name).write_text(name)
    run(["git", "add", ".elis/pe/PE-OPS-SKILLS-01"], repo)
    run(["git", "commit", "-m", "scope"], repo)
    head = run(["git", "rev-parse", "HEAD"], repo).stdout.strip()
    run(["git", "checkout", "--detach", "HEAD"], repo)
    proc = run(
        [
            sys.executable,
            str(script("check_implementation_readiness.py")),
            "--repo",
            str(repo),
            "--pe-id",
            "PE-OPS-SKILLS-01",
            "--mode",
            "validator",
            "--head",
            head,
            "--worktree",
            str(repo),
        ],
        repo,
    )
    assert proc.returncode == 0, proc.stderr
    assert "READY PE-OPS-SKILLS-01" in proc.stdout
    # Persistent context files were already removed (part of the test setup).
    # Verify the optional check reports them as missing.
    proc2 = run(
        [
            sys.executable,
            str(script("check_persistent_context_files.py")),
            "--repo",
            str(repo),
        ],
        repo,
    )
    assert proc2.returncode == 0
    assert "PERSISTENT_CONTEXT_OPTIONAL" in proc2.stdout


def test_validation_readiness_wrong_scope_and_stale_artifact(tmp_path):
    repo = init_repo(tmp_path)
    # Remove runtime bootstrap files that belong in the runtime workspace, not the Git worktree
    for name in ["HEARTBEAT.md", "IDENTITY.md", "SOUL.md", "TOOLS.md", "USER.md"]:
        (repo / name).unlink(missing_ok=True)
    import shutil

    shutil.rmtree(repo / ".openclaw", ignore_errors=True)
    run(
        [
            "git",
            "checkout",
            "-b",
            "feature/pe-ops-skills-01-harden-agent-skills-and-dispatch-validation-gates",
        ],
        repo,
    )
    (repo / ".elis/pe/PE-OPS-SKILLS-01/GOVERNANCE.md").write_text("x")
    (repo / ".elis/pe/PE-OPS-SKILLS-01/HANDOFF.md").write_text("x")
    (repo / ".elis/pe/PE-OPS-SKILLS-01/REVIEW.md").write_text("x")
    (repo / ".elis/pe/PE-OPS-SKILLS-01/old.txt").write_text("stale")
    run(["git", "add", "-A"], repo)
    run(["git", "commit", "-m", "scope"], repo)
    head = run(["git", "rev-parse", "HEAD"], repo).stdout.strip()
    proc = run(
        [
            sys.executable,
            str(script("check_validation_readiness.py")),
            "--repo",
            str(repo),
            "--pe-id",
            "PE-OPS-SKILLS-01",
            "--worktree",
            str(repo),
            "--expected-commit",
            head,
            "--allowed-root",
            "/home/samurai",
            "--artifact-dir",
            str(repo / ".elis/pe/PE-OPS-SKILLS-01"),
        ],
        repo,
    )
    assert proc.returncode != 0
    assert "WORKSPACE_MISMATCH" in proc.stderr
    proc2 = run(
        [
            sys.executable,
            str(script("check_validation_readiness.py")),
            "--repo",
            str(repo),
            "--pe-id",
            "PE-OPS-SKILLS-01",
            "--worktree",
            str(repo),
            "--expected-commit",
            head,
            "--allowed-root",
            str(repo),
            "--artifact-dir",
            str(repo / ".elis/pe/PE-OPS-SKILLS-01"),
        ],
        repo,
    )
    assert proc2.returncode != 0
    assert "STALE_PE_ARTIFACTS" in proc2.stderr


def test_persistent_context_files_check(tmp_path):
    repo = init_repo(tmp_path)
    proc = run(
        [
            sys.executable,
            str(script("check_persistent_context_files.py")),
            "--repo",
            str(repo),
            "--required",
        ],
        repo,
    )
    assert proc.returncode == 0
    assert "PERSISTENT_CONTEXT_OK" in proc.stdout
