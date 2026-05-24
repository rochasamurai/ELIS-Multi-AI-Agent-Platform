#!/usr/bin/env python3
"""check_reset_ack.py — enforce reset/binding acknowledgement before dispatch.

The NO_RESET_ACK_NO_DISPATCH rule: no agent may be dispatched unless it has
returned a complete reset/binding acknowledgement.

Required acknowledgement fields:
  - agent identity
  - PE ID
  - target worktree/path
  - branch
  - starting HEAD
  - timestamp
  - channel/thread binding (if applicable)
  - confirmation prior runtime context was discarded
  - confirmation it will write only within authorised worktree/scope

The acknowledgement is sought from:
  1. EVIDENCE_PATH env var — explicit evidence file
  2. .elis/pe/<PE_ID>/evidence/ directory for reset_ack marks

Usage:
  python scripts/check_reset_ack.py --pe-id PE-OPS-WORKTREE-BINDING-02 --agent infra-impl-b

Exit codes:
  0 — reset acknowledgement found and valid
  1 — reset acknowledgement missing or invalid
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


def _find_evidence_path(pe_id: str, agent_id: str) -> Path | None:
    """Look for reset_ack evidence file in the PE evidence directory."""
    evidence_dir = Path(f".elis/pe/{pe_id}/evidence")
    if evidence_dir.is_dir():
        for f in evidence_dir.iterdir():
            if f.is_file() and "reset_ack" in f.name and agent_id in f.name:
                return f
    return None


def _check_handoff_for_ack(pe_id: str, agent_id: str) -> dict | None:
    """Look for a Reset Acknowledgement section in HANDOFF.md."""
    handoff_path = Path("HANDOFF.md")
    if not handoff_path.exists():
        return None

    content = handoff_path.read_text(encoding="utf-8")

    # Search for acknowledgement sections. Accept flexible header patterns.
    patterns = [
        r"##\s+Reset Acknowledgement.*?(?=##|\Z)",
        rf"##\s+{re.escape(agent_id)}\s+Reset Acknowledgement.*?(?=##|\Z)",
    ]

    for pattern in patterns:
        match = re.search(pattern, content, re.DOTALL)
        if match:
            section_text = match.group(0)
            return _parse_ack_section(section_text, agent_id)

    return None


def _parse_ack_section(section_text: str, agent_id: str) -> dict | None:
    """Parse table-like or field-like content from an acknowledgement section."""
    data: dict[str, str] = {}

    # Match pipe-delimited table rows: | key | value |
    table_matches = re.findall(r"\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|", section_text)
    for key, value in table_matches:
        data[key.strip().lower()] = value.strip()

    # Match key: value pairs (inline, not in a table)
    kv_matches = re.findall(
        r"^\s*[-*]?\s*(.+?)\s*:\s*(.+)$", section_text, re.MULTILINE
    )
    for key, value in kv_matches:
        data[key.strip().lower()] = value.strip()

    return data if data else None


def _check_json_evidence_file(path: Path, agent_id: str) -> tuple[bool, list[str]]:
    """Validate a JSON reset acknowledgement file."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return False, ["Invalid JSON in evidence file."]

    return _validate_ack_data(data, agent_id)


