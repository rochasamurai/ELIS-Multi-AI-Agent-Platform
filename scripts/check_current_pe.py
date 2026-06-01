"""Validate CURRENT_PE.md for PE-AUTO-02."""

from __future__ import annotations

import os
import re
import sys
from importlib import import_module
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

agent_id_module = import_module("elis.agent_id")
engine_from_agent_id = agent_id_module.engine_from_agent_id
canonical_agent_id = agent_id_module.canonical_agent_id
workflow_state_machine = import_module("elis.workflow_state_machine")

VALID_ACTIVE_STATUSES = set(workflow_state_machine.ACTIVE_STATES)
VALID_REGISTRY_STATUSES = set(workflow_state_machine.CANONICAL_STATES)
PE_ID_RE = re.compile(r"^PE(?:-[A-Z0-9]+)+-[0-9]+$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
BRANCH_RE = re.compile(r"^(feature/pe-[a-z0-9-]+|chore/[a-z0-9-]+)$")
REQUIRED_RELEASE_FIELDS = ("Release", "Base branch", "Plan file", "Plan location")
REQUIRED_REGISTRY_COLUMNS = {
    "pe-id",
    "domain",
    "implementer-agentid",
    "validator-agentid",
    "branch",
    "status",
    "last-updated",
}
ENGINE_TO_AGENT = {
    "codex": {"CODEX", "slot-a"},
    "claude": {"Claude Code", "slot-b"},
    "gemini": {"Gemini CLI"},
}


def fail(message: str) -> int:
    print(f"ERROR: {message}")
    return 1


def _table_value(lines: list[str], field: str) -> str | None:
    for line in lines:
        parts = [part.strip() for part in line.split("|")]
        if len(parts) >= 4 and parts[1] == field:
            return parts[2]
    return None


def _table_block(lines: list[str], heading: str) -> list[str]:
    start = None
    for idx, line in enumerate(lines):
        if line.strip().lower() == heading.lower():
            start = idx + 1
            break

    if start is None:
        return []

    block: list[str] = []
    for line in lines[start:]:
        stripped = line.strip()
        if not stripped:
            if block:
                break
            continue
        if stripped.startswith("|"):
            block.append(stripped)
            continue
        if block:
            break
    return block


def _parse_roles(content: str) -> dict[str, str]:
    roles_block = _table_block(content.splitlines(), "## Agent roles")
    if len(roles_block) < 3:
        raise ValueError("Agent roles table missing or malformed.")

    roles: dict[str, str] = {}
    for raw in roles_block[2:]:
        parts = [part.strip() for part in raw.strip("|").split("|")]
        if len(parts) < 2:
            raise ValueError("Agent roles row is malformed.")
        agent, role = parts[0], parts[1]
        if role not in {"Implementer", "Validator"}:
            raise ValueError(f"Agent {agent} has invalid role '{role}'.")
        roles[agent] = role
    if len(roles) != 2:
        raise ValueError("Agent roles table must contain exactly two agent rows.")
    if set(roles.values()) != {"Implementer", "Validator"}:
        raise ValueError("Agent roles must contain one Implementer and one Validator.")
    return roles


def _parse_registry(content: str) -> tuple[list[str], list[dict[str, str]]]:
    block = _table_block(content.splitlines(), "## Active PE Registry")
    if len(block) < 3:
        raise ValueError("Active PE Registry table missing or malformed.")

    header = [part.strip().lower() for part in block[0].strip("|").split("|")]
    rows: list[dict[str, str]] = []
    for raw in block[2:]:
        values = [part.strip() for part in raw.strip("|").split("|")]
        if len(values) != len(header):
            raise ValueError("Active PE Registry row has wrong column count.")
        rows.append(dict(zip(header, values)))
    return header, rows


def _engine(agent_id: str) -> str | None:
    try:
        return engine_from_agent_id(agent_id)
    except ValueError:
        return None


def _validate_release_context(lines: list[str]) -> None:
    for field in REQUIRED_RELEASE_FIELDS:
        value = _table_value(lines, field)
        if not value:
            raise ValueError(f"Release context field '{field}' has no value.")


def _validate_current_pe(lines: list[str]) -> tuple[str, str]:
    pe = _table_value(lines, "PE")
    if not pe:
        raise ValueError("PE field missing or blank.")
    if pe == "—":
        branch = _table_value(lines, "Branch")
        if not branch:
            raise ValueError("Branch field missing or blank.")
        if branch != "—":
            raise ValueError(
                "Branch must also be '—' when CURRENT_PE.md is in plan-complete mode."
            )
        return pe, branch
    if not PE_ID_RE.fullmatch(pe):
        raise ValueError(f"PE field has invalid format: '{pe}'.")

    branch = _table_value(lines, "Branch")
    if not branch:
        raise ValueError("Branch field missing or blank.")
    if not BRANCH_RE.fullmatch(branch):
        raise ValueError(f"Branch has invalid format: '{branch}'.")
    return pe, branch


def _current_registry_row(
    pe: str, branch: str, rows: list[dict[str, str]]
) -> dict[str, str]:
    current = next((row for row in rows if row["pe-id"] == pe), None)
    if current is None:
        raise ValueError(f"Current PE '{pe}' not found in Active PE Registry.")
    if current["branch"] != branch:
        raise ValueError(
            "Current PE branch mismatch: "
            f"table has '{current['branch']}', expected '{branch}'."
        )
    return current


def _validate_status_and_date(current: dict[str, str]) -> None:
    status = current["status"].lower()
    if status not in VALID_REGISTRY_STATUSES:
        raise ValueError(f"Invalid registry status '{current['status']}'.")
    if status not in VALID_ACTIVE_STATUSES:
        raise ValueError(
            "Active PE status must be planning or implementing, "
            f"found '{current['status']}'."
        )
    if not DATE_RE.fullmatch(current["last-updated"]):
        raise ValueError(
            "Registry last-updated must be YYYY-MM-DD, "
            f"found '{current['last-updated']}'."
        )


def _validate_engines(current: dict[str, str]) -> tuple[str, str]:
    impl_engine = _engine(current["implementer-agentid"])
    val_engine = _engine(current["validator-agentid"])

    if impl_engine is None:
        raise ValueError(
            "Implementer agent id has no valid engine: "
            f"'{current['implementer-agentid']}'."
        )
    if val_engine is None:
        raise ValueError(
            "Validator agent id has no valid engine: "
            f"'{current['validator-agentid']}'."
        )
    if impl_engine == val_engine:
        raise ValueError("Implementer and validator must use opposite engines.")

    return impl_engine, val_engine


_WAIVER_REQUIRED_CLASSIFICATION = "OPS_AGENT_ALTERNATION_RULE_VIOLATION_AT_PE_OPENING"
_WAIVER_REQUIRED_STATUS = "GRANTED"
_WAIVER_REQUIRED_ONE_TIME_PHRASES = ("one-time, this pe only", "scope: one-time")
_WAIVER_REQUIRED_RULE_UNCHANGED_PHRASES = (
    "does not change the alternation rule globally",
    "not change the alternation rule globally",
)
_WAIVER_REQUIRED_PO_APPROVAL_PHRASES = ("approved by:",)


def _load_alternation_waiver(
    pe_id: str, current_pe_path: Path
) -> dict[str, str] | None:
    """Load and parse a PE-local alternation waiver file.

    Returns a dict of parsed fields, or None if no waiver file exists.
    Raises ValueError if the waiver file is present but malformed.
    """
    waiver_path = (
        current_pe_path.parent / ".elis" / "pe" / pe_id / "ALTERNATION_WAIVER.md"
    )
    if not waiver_path.exists():
        return None

    # Enforce: waiver must be inside .elis/pe/<PE_ID>/ relative to the repo root.
    try:
        waiver_path.relative_to(current_pe_path.parent / ".elis" / "pe" / pe_id)
    except ValueError:
        raise ValueError(
            f"Alternation waiver file is outside the required PE directory "
            f"'.elis/pe/{pe_id}/': '{waiver_path}'."
        )

    text = waiver_path.read_text(encoding="utf-8")
    # Strip markdown bold/italic markers before phrase matching
    plain = re.sub(r"\*{1,2}([^*]+)\*{1,2}", r"\1", text)
    lower = plain.lower()

    def _extract(pattern: str) -> str | None:
        m = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
        return m.group(1).strip() if m else None

    # PE ID from heading: # ALTERNATION WAIVER — <PE_ID>
    heading_pe = _extract(
        r"^#\s+ALTERNATION WAIVER\s+[—-]+\s+(\S+)",
    )
    # Classification
    classification = _extract(r"Classification:\s*(\S+)")
    # Waiver status (must start with GRANTED)
    waiver_status_raw = _extract(r"Waiver status:\s*(\S+)")
    # Actual implementer — strip backticks
    actual_impl = _extract(r"Actual implementer\s*\|?\s*[`']?([a-z][a-z0-9-]+[a-z0-9])")
    # Expected implementer
    expected_impl = _extract(
        r"Expected implementer[^|]*\|?\s*[`']?([a-z][a-z0-9-]+[a-z0-9])"
    )
    # Validator
    validator = _extract(r"Validator\s*\|?\s*[`']?([a-z][a-z0-9-]+[a-z0-9])")

    # Check one-time scope
    has_one_time = any(phrase in lower for phrase in _WAIVER_REQUIRED_ONE_TIME_PHRASES)
    # Check global rule unchanged statement
    has_rule_unchanged = any(
        phrase in lower for phrase in _WAIVER_REQUIRED_RULE_UNCHANGED_PHRASES
    )
    # Check PO approval recorded
    has_po_approval = any(
        phrase in lower for phrase in _WAIVER_REQUIRED_PO_APPROVAL_PHRASES
    )

    return {
        "heading_pe": heading_pe or "",
        "classification": classification or "",
        "waiver_status": waiver_status_raw or "",
        "actual_implementer": actual_impl or "",
        "expected_implementer": expected_impl or "",
        "validator": validator or "",
        "has_one_time_scope": has_one_time,
        "has_rule_unchanged": has_rule_unchanged,
        "has_po_approval": has_po_approval,
    }


def _validate_waiver_fields(
    waiver: dict[str, str],
    pe_id: str,
    current: dict[str, str],
) -> None:
    """Validate all required waiver fields match the active PE. Raises ValueError on mismatch."""
    errors: list[str] = []

    if waiver["heading_pe"] != pe_id:
        errors.append(
            f"Waiver PE ID '{waiver['heading_pe']}' does not match active PE '{pe_id}'."
        )
    if waiver["classification"] != _WAIVER_REQUIRED_CLASSIFICATION:
        errors.append(
            f"Waiver classification '{waiver['classification']}' is not "
            f"'{_WAIVER_REQUIRED_CLASSIFICATION}'."
        )
    if not waiver["waiver_status"].startswith(_WAIVER_REQUIRED_STATUS):
        errors.append(
            f"Waiver status '{waiver['waiver_status']}' is not '{_WAIVER_REQUIRED_STATUS}'."
        )
    impl_id = current.get("implementer-agentid", "")
    if waiver["actual_implementer"] != impl_id:
        errors.append(
            f"Waiver actual implementer '{waiver['actual_implementer']}' "
            f"does not match registry implementer '{impl_id}'."
        )
    val_id = current.get("validator-agentid", "")
    if waiver["validator"] != val_id:
        errors.append(
            f"Waiver validator '{waiver['validator']}' "
            f"does not match registry validator '{val_id}'."
        )
    # expected implementer must differ from actual
    if waiver["expected_implementer"] == impl_id:
        errors.append(
            f"Waiver expected implementer '{waiver['expected_implementer']}' "
            "must differ from actual implementer."
        )
    if not waiver["has_one_time_scope"]:
        errors.append("Waiver does not contain required one-time scope statement.")
    if not waiver["has_rule_unchanged"]:
        errors.append(
            "Waiver does not contain required statement that alternation rule is not changed globally."
        )
    if not waiver["has_po_approval"]:
        errors.append("Waiver does not contain required PO approval record.")

    if errors:
        raise ValueError("Alternation waiver fields invalid: " + "; ".join(errors))


def _validate_alternation(
    current: dict[str, str],
    rows: list[dict[str, str]],
    impl_engine: str,
    current_pe_path: Path | None = None,
) -> None:
    domain = current["domain"].strip().lower()
    merged_same_domain = [
        row
        for row in rows
        if row["domain"].strip().lower() == domain
        and row["status"].strip().lower() == "merged"
    ]
    if not merged_same_domain:
        return

    previous_engine = _engine(merged_same_domain[-1]["implementer-agentid"])
    if previous_engine is None:
        raise ValueError(
            "Previous merged implementer has no valid engine: "
            f"'{merged_same_domain[-1]['implementer-agentid']}'."
        )
    if previous_engine != impl_engine:
        return  # alternation valid — no waiver needed

    # Alternation violated — check for a valid PE-local waiver.
    pe_id = current.get("pe-id", "")
    if not pe_id:
        raise ValueError(
            "Alternation rule violated: current implementer engine matches "
            "the last merged PE in the same domain."
        )

    resolve_base = (
        current_pe_path if current_pe_path is not None else Path("CURRENT_PE.md")
    )
    waiver = _load_alternation_waiver(pe_id, resolve_base)
    if waiver is None:
        raise ValueError(
            "Alternation rule violated: current implementer engine matches "
            "the last merged PE in the same domain. "
            "No PE-local alternation waiver found."
        )

    _validate_waiver_fields(waiver, pe_id, current)
    print(
        f"WARNING: Alternation rule waiver accepted for {pe_id} "
        f"(classification: {waiver['classification']}, "
        f"actual implementer: {waiver['actual_implementer']}, "
        f"waiver status: {waiver['waiver_status']}). "
        "The general alternation rule is not changed."
    )


def _validate_roles_table(
    roles: dict[str, str],
    impl_engine: str,
    val_engine: str,
    impl_agent_id: str | None = None,
    val_agent_id: str | None = None,
) -> None:
    if impl_engine == val_engine:
        raise ValueError("Active PE registry engines are not opposite.")

    # Strategy 1: match by canonical agent ID from the registry directly.
    # Both the roles table and registry use the same naming convention
    # (<domain>-<role>-<slot>), so the canonical implementer-agentid from
    # the registry row should match the agent name in the roles table.
    canonical_impl = canonical_agent_id(impl_agent_id) if impl_agent_id else None
    canonical_val = canonical_agent_id(val_agent_id) if val_agent_id else None

    if canonical_impl and roles.get(canonical_impl) is not None:
        impl_match = roles[canonical_impl] == "Implementer"
    else:
        impl_match = None

    if canonical_val and roles.get(canonical_val) is not None:
        val_match = roles[canonical_val] == "Validator"
    else:
        val_match = None

    if impl_match is True and val_match is True:
        return  # Pass: canonical IDs matched.

    # Strategy 2: fall back to legacy ENGINE_TO_AGENT labels.
    expected_impl_agents = ENGINE_TO_AGENT.get(impl_engine)
    expected_val_agents = ENGINE_TO_AGENT.get(val_engine)
    if expected_impl_agents is None or expected_val_agents is None:
        missing_engine = impl_engine if expected_impl_agents is None else val_engine
        raise ValueError(
            f"Active PE registry engine '{missing_engine}' does not map "
            "to known agent labels."
        )
    if not any(roles.get(agent) == "Implementer" for agent in expected_impl_agents):
        raise ValueError(
            "Agent roles table does not match the active PE registry implementer."
        )
    if not any(roles.get(agent) == "Validator" for agent in expected_val_agents):
        raise ValueError(
            "Agent roles table does not match the active PE registry validator."
        )


def _is_dual_track(content: str) -> bool:
    return bool(re.search(r"^\|\s*Track A PE\s*\|", content, re.MULTILINE))


def _dual_track_value(content: str, field: str) -> str | None:
    """Extract a value from the dual-track Current PE table."""
    match = re.search(
        rf"^\|\s*{re.escape(field)}\s*\|\s*([^|]+?)\s*\|$",
        content,
        re.MULTILINE,
    )
    return match.group(1).strip() if match else None


def _validate_dual_track(content: str, lines: list[str]) -> None:
    """Validate dual-track CURRENT_PE.md structure (AC-4)."""
    track_a_pe = _dual_track_value(content, "Track A PE")
    track_a_branch = _dual_track_value(content, "Track A Branch")
    track_b_pe = _dual_track_value(content, "Track B PE")
    track_b_branch = _dual_track_value(content, "Track B Branch")

    for label, value in [
        ("Track A PE", track_a_pe),
        ("Track A Branch", track_a_branch),
        ("Track B PE", track_b_pe),
        ("Track B Branch", track_b_branch),
    ]:
        if not value:
            raise ValueError(f"Dual-track field '{label}' is missing or blank.")

    for label, value in [("Track A PE", track_a_pe), ("Track B PE", track_b_pe)]:
        if value and not PE_ID_RE.fullmatch(value):
            raise ValueError(f"Dual-track {label} has invalid format: '{value}'.")
    for label, value in [
        ("Track A Branch", track_a_branch),
        ("Track B Branch", track_b_branch),
    ]:
        if value and not BRANCH_RE.fullmatch(value):
            raise ValueError(f"Dual-track {label} has invalid format: '{value}'.")

    if track_a_pe == track_b_pe:
        raise ValueError(f"Track A and Track B refer to the same PE '{track_a_pe}'.")

    # Validate both tracks exist in the registry
    _, rows = _parse_registry(content)
    for pe_id, branch in [(track_a_pe, track_a_branch), (track_b_pe, track_b_branch)]:
        row = next((r for r in rows if r["pe-id"] == pe_id), None)
        if row is None:
            raise ValueError(
                f"Dual-track PE '{pe_id}' not found in Active PE Registry."
            )
        if row["branch"] != branch:
            raise ValueError(
                f"Dual-track branch mismatch for {pe_id}: "
                f"registry has '{row['branch']}', expected '{branch}'."
            )

    # Engines must differ (parallel tracks must use opposite engines)
    row_a = next(r for r in rows if r["pe-id"] == track_a_pe)
    row_b = next(r for r in rows if r["pe-id"] == track_b_pe)
    engine_a = _engine(row_a["implementer-agentid"])
    engine_b = _engine(row_b["implementer-agentid"])
    if engine_a is None or engine_b is None:
        raise ValueError("Cannot determine implementer engines for dual-track PEs.")
    if engine_a == engine_b:
        raise ValueError(
            f"Dual-track PEs {track_a_pe} and {track_b_pe} use the same "
            f"implementer engine ('{engine_a}'). Parallel tracks must use "
            "opposite engines."
        )

    # No mutual dependency — load plan file and check
    plan_file_value = _table_value(lines, "Plan file")
    plan_location_value = _table_value(lines, "Plan location")
    if plan_file_value:
        current_pe_parent = Path(
            os.environ.get("CURRENT_PE_PATH", "CURRENT_PE.md")
        ).parent
        plan_path = (
            current_pe_parent / plan_file_value
            if plan_location_value in {None, "repo root"}
            else current_pe_parent / plan_location_value / plan_file_value
        )
        if plan_path.exists():
            try:
                from scripts.check_parallel_eligibility import (  # noqa: PLC0415
                    check_eligibility,
                )
                from scripts.pe_sequencer import parse_plan  # noqa: PLC0415

                plan_pes = parse_plan(plan_path)
                eligible, reasons = check_eligibility(track_a_pe, track_b_pe, plan_pes)
                if not eligible:
                    raise ValueError(
                        f"Dual-track PEs {track_a_pe} and {track_b_pe} are not "
                        f"parallel-eligible: {'; '.join(reasons)}"
                    )
            except ImportError:
                pass  # Plan eligibility check unavailable — skip


def main() -> int:
    path = Path(os.environ.get("CURRENT_PE_PATH", "CURRENT_PE.md"))
    if not path.exists():
        return fail("CURRENT_PE.md not found.")

    content = path.read_text(encoding="utf-8")
    if not content.strip():
        return fail("CURRENT_PE.md is empty.")

    lines = content.splitlines()
    try:
        _validate_release_context(lines)

        # Dual-track mode: validate Track A + B structure (AC-4)
        if _is_dual_track(content):
            _validate_dual_track(content, lines)
            print(
                "CURRENT_PE.md OK — dual-track mode: "
                "release context, Track A/B structure, and engine eligibility valid."
            )
            return 0

        # Single-track mode: existing validation path
        pe, branch = _validate_current_pe(lines)
        if pe == "—" and branch == "—":
            print(
                "CURRENT_PE.md OK — release context valid and plan-complete mode is active."
            )
            return 0
        roles = _parse_roles(content)
        header, rows = _parse_registry(content)
        missing = sorted(REQUIRED_REGISTRY_COLUMNS.difference(header))
        if missing:
            raise ValueError(
                f"Active PE Registry columns missing: {', '.join(missing)}."
            )

        current = _current_registry_row(pe, branch, rows)
        _validate_status_and_date(current)
        impl_engine, val_engine = _validate_engines(current)
        _validate_alternation(current, rows, impl_engine, current_pe_path=path)
        _validate_roles_table(
            roles,
            impl_engine,
            val_engine,
            impl_agent_id=current["implementer-agentid"],
            val_agent_id=current["validator-agentid"],
        )
    except ValueError as exc:
        return fail(str(exc))

    print("CURRENT_PE.md OK — release context, roles, registry, and alternation valid.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
