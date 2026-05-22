#!/usr/bin/env python3
"""Tests for scripts/check_dispatch_binding.py — PE dispatch binding guards."""

from __future__ import annotations

import importlib.util
import subprocess
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "check_dispatch_binding.py"


def _load():
    spec = importlib.util.spec_from_file_location("check_dispatch_binding", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


MODULE = _load()


def test_is_pe_specific_runtime():
    """PE-specific runtime worktrees should be detected."""
    assert MODULE._is_pe_specific_runtime(
        "/opt/elis/agent-worktrees/PE-OPS-A2A-01-infra-impl-a"
    )
    assert not MODULE._is_pe_specific_runtime("/opt/elis/agent-worktrees/infra-impl-b")
    assert not MODULE._is_pe_specific_runtime("/opt/elis/repo")


def test_agent_worktree_map():
    """All canonical agents should map to fixed worktrees."""
    assert MODULE.AGENT_WORKTREE_MAP["pm"] == "/opt/elis/agent-worktrees/pm"
    assert (
        MODULE.AGENT_WORKTREE_MAP["infra-impl-b"]
        == "/opt/elis/agent-worktrees/infra-impl-b"
    )
    assert (
        MODULE.AGENT_WORKTREE_MAP["infra-val-a"]
        == "/opt/elis/agent-worktrees/infra-val-a"
    )


def test_agent_worktree_map_new_entries():
    """New agent worktree entries should be present."""
    assert "advisor" in MODULE.AGENT_WORKTREE_MAP
    assert MODULE.AGENT_WORKTREE_MAP["advisor"] == "/opt/elis/agent-worktrees/advisor"


def test_failure_class_taxonomy():
    """Failure-class taxonomy should include all blocking scenarios."""
    assert "WRONG_BRANCH" in MODULE.FAILURE_CLASSES
    assert "WRONG_HEAD" in MODULE.FAILURE_CLASSES
    assert "DIRTY_WORKTREE" in MODULE.FAILURE_CLASSES
    assert "MISSING_ORIGIN_REMOTE" in MODULE.FAILURE_CLASSES
    assert "CANONICAL_REPO_DIRTY_STATE_MASKING_ORIGIN" in MODULE.FAILURE_CLASSES
    assert "DETACHED_HEAD" in MODULE.FAILURE_CLASSES
    assert "MISSING_PE_TASK" in MODULE.FAILURE_CLASSES
    assert "DISPATCH_PATH_BLOCKED" in MODULE.FAILURE_CLASSES
    assert "DISPATCH_RECOVERY_BLOCKED" in MODULE.FAILURE_CLASSES
    assert "IMPLEMENTER_EXECUTION_BLOCKED" in MODULE.FAILURE_CLASSES
    assert "MISSING_RESET_ACK" in MODULE.FAILURE_CLASSES
    assert "SELF_FIX_ROUTING" in MODULE.FAILURE_CLASSES
    assert "UNCOMMITTED_MISREPORTED" in MODULE.FAILURE_CLASSES


def test_classify_failure():
    """classify_failure should return the correct label."""
    label = MODULE.classify_failure("WRONG_BRANCH")
    assert "WRONG_BRANCH" in label
    assert "Agent worktree is on an unexpected branch" in label

    label = MODULE.classify_failure("MISSING_ORIGIN_REMOTE")
    assert "MISSING_ORIGIN_REMOTE" in label

    label = MODULE.classify_failure("CANONICAL_REPO_DIRTY_STATE_MASKING_ORIGIN")
    assert "CANONICAL_REPO_DIRTY_STATE_MASKING_ORIGIN" in label

    label = MODULE.classify_failure("UNKNOWN_CODE")
    assert "UNKNOWN_FAILURE" in label


def test_check_forbidden_not_in_clean_worktree(tmp_path):
    """_check_forbidden_files_in_worktree should return empty for clean worktree."""
    (tmp_path / "README.md").write_text("clean")
    (tmp_path / ".elis/pe/PE-TEST").mkdir(parents=True)
    result = MODULE._check_forbidden_files_in_worktree(tmp_path)
    assert result == []


def test_untracked_or_dirty():
    """Common runtime/context files should be classified as protected."""
    is_protected, reason = MODULE._is_untracked_or_dirty("HEARTBEAT.md")
    assert is_protected
    assert "runtime/context" in reason

    is_protected, reason = MODULE._is_untracked_or_dirty("AGENTS.md")
    assert is_protected

    is_protected, reason = MODULE._is_untracked_or_dirty(".openclaw")
    assert is_protected

    is_protected, reason = MODULE._is_untracked_or_dirty("HANDOFF.md")
    assert not is_protected


def test_classify_failure_cli():
    """--classify flag should produce the correct output."""
    result = subprocess.run(
        ["python3", str(SCRIPT), "--classify", "DISPATCH_PATH_BLOCKED"],
        capture_output=True,
        text=True,
    )
    assert "DISPATCH_PATH_BLOCKED" in result.stdout
    assert result.returncode == 1

    result = subprocess.run(
        ["python3", str(SCRIPT), "--classify", "WRONG_BRANCH"],
        capture_output=True,
        text=True,
    )
    assert "WRONG_BRANCH" in result.stdout
    assert result.returncode == 1


def test_nonexistent_worktree_does_not_crash():
    """Running check_dispatch_binding.py with a nonexistent worktree should not crash."""
    repo = str(Path(__file__).resolve().parents[1])
    result = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--repo",
            repo,
            "--pe-id",
            "PE-OPS-PM-GUARDRAILS-02",
            "--branch",
            "feature/test",
            "--head",
            "deadbeef0123456789",
            "--worktree",
            "/tmp/nonexistent_dispatch_test",
            "--mode",
            "implementer",
        ],
        capture_output=True,
        text=True,
    )
    # Should exit non-zero (failure), not crash with traceback
    assert result.returncode != 0
    # Should mention WORKTREE_MISSING
    assert "WORKTREE_MISSING" in result.stderr or "WORKTREE_MISSING" in result.stdout


