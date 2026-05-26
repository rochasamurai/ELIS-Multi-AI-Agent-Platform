#!/usr/bin/env python3
"""Contract tests for the current PE opening packet."""

from __future__ import annotations

import json
from pathlib import Path


ACTIVE_MARKERS = (
    "PE-OPS-CURRENT-PE-STATE-01",
    "feature/pe-ops-current-pe-state-01",
    "infra-impl-b",
    "infra-val-a",
    "planning / awaiting implementer dispatch",
)

CLOSEOUT_MARKERS = (
    "PE-OPS-CURRENT-PE-STATE-01",
    "plan-complete / no active PE",
    "merged on `origin/main`",
    "| PE      | — |",
    "| Branch  | — |",
    "| — | — |",
    "no active PE roles",
)

A2A_RUNTIME_ACTIVE_MARKERS = (
    "PE-OPS-A2A-RUNTIME-01",
    "feature/pe-ops-a2a-runtime-01-clean-local-backbone",
    "infra-impl-a",
    "infra-val-a",
    "gate-2-pending",
)


def _matches_active_state(text: str) -> bool:
    return all(marker in text for marker in ACTIVE_MARKERS)


def _matches_closeout_state(text: str) -> bool:
    return all(marker in text for marker in CLOSEOUT_MARKERS)


def _matches_a2a_runtime_active_state(text: str) -> bool:
    return all(marker in text for marker in A2A_RUNTIME_ACTIVE_MARKERS)


def test_current_pe_marks_the_active_pe_and_roles() -> None:
    text = Path("CURRENT_PE.md").read_text(encoding="utf-8")

    assert (
        _matches_active_state(text)
        or _matches_closeout_state(text)
        or _matches_a2a_runtime_active_state(text)
    )


def test_current_pe_state_file_matches_current_pe_md() -> None:
    current_state = json.loads(
        Path(".elis/state/current_pe.json").read_text(encoding="utf-8")
    )
    text = Path("CURRENT_PE.md").read_text(encoding="utf-8")

    assert current_state["pe_id"] in text
    assert current_state["branch"] in text
    assert current_state["implementer"] in text
    assert current_state["validator"] in text
    assert current_state["current_state"] in text


def test_pe_task_documents_scope_and_state_model() -> None:
    text = Path(".elis/pe/PE-OPS-CURRENT-PE-STATE-01/PE_TASK.md").read_text(
        encoding="utf-8"
    )

    assert "Move canonical PE machine state out of `CURRENT_PE.md`" in text
    assert ".elis/state/current_pe.json" in text
    assert "schemas/current_pe.schema.json" in text
    assert "`CURRENT_PE.md` becomes a validated human-readable summary only." in text
    assert (
        "`scripts/check_current_pe.py` validates schema + JSON/CURRENT_PE consistency."
        in text
    )


def test_handoff_contains_current_state_and_opening_constraints() -> None:
    text = Path(".elis/pe/PE-OPS-CURRENT-PE-STATE-01/HANDOFF.md").read_text(
        encoding="utf-8"
    )

    assert "opening-complete-awaiting-dispatch" in text
    assert "PE-OPS-CURRENT-PE-STATE-01" in text
    assert "infra-impl-b" in text
    assert "infra-val-a" in text
    assert "No runtime/config/auth/service changes" in text
    assert "No service restart" in text


def test_governance_doc_states_the_state_model() -> None:
    text = Path("docs/governance/ELIS_Current_PE_State_Model.md").read_text(
        encoding="utf-8"
    )

    assert "structured machine-readable source of truth" in text
    assert ".elis/state/current_pe.json" in text
    assert "schemas/current_pe.schema.json" in text
    assert (
        "`CURRENT_PE.md` is a rendered human-readable summary and must remain consistent with the JSON state"
        in text
    )
    assert (
        "Markdown string matching must not be the canonical validation mechanism"
        in text
    )


def test_script_mentions_current_pe_state_and_json() -> None:
    text = Path("scripts/pm_dispatch.py").read_text(encoding="utf-8")

    assert "CURRENT_PE_STATE_PATH" in text
    assert "_load_current_pe_state" in text
    assert "Current PE packet" in text or "current PE packet" in text
    assert "Phase 1 only generates and checks dispatch contracts" in text


def test_current_state_schema_exists_and_requires_core_keys() -> None:
    text = Path("schemas/current_pe.schema.json").read_text(encoding="utf-8")

    assert '"pe_id"' in text
    assert '"current_state"' in text
    assert '"file_scope"' in text
    assert '"runtime_bootstrap_allowlist"' in text
    assert '"live_dispatch_statement"' in text
