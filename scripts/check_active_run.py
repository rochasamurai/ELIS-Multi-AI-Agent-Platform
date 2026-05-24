#!/usr/bin/env python3
"""check_active_run.py — enforce active-run evidence before status reports.

The NO_ACTIVE_RUN_EVIDENCE_NO_IN_PROGRESS_STATUS rule:
PM must not claim an agent is working (status 'implementing' or 'validating')
unless there is live active run/session evidence.

Required evidence:
  - active run/session id
  - correct agent
  - correct PE
  - correct worktree
  - correct branch
  - last activity timestamp
  - status: running or in_progress

If no active run evidence is present, status must be one of:
  NOT_STARTED, STALLED, FAILED, INCONCLUSIVE

Source of truth resolution order:
  1. EVIDENCE_PATH env var — explicit evidence file
  2. .elis/pe/<PE_ID>/evidence/active_run_<agent_id>.md

Usage:
  python scripts/check_active_run.py --pe-id PE-OPS-WORKTREE-BINDING-02 --agent infra-impl-b

Exit codes:
  0 — active run evidence found, plausible
  1 — no active run evidence
  2 — evidence found but invalid (wrong agent/PE/branch)
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


def _find_evidence_file(pe_id: str, agent_id: str) -> Path | None:
    """Look for active run evidence file in PE evidence directory."""
    evidence_dir = Path(f".elis/pe/{pe_id}/evidence")
    if evidence_dir.is_dir():
        for f in evidence_dir.iterdir():
            if f.is_file() and "active_run" in f.name and agent_id in f.name:
                return f
    return None


def _check_handoff_for_evidence(pe_id: str, agent_id: str) -> dict | None:
    """Look for Active Run Evidence section in HANDOFF.md."""
    handoff_path = Path("HANDOFF.md")
    if not handoff_path.exists():
        return None

    content = handoff_path.read_text(encoding="utf-8")
    patterns = [
        r"##\s+Active Run Evidence.*?(?=##|\Z)",
        r"##\s+Active.*Run.*Evidence.*?(?=##|\Z)",
    ]
    for pattern in patterns:
        match = re.search(pattern, content, re.DOTALL)
        if match:
            section_text = match.group(0)
            return _parse_evidence_section(section_text)
    return None


def _parse_evidence_section(section_text: str) -> dict | None:
    """Parse table-like or field-like content from an evidence section."""
    data: dict[str, str] = {}
    table_matches = re.findall(r"\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|", section_text)
    for key, value in table_matches:
        data[key.strip().lower()] = value.strip()
    kv_matches = re.findall(
        r"^\s*[-*]?\s*(.+?)\s*:\s*(.+)$", section_text, re.MULTILINE
    )
    for key, value in kv_matches:
        data[key.strip().lower()] = value.strip()
    return data if data else None


def _parse_json_or_md_file(path: Path) -> dict | None:
    """Parse a JSON or markdown evidence file."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else None
    except (json.JSONDecodeError, UnicodeDecodeError):
        pass

    content = path.read_text(encoding="utf-8")
    return _parse_evidence_section(content)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check active run evidence before allowing in-progress status."
    )
    parser.add_argument(
        "--pe-id",
        required=True,
        help="PE ID (e.g. PE-OPS-WORKTREE-BINDING-02).",
    )
    parser.add_argument(
        "--agent",
        required=True,
        help="Agent ID (e.g. infra-impl-b).",
    )
    parser.add_argument(
        "--evidence-path",
        default=None,
        help="Explicit path to active run evidence file.",
    )
    args = parser.parse_args()

    pe_id = args.pe_id
    agent_id = args.agent

    print(f"Checking active run evidence for {agent_id} / {pe_id}...")
    print()

    evidence_data: dict | None = None
    source: str = ""

    # Resolution order: explicit evidence path → evidence directory
    if args.evidence_path:
        ep = Path(args.evidence_path)
        if ep.exists():
            if ep.name == "HANDOFF.md":
                print("FAIL: HANDOFF.md is not accepted as active run evidence.")
                return 1
            evidence_data = _parse_json_or_md_file(ep)
            source = str(ep)
        else:
            print(f"FAIL: Evidence path not found: {args.evidence_path}")
            return 1

    if evidence_data is None:
        evidence_file = _find_evidence_file(pe_id, agent_id)
        if evidence_file:
            evidence_data = _parse_json_or_md_file(evidence_file)
            source = str(evidence_file)

    if evidence_data is None:
        handoff_path = Path("HANDOFF.md")
        if handoff_path.exists():
            print("FAIL: HANDOFF.md is not accepted as active run evidence.")
            return 1

    if evidence_data is None:
        print("FAIL: No active run evidence found.")
        print()
        print("Checked locations:")
        if args.evidence_path:
            print(f"  - explicit path: {args.evidence_path}")
        print(f"  - .elis/pe/{pe_id}/evidence/active_run_{agent_id}.*")
        print("  - runtime evidence exported via EVIDENCE_PATH")
        print()
        print(
            "NO_ACTIVE_RUN_EVIDENCE_NO_IN_PROGRESS_STATUS gate: "
            "Cannot claim in-progress status. "
            "Status must be one of: NOT_STARTED, STALLED, FAILED, INCONCLUSIVE."
        )
        return 1

    print(f"Source: {source}")
    print()

    # Validate
    issues: list[str] = []

    session_id = evidence_data.get("session_id", evidence_data.get("run_id", ""))
    if not session_id or str(session_id).strip() in ("", "null", "None"):
        issues.append("Missing active run/session ID.")

    actual_agent = evidence_data.get("agent", evidence_data.get("agent_id", ""))
    if actual_agent and str(actual_agent).strip().lower() != agent_id.lower():
        issues.append(
            f"Agent mismatch: evidence is for '{actual_agent}', "
            f"expected '{agent_id}'."
        )

    actual_pe = evidence_data.get("pe", evidence_data.get("pe_id", ""))
    if actual_pe and str(actual_pe).strip() != pe_id:
        issues.append(
            f"PE mismatch: evidence is for '{actual_pe}', expected '{pe_id}'."
        )

    status = evidence_data.get("status", "")
    valid_statuses = {"running", "in_progress"}
    status_text = str(status).strip().lower()
    if status_text not in valid_statuses:
        issues.append(f"Active run status is not live: {status_text or '(missing)'}")

    timestamp = evidence_data.get("timestamp", evidence_data.get("last_activity", ""))
    if not timestamp or str(timestamp).strip() in ("", "null", "None"):
        issues.append("Missing activity timestamp.")

    if issues:
        print("Active run evidence INVALID:")
        for issue in issues:
            print(f"  FAIL: {issue}")
        return 2

    print("Active run evidence VALID.")
    print(f"  Session: {session_id}")
    print(f"  Agent: {actual_agent}")
    print(f"  PE: {actual_pe}")
    print(f"  Status: {status or '(not reported)'}")
    print(f"  Timestamp: {timestamp or '(not reported)'}")
    print()
    print(
        "NO_ACTIVE_RUN_EVIDENCE_NO_IN_PROGRESS_STATUS gate: "
        "PASS — in-progress status allowed."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