def test_nonexistent_worktree_validator():
    """Running check_dispatch_binding.py validator mode with nonexistent worktree."""
    repo = str(Path(__file__).resolve().parents[1])
    result = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--repo",
            repo,
            "--pe-id",
            "PE-OPS-PM-GUARDRAILS-02",
            "--head",
            "deadbeef0123456789",
            "--worktree",
            "/tmp/nonexistent_dispatch_test_val",
            "--mode",
            "validator",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0


def test_forbidden_files_in_worktree_detection():
    """check_dispatch_binding should detect forbidden runtime files in worktree."""
    assert hasattr(MODULE, "_check_forbidden_files_in_worktree")
    assert hasattr(MODULE, "FIXED_WORKTREE_FORBIDDEN")
    assert "HEARTBEAT.md" in MODULE.FIXED_WORKTREE_FORBIDDEN
    assert "SOUL.md" in MODULE.FIXED_WORKTREE_FORBIDDEN
    assert "TOOLS.md" in MODULE.FIXED_WORKTREE_FORBIDDEN
    assert "USER.md" in MODULE.FIXED_WORKTREE_FORBIDDEN
    assert "IDENTITY.md" in MODULE.FIXED_WORKTREE_FORBIDDEN
    assert (
        "AGENTS.md" not in MODULE.FIXED_WORKTREE_FORBIDDEN
    )  # AGENTS.md is allowed in worktree


def test_check_forbidden_files_in_worktree(tmp_path):
    """_check_forbidden_files_in_worktree should find runtime files in worktree."""
    (tmp_path / "HEARTBEAT.md").write_text("test")
    result = MODULE._check_forbidden_files_in_worktree(tmp_path)
    assert "HEARTBEAT.md" in result

    (tmp_path / ".openclaw").mkdir()
    result = MODULE._check_forbidden_files_in_worktree(tmp_path)
    assert "HEARTBEAT.md" in result
    assert ".openclaw" in result