def _validate_ack_data(data: dict, agent_id: str) -> tuple[bool, list[str]]:
    """Validate a reset acknowledgement data dictionary."""
    required_fields = [
        ("agent", "agent identity"),
        ("pe", "PE ID"),
        ("worktree", "target worktree/path"),
        ("branch", "branch"),
        ("head", "starting HEAD"),
        ("timestamp", "timestamp"),
    ]

    missing_fields: list[str] = []
    issues: list[str] = []

    for field_key, field_label in required_fields:
        value = data.get(field_key, "")
        if not value or str(value).strip() in ("", "null", "None"):
            missing_fields.append(field_label)

    if missing_fields:
        issues.append(f"Missing required fields: {', '.join(missing_fields)}")

    # Verify agent identity
    actual_agent = str(data.get("agent", ""))
    if actual_agent.strip().lower() != agent_id.lower():
        issues.append(
            f"Agent identity mismatch: expected '{agent_id}', got '{actual_agent}'"
        )

    # Verify discard confirmation
    discard_confirmed = data.get("prior_context_discarded", data.get("discard", ""))
    if str(discard_confirmed).strip().lower() not in ("yes", "true", "confirmed"):
        issues.append("Prior runtime context discard not confirmed.")

    # Verify write scope
    write_scope = data.get("write_scope", data.get("write_scope_confirmed", ""))
    if not write_scope or str(write_scope).strip().lower() not in (
        "yes",
        "true",
        "confirmed",
    ):
        issues.append("Write scope within authorised worktree not confirmed.")

    return len(issues) == 0, issues


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check reset acknowledgement before dispatch."
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
        help="Explicit path to a reset acknowledgement evidence file.",
    )
    args = parser.parse_args()

    pe_id = args.pe_id
    agent_id = args.agent

    print(f"Checking reset acknowledgement for {agent_id} / {pe_id}...")
    print()

    # Resolution order: explicit path → evidence dir
    ack_data: dict | None = None
    source: str = ""

    if args.evidence_path:
        ep = Path(args.evidence_path)
        if ep.exists():
            if ep.suffix == ".json":
                valid, issues = _check_json_evidence_file(ep, agent_id)
                if valid:
                    ack_data = json.loads(ep.read_text(encoding="utf-8"))
                    source = str(ep)
                else:
                    print(f"EVIDENCE FILE FAILED: {ep}")
                    for i in issues:
                        print(f"  FAIL: {i}")
                    return 1
            else:
                if ep.name == "HANDOFF.md":
                    print(
                        "FAIL: HANDOFF.md is not accepted as reset acknowledgement evidence."
                    )
                    return 1
                # Non-JSON file: try as markdown
                content = ep.read_text(encoding="utf-8")
                ack_data = _parse_ack_section(content, agent_id)
                source = str(ep)
        else:
            print(f"FAIL: Evidence path not found: {args.evidence_path}")
            return 1

    if ack_data is None:
        evidence_file = _find_evidence_path(pe_id, agent_id)
        if evidence_file:
            if evidence_file.suffix == ".json":
                valid, issues = _check_json_evidence_file(evidence_file, agent_id)
                if valid:
                    ack_data = json.loads(evidence_file.read_text(encoding="utf-8"))
                    source = str(evidence_file)
                else:
                    print(f"EVIDENCE FILE FAILED: {evidence_file}")
                    for i in issues:
                        print(f"  FAIL: {i}")
                    return 1
            else:
                content = evidence_file.read_text(encoding="utf-8")
                ack_data = _parse_ack_section(content, agent_id)
                source = str(evidence_file)

    if ack_data is None:
        handoff_path = Path("HANDOFF.md")
        if handoff_path.exists():
            print("FAIL: HANDOFF.md is not accepted as reset acknowledgement evidence.")
            return 1

    if ack_data is None:
        print("FAIL: No reset acknowledgement found.")
        print()
        print("Checked locations:")
        if args.evidence_path:
            print(f"  - explicit path: {args.evidence_path}")
        print(f"  - .elis/pe/{pe_id}/evidence/reset_ack_*")
        print("  - runtime evidence exported via EVIDENCE_PATH")
        print()
        print("NO_RESET_ACK_NO_DISPATCH gate: DISPATCH PROHIBITED.")
        return 1

    valid, issues = _validate_ack_data(ack_data, agent_id)
    print(f"Source: {source}")
    print()
    if valid:
        print(f"Reset acknowledgement VALID for {agent_id}.")
        print(f"  PE: {ack_data.get('pe', '(unknown)')}")
        print(f"  Agent: {ack_data.get('agent', '(unknown)')}")
        print(f"  Worktree: {ack_data.get('worktree', '(unknown)')}")
        print(f"  Branch: {ack_data.get('branch', '(unknown)')}")
        print(f"  HEAD: {ack_data.get('head', '(unknown)')}")
        print(f"  Timestamp: {ack_data.get('timestamp', '(unknown)')}")
        print()
        print("NO_RESET_ACK_NO_DISPATCH gate: PASS — dispatch allowed.")
        return 0
    else:
        print(f"Reset acknowledgement INVALID for {agent_id}:")
        for i in issues:
            print(f"  FAIL: {i}")
        print()
        print("NO_RESET_ACK_NO_DISPATCH gate: DISPATCH PROHIBITED.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
