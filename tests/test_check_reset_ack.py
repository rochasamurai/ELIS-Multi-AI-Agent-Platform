#!/usr/bin/env python3
"""Tests for scripts/check_reset_ack.py."""

from __future__ import annotations

import importlib.util
import tempfile
import json
import subprocess
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "check_reset_ack.py"


def _load():
    spec = importlib.util.spec_from_file_location("check_reset_ack", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


MODULE = _load()

SAMPLE_VALID_ACK_DATA = {
    "agent": "infra-impl-b",
    "pe": "PE-OPS-WORKTREE-BINDING-02",
    "worktree": "/opt/elis/agent-worktrees/infra-impl-b",
    "branch": "feature/pe-ops-worktree-binding-02-enforce-fixed-worktree-dispatch-gates",
    "head": "e5d3afc733ef7e4a3dc429cff63aa0f583100ccf",
    "timestamp": "2026-05-09T22:00:00+01:00",
    "prior_context_discarded": "yes",
    "write_scope": "yes",
}


def test_validate_valid_ack_data():
    """A complete, valid acknowledgement should pass validation."""
    valid, issues = MODULE._validate_ack_data(SAMPLE_VALID_ACK_DATA, "infra-impl-b")
    assert valid, f"Expected valid, got issues: {issues}"
    assert len(issues) == 0


def test_validate_missing_agent():
    """Missing agent identity should fail."""
    data = {**SAMPLE_VALID_ACK_DATA, "agent": ""}
    valid, issues = MODULE._validate_ack_data(data, "infra-impl-b")
    assert not valid
    assert any("agent identity" in i for i in issues)


def test_validate_wrong_agent():
    """Wrong agent identity should fail."""
    data = {**SAMPLE_VALID_ACK_DATA, "agent": "infra-impl-a"}
    valid, issues = MODULE._validate_ack_data(data, "infra-impl-b")
    assert not valid
    assert any("Agent identity mismatch" in i for i in issues)


def test_validate_missing_pe_id():
    """Missing PE ID should fail."""
    data = {**SAMPLE_VALID_ACK_DATA, "pe": ""}
    valid, issues = MODULE._validate_ack_data(data, "infra-impl-b")
    assert not valid
    assert any("PE ID" in i for i in issues)


def test_validate_missing_worktree():
    """Missing worktree path should fail."""
    data = {**SAMPLE_VALID_ACK_DATA, "worktree": ""}
    valid, issues = MODULE._validate_ack_data(data, "infra-impl-b")
    assert not valid
    assert any("worktree" in i for i in issues)


def test_validate_missing_branch():
    """Missing branch should fail."""
    data = {**SAMPLE_VALID_ACK_DATA, "branch": ""}
    valid, issues = MODULE._validate_ack_data(data, "infra-impl-b")
    assert not valid
    assert any("branch" in i for i in issues)


def test_validate_missing_head():
    """Missing HEAD should fail."""
    data = {**SAMPLE_VALID_ACK_DATA, "head": ""}
    valid, issues = MODULE._validate_ack_data(data, "infra-impl-b")
    assert not valid
    assert any("starting HEAD" in i for i in issues)


def test_validate_missing_discard_confirmation():
    """Missing prior context discard confirmation should fail."""
    data = {**SAMPLE_VALID_ACK_DATA, "prior_context_discarded": ""}
    valid, issues = MODULE._validate_ack_data(data, "infra-impl-b")
    assert not valid
    assert any("discard not confirmed" in i or "not confirmed" in i for i in issues)


def test_validate_missing_timestamp():
    """Missing timestamp should fail."""
    data = {**SAMPLE_VALID_ACK_DATA, "timestamp": ""}
    valid, issues = MODULE._validate_ack_data(data, "infra-impl-b")
    assert not valid
    assert any("timestamp" in i for i in issues)


def test_validate_accepts_alternative_keys():
    """Should accept 'discard' and 'write_scope_confirmed' as alternative keys."""
    data = {
        "agent": "infra-impl-b",
        "pe": "PE-OPS-WORKTREE-BINDING-02",
        "worktree": "/opt/elis/agent-worktrees/infra-impl-b",
        "branch": "feature/pe-ops-worktree-binding-02-enforce-fixed-worktree-dispatch-gates",
        "head": "e5d3afc733ef7e4a3dc429cff63aa0f583100ccf",
        "timestamp": "2026-05-09T22:00:00+01:00",
        "discard": "confirmed",
        "write_scope_confirmed": "true",
    }
    valid, issues = MODULE._validate_ack_data(data, "infra-impl-b")
    assert valid, f"Expected valid with alt keys, got: {issues}"


def test_json_evidence_file(tmp_path):
    """A valid JSON evidence file should be parseable."""
    evidence_path = tmp_path / "reset_ack_infra-impl-b.json"
    evidence_path.write_text(json.dumps(SAMPLE_VALID_ACK_DATA))
    valid, issues = MODULE._check_json_evidence_file(evidence_path, "infra-impl-b")
    assert valid, f"Expected valid, got: {issues}"


def test_json_evidence_file_invalid_json(tmp_path):
    """Invalid JSON should fail parsing."""
    evidence_path = tmp_path / "reset_ack_infra-impl-b.json"
    evidence_path.write_text("not valid json}{")
    valid, issues = MODULE._check_json_evidence_file(evidence_path, "infra-impl-b")
    assert not valid


def test_find_evidence_path(tmp_path):
    """Evidence file should be found by name pattern."""
    import os as _os

    with tempfile.TemporaryDirectory() as tmpdir:
        ev_dir = Path(tmpdir) / ".elis" / "pe" / "PE-TEST-01" / "evidence"
        ev_dir.mkdir(parents=True)
        (ev_dir / "reset_ack_infra-impl-b.json").write_text("{}")

        with tempfile.TemporaryDirectory() as tmpdir2:
            test_cwd = Path(tmpdir2)
            pe_ev_path = test_cwd / ".elis" / "pe" / "PE-TEST-01" / "evidence"
            pe_ev_path.mkdir(parents=True)
            (pe_ev_path / "reset_ack_infra-impl-b.json").write_text("{}")
            orig_cwd = Path.cwd()
            try:
                _os.chdir(str(test_cwd))
                found = MODULE._find_evidence_path("PE-TEST-01", "infra-impl-b")
                assert found is not None
                assert "reset_ack_infra-impl-b.json" in str(found)
            finally:
                _os.chdir(str(orig_cwd))


def test_script_without_evidence():
    """Calling the script without evidence should exit 1."""
    with tempfile.TemporaryDirectory() as tmpdir:
        result = subprocess.run(
            [str(SCRIPT), "--pe-id", "PE-NO-EVIDENCE-01", "--agent", "infra-impl-b"],
            capture_output=True,
            text=True,
            cwd=tmpdir,
            timeout=30,
        )
        assert result.returncode == 1
        assert "No reset acknowledgement found" in result.stdout


def test_script_with_inline_handoff_ack(tmp_path):
    """Script should reject acknowledgement in HANDOFF.md."""
    cwd = Path(tmp_path)
    handoff = cwd / "HANDOFF.md"
    handoff.write_text(
        "## Reset Acknowledgement\n\n"
        "| Field | Value |\n"
        "|-------|-------|\n"
        "| agent | infra-impl-b |\n"
        "| pe | PE-TEST-02 |\n"
        "| worktree | /opt/elis/agent-worktrees/infra-impl-b |\n"
        "| branch | feature/test-branch |\n"
        "| head | abc123def456 |\n"
        "| timestamp | 2026-05-09T22:00:00Z |\n"
        "| prior_context_discarded | yes |\n"
        "| write_scope | yes |\n"
    )
    result = subprocess.run(
        [str(SCRIPT), "--pe-id", "PE-TEST-02", "--agent", "infra-impl-b"],
        capture_output=True,
        text=True,
        cwd=str(cwd),
        timeout=30,
    )
    assert result.returncode != 0, (
        f"Expected failure, got {result.returncode}\n{result.stdout}\n{result.stderr}"
    )
    assert "HANDOFF.md" in result.stdout or "HANDOFF.md" in result.stderr
