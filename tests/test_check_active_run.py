#!/usr/bin/env python3
"""Tests for scripts/check_active_run.py."""

from __future__ import annotations

import importlib.util
import tempfile
import json
import subprocess
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "check_active_run.py"


def _load():
    spec = importlib.util.spec_from_file_location("check_active_run", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


MODULE = _load()

SAMPLE_VALID_EVIDENCE = {
    "session_id": "agent:infra-impl-b:subagent:abc123",
    "agent": "infra-impl-b",
    "pe": "PE-OPS-WORKTREE-BINDING-02",
    "worktree": "/opt/elis/agent-worktrees/infra-impl-b",
    "branch": "feature/pe-ops-worktree-binding-02-enforce-fixed-worktree-dispatch-gates",
    "status": "running",
    "timestamp": "2026-05-09T22:00:00+01:00",
}


def test_script_no_evidence():
    """No evidence should exit 1."""
    with tempfile.TemporaryDirectory() as tmpdir:
        result = subprocess.run(
            [str(SCRIPT), "--pe-id", "PE-NO-EVIDENCE-01", "--agent", "infra-impl-b"],
            capture_output=True,
            text=True,
            cwd=tmpdir,
            timeout=30,
        )
        assert result.returncode == 1
        assert "No active run evidence found" in result.stdout


def test_script_with_json_evidence(tmp_path):
    """A JSON evidence file should pass."""
    cwd = Path(tmp_path)
    ev_dir = cwd / ".elis" / "pe" / "PE-OPS-WORKTREE-BINDING-02" / "evidence"
    ev_dir.mkdir(parents=True)
    ev_file = ev_dir / "active_run_infra-impl-b.json"
    ev_file.write_text(json.dumps(SAMPLE_VALID_EVIDENCE))

    result = subprocess.run(
        [
            str(SCRIPT),
            "--pe-id",
            "PE-OPS-WORKTREE-BINDING-02",
            "--agent",
            "infra-impl-b",
        ],
        capture_output=True,
        text=True,
        cwd=str(cwd),
        timeout=30,
    )
    assert (
        result.returncode == 0
    ), f"Expected 0, got {result.returncode}\n{result.stdout}"
    assert "Active run evidence VALID" in result.stdout


def test_script_with_explicit_evidence_path(tmp_path):
    """Explicit evidence path should work."""
    ev_file = tmp_path / "active_run_evidence.json"
    ev_file.write_text(json.dumps(SAMPLE_VALID_EVIDENCE))

    result = subprocess.run(
        [
            str(SCRIPT),
            "--pe-id",
            "PE-OPS-WORKTREE-BINDING-02",
            "--agent",
            "infra-impl-b",
            "--evidence-path",
            str(ev_file),
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert (
        result.returncode == 0
    ), f"Expected 0, got {result.returncode}\n{result.stdout}"
    assert "Active run evidence VALID" in result.stdout


def test_script_with_wrong_agent(tmp_path):
    """Wrong agent in evidence should exit 2."""
    ev_file = tmp_path / "active_run_evidence.json"
    data = {**SAMPLE_VALID_EVIDENCE, "agent": "infra-impl-a"}
    ev_file.write_text(json.dumps(data))

    result = subprocess.run(
        [
            str(SCRIPT),
            "--pe-id",
            "PE-ACTIVE-TEST",
            "--agent",
            "infra-impl-b",
            "--evidence-path",
            str(ev_file),
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 2
    assert "Agent mismatch" in result.stdout


def test_script_with_wrong_pe(tmp_path):
    """Wrong PE in evidence should exit 2."""
    ev_file = tmp_path / "active_run_evidence.json"
    data = {**SAMPLE_VALID_EVIDENCE, "pe": "PE-WRONG-01"}
    ev_file.write_text(json.dumps(data))

    result = subprocess.run(
        [
            str(SCRIPT),
            "--pe-id",
            "PE-ACTIVE-TEST",
            "--agent",
            "infra-impl-b",
            "--evidence-path",
            str(ev_file),
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 2
    assert "PE mismatch" in result.stdout


def test_handoff_evidence_detection(tmp_path):
    """Active run evidence in HANDOFF.md should be rejected."""
    cwd = Path(tmp_path)
    handoff = cwd / "HANDOFF.md"
    handoff.write_text(
        "## Active Run Evidence\n\n"
        "| Field | Value |\n"
        "|-------|-------|\n"
        "| session_id | agent:infra-impl-b:run:xyz789 |\n"
        "| agent | infra-impl-b |\n"
        "| pe | PE-HANDOFF-TEST |\n"
        "| status | running |\n"
        "| timestamp | 2026-05-09T22:05:00Z |\n"
    )

    result = subprocess.run(
        [str(SCRIPT), "--pe-id", "PE-HANDOFF-TEST", "--agent", "infra-impl-b"],
        capture_output=True,
        text=True,
        cwd=str(cwd),
        timeout=30,
    )
    assert (
        result.returncode != 0
    ), f"Expected failure, got {result.returncode}\n{result.stdout}\n{result.stderr}"
    assert "HANDOFF.md" in result.stdout or "HANDOFF.md" in result.stderr


def test_missing_session_id():
    """Missing session ID should fail validation."""
    data = {**SAMPLE_VALID_EVIDENCE, "session_id": ""}
    # Simulate by checking logic directly
    ev_file = Path(tempfile.mktemp(suffix=".json"))
    try:
        ev_file.write_text(json.dumps(data))
        result = subprocess.run(
            [
                str(SCRIPT),
                "--pe-id",
                "PE-TEST",
                "--agent",
                "infra-impl-b",
                "--evidence-path",
                str(ev_file),
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 2
    finally:
        ev_file.unlink(missing_ok=True)


def test_missing_timestamp():
    """Missing timestamp should fail validation."""
    data = {**SAMPLE_VALID_EVIDENCE, "timestamp": ""}
    ev_file = Path(tempfile.mktemp(suffix=".json"))
    try:
        ev_file.write_text(json.dumps(data))
        result = subprocess.run(
            [
                str(SCRIPT),
                "--pe-id",
                "PE-TEST",
                "--agent",
                "infra-impl-b",
                "--evidence-path",
                str(ev_file),
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 2
    finally:
        ev_file.unlink(missing_ok=True)
