"""Tests for scripts/check_current_pe.py."""

from __future__ import annotations

import importlib.util
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "check_current_pe.py"


def _load():
    spec = importlib.util.spec_from_file_location("check_current_pe", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


MODULE = _load()


VALID_CURRENT_PE = """\
# Current PE Assignment

## Release context

| Field          | Value                               |
|----------------|-------------------------------------|
| Release        | ELIS 2-Agent Automation Plan        |
| Base branch    | main                                |
| Plan file      | ELIS_2Agent_Automation_Plan_v2_0.md |
| Plan location  | repo root                           |

## Current PE

| Field   | Value                                         |
|---------|-----------------------------------------------|
| PE      | PE-AUTO-02                                    |
| Branch  | feature/pe-auto-02-current-pe-ci-validation   |

## Agent roles

| Agent       | Role        |
|-------------|-------------|
| CODEX       | Implementer |
| Claude Code | Validator   |

## Active PE Registry

| PE-ID       | Domain | Implementer-agentId | Validator-agentId | Branch                                       | Status        | Last-updated |
|-------------|--------|---------------------|-------------------|----------------------------------------------|---------------|--------------|
| PE-AUTO-01  | infra  | infra-impl-claude   | infra-val-codex   | feature/pe-auto-01-bot-accounts-pats         | merged        | 2026-03-28   |
| PE-AUTO-02  | infra  | infra-impl-codex    | infra-val-claude  | feature/pe-auto-02-current-pe-ci-validation  | implementing  | 2026-03-28   |
"""

VALID_CURRENT_PE_GEMINI = """\
# Current PE Assignment

## Release context

| Field          | Value                                     |
|----------------|-------------------------------------------|
| Release        | ELIS Hybrid SLR Execution Plan · v1.8.1   |
| Base branch    | main                                      |
| Plan file      | ELIS_MultiAgent_Implementation_Plan_v1_8_1.md |
| Plan location  | repo root                                 |

## Current PE

| Field   | Value                                      |
|---------|--------------------------------------------|
| PE      | PE-SLR-01                                  |
| Branch  | feature/pe-slr-01-harvest-workflow-contract |

## Agent roles

| Agent       | Role        |
|-------------|-------------|
| CODEX       | Implementer |
| Gemini CLI  | Validator   |

## Active PE Registry

| PE-ID       | Domain | Implementer-agentId | Validator-agentId | Branch                                        | Status          | Last-updated |
|-------------|--------|---------------------|-------------------|-----------------------------------------------|-----------------|--------------|
| PE-OC-10    | slr    | slr-impl-claude     | slr-val-codex     | feature/pe-oc-10-e2e-slr                      | merged          | 2026-02-22   |
| PE-SLR-01   | slr    | prog-impl-codex     | gemini-cli        | feature/pe-slr-01-harvest-workflow-contract   | gate-2-pending  | 2026-04-13   |
"""

VALID_CURRENT_PE_SLOT_LABELS = """\
# Current PE Assignment

## Release context

| Field          | Value                                       |
|----------------|---------------------------------------------|
| Release        | ELIS Multi-Agent Implementation Plan · v2.0.1 |
| Base branch    | main                                        |
| Plan file      | ELIS_MultiAgent_Implementation_Plan_v2_0.md |
| Plan location  | repo root                                   |

## Current PE

| Field   | Value                                       |
|---------|---------------------------------------------|
| PE      | PE-INFRA-AGENT-01                           |
| Branch  | feature/pe-infra-agent-01-doc-consolidation |

## Agent roles

| Agent  | Role        |
|--------|-------------|
| slot-b | Implementer |
| slot-a | Validator   |

## Active PE Registry

| PE-ID             | Domain | Implementer-agentId | Validator-agentId | Branch                                        | Status         | Last-updated |
|-------------------|--------|---------------------|-------------------|-----------------------------------------------|----------------|--------------|
| PE-AGT-00         | agt    | infra-impl-a        | infra-val-b       | feature/pe-agt-00-model-authentication-setup  | merged         | 2026-04-26   |
| PE-INFRA-AGENT-01 | agt    | infra-impl-b        | infra-val-a       | feature/pe-infra-agent-01-doc-consolidation   | implementing   | 2026-04-28   |
"""


def _write_current_pe(tmp_path: Path, content: str) -> Path:
    path = tmp_path / "CURRENT_PE.md"
    path.write_text(content, encoding="utf-8")
    return path


def test_main_accepts_valid_current_pe(tmp_path, monkeypatch, capsys):
    path = _write_current_pe(tmp_path, VALID_CURRENT_PE)
    monkeypatch.setenv("CURRENT_PE_PATH", str(path))
    assert MODULE.main() == 0
    assert "CURRENT_PE.md OK" in capsys.readouterr().out


def test_main_accepts_gemini_validator_and_gate_2_pending(
    tmp_path, monkeypatch, capsys
):
    path = _write_current_pe(tmp_path, VALID_CURRENT_PE_GEMINI)
    monkeypatch.setenv("CURRENT_PE_PATH", str(path))
    assert MODULE.main() == 0
    assert "CURRENT_PE.md OK" in capsys.readouterr().out


def test_blank_release_field_fails(tmp_path, monkeypatch):
    content = VALID_CURRENT_PE.replace(
        "| Plan file      | ELIS_2Agent_Automation_Plan_v2_0.md |",
        "| Plan file      |                                     |",
    )
    path = _write_current_pe(tmp_path, content)
    monkeypatch.setenv("CURRENT_PE_PATH", str(path))
    assert MODULE.main() == 1


def test_invalid_pe_format_fails(tmp_path, monkeypatch):
    content = VALID_CURRENT_PE.replace("PE-AUTO-02", "PE-auto-02", 1)
    path = _write_current_pe(tmp_path, content)
    monkeypatch.setenv("CURRENT_PE_PATH", str(path))
    assert MODULE.main() == 1


def test_invalid_branch_format_fails(tmp_path, monkeypatch):
    content = VALID_CURRENT_PE.replace(
        "feature/pe-auto-02-current-pe-ci-validation",
        "bugfix/current-pe",
        1,
    )
    path = _write_current_pe(tmp_path, content)
    monkeypatch.setenv("CURRENT_PE_PATH", str(path))
    assert MODULE.main() == 1


def test_active_pe_status_must_be_a_supported_live_status(tmp_path, monkeypatch):
    content = VALID_CURRENT_PE.replace(
        "| PE-AUTO-02  | infra  | infra-impl-codex    | infra-val-claude  | feature/pe-auto-02-current-pe-ci-validation  | implementing  | 2026-03-28   |",
        "| PE-AUTO-02  | infra  | infra-impl-codex    | infra-val-claude  | feature/pe-auto-02-current-pe-ci-validation  | merged         | 2026-03-28   |",
    )
    path = _write_current_pe(tmp_path, content)
    monkeypatch.setenv("CURRENT_PE_PATH", str(path))
    assert MODULE.main() == 1


def test_alternation_rule_violation_fails(tmp_path, monkeypatch):
    content = VALID_CURRENT_PE.replace(
        "| PE-AUTO-02  | infra  | infra-impl-codex    | infra-val-claude  | feature/pe-auto-02-current-pe-ci-validation  | implementing  | 2026-03-28   |",
        "| PE-AUTO-02  | infra  | infra-impl-claude   | infra-val-codex   | feature/pe-auto-02-current-pe-ci-validation  | implementing  | 2026-03-28   |",
    )
    path = _write_current_pe(tmp_path, content)
    monkeypatch.setenv("CURRENT_PE_PATH", str(path))
    assert MODULE.main() == 1


def test_same_engine_roles_fail(tmp_path, monkeypatch):
    content = VALID_CURRENT_PE.replace(
        "| PE-AUTO-02  | infra  | infra-impl-codex    | infra-val-claude  | feature/pe-auto-02-current-pe-ci-validation  | implementing  | 2026-03-28   |",
        "| PE-AUTO-02  | infra  | infra-impl-codex    | infra-val-codex   | feature/pe-auto-02-current-pe-ci-validation  | implementing  | 2026-03-28   |",
    )
    path = _write_current_pe(tmp_path, content)
    monkeypatch.setenv("CURRENT_PE_PATH", str(path))
    assert MODULE.main() == 1


def test_missing_registry_row_for_current_pe_fails(tmp_path, monkeypatch):
    content = VALID_CURRENT_PE.replace(
        "| PE-AUTO-02  | infra  | infra-impl-codex    | infra-val-claude  | feature/pe-auto-02-current-pe-ci-validation  | implementing  | 2026-03-28   |\n",
        "",
    )
    path = _write_current_pe(tmp_path, content)
    monkeypatch.setenv("CURRENT_PE_PATH", str(path))
    assert MODULE.main() == 1


def test_branch_mismatch_between_current_and_registry_fails(tmp_path, monkeypatch):
    content = VALID_CURRENT_PE.replace(
        "feature/pe-auto-02-current-pe-ci-validation  | implementing",
        "feature/pe-auto-02-wrong-branch             | implementing",
    )
    path = _write_current_pe(tmp_path, content)
    monkeypatch.setenv("CURRENT_PE_PATH", str(path))
    assert MODULE.main() == 1


def test_agent_roles_table_must_match_registry_engines(tmp_path, monkeypatch):
    content = VALID_CURRENT_PE.replace(
        "| CODEX       | Implementer |",
        "| CODEX       | Validator   |",
    )
    content = content.replace(
        "| Claude Code | Validator   |",
        "| Claude Code | Implementer |",
    )
    path = _write_current_pe(tmp_path, content)
    monkeypatch.setenv("CURRENT_PE_PATH", str(path))
    assert MODULE.main() == 1


def test_main_accepts_slot_based_roles_table(tmp_path, monkeypatch, capsys):
    path = _write_current_pe(tmp_path, VALID_CURRENT_PE_SLOT_LABELS)
    monkeypatch.setenv("CURRENT_PE_PATH", str(path))
    assert MODULE.main() == 0
    assert "CURRENT_PE.md OK" in capsys.readouterr().out


def test_slot_based_roles_table_must_match_registry_engines(tmp_path, monkeypatch):
    content = VALID_CURRENT_PE_SLOT_LABELS.replace(
        "| slot-b | Implementer |",
        "| slot-b | Validator   |",
    )
    content = content.replace(
        "| slot-a | Validator   |",
        "| slot-a | Implementer |",
    )
    path = _write_current_pe(tmp_path, content)
    monkeypatch.setenv("CURRENT_PE_PATH", str(path))
    assert MODULE.main() == 1


def test_plan_complete_mode_is_valid(tmp_path, monkeypatch, capsys):
    content = (
        VALID_CURRENT_PE.replace(
            "| PE      | PE-AUTO-02                                    |",
            "| PE      | —                                             |",
        )
        .replace(
            "| Branch  | feature/pe-auto-02-current-pe-ci-validation   |",
            "| Branch  | —                                             |",
        )
        .replace(
            "| CODEX       | Implementer |",
            "| CODEX       | —           |",
        )
        .replace(
            "| Claude Code | Validator   |",
            "| Claude Code | —           |",
        )
        .replace(
            "## Agent roles\n",
            "## Agent roles\n\n> **Plan complete.** All PEs are merged.\n\n",
        )
    )
    path = _write_current_pe(tmp_path, content)
    monkeypatch.setenv("CURRENT_PE_PATH", str(path))
    assert MODULE.main() == 0
    assert "plan-complete mode" in capsys.readouterr().out


# ---------------------------------------------------------------------------
# Alternation waiver mechanism tests
# ---------------------------------------------------------------------------

ALTERNATION_VIOLATION_PE = """\
# Current PE Assignment

## Release context

| Field          | Value                               |
|----------------|-------------------------------------|
| Release        | ELIS 2-Agent Automation Plan        |
| Base branch    | main                                |
| Plan file      | ELIS_2Agent_Automation_Plan_v2_0.md |
| Plan location  | repo root                           |

## Current PE

| Field   | Value                                             |
|---------|---------------------------------------------------|
| PE      | PE-OPS-OPENCLAW-CLI-PATH-01                       |
| Branch  | feature/pe-ops-openclaw-cli-path-01-fix-path      |

## Agent roles

| Agent        | Role        |
|--------------|-------------|
| infra-impl-b | Implementer |
| infra-val-a  | Validator   |

## Active PE Registry

| PE-ID                        | Domain | Implementer-agentId | Validator-agentId | Branch                                           | Status        | Last-updated |
|------------------------------|--------|---------------------|-------------------|--------------------------------------------------|---------------|--------------|
| PE-OPS-WORKTREE-BINDING-02   | ops    | infra-impl-b        | infra-val-a       | feature/pe-ops-worktree-binding-02               | merged        | 2026-05-09   |
| PE-OPS-OPENCLAW-CLI-PATH-01  | ops    | infra-impl-b        | infra-val-a       | feature/pe-ops-openclaw-cli-path-01-fix-path     | gate-2-pending | 2026-06-01  |
"""

VALID_WAIVER_CONTENT = """\
# ALTERNATION WAIVER — PE-OPS-OPENCLAW-CLI-PATH-01

> Classification: OPS_AGENT_ALTERNATION_RULE_VIOLATION_AT_PE_OPENING
> Waiver status: GRANTED (PO, 2026-06-01)

## Violation

| Field | Value |
|---|---|
| PE | PE-OPS-OPENCLAW-CLI-PATH-01 |
| Actual implementer | `infra-impl-b` (engine: claude) |
| Expected implementer (by alternation) | `infra-impl-a` (engine: codex) |
| Validator | `infra-val-a` |

## Hard Constraints

- This waiver does **not** change the alternation rule globally.
- Future ops PEs must alternate correctly from `infra-impl-b`.
- The implementer record in `CURRENT_PE.md` is **not** falsified.

## PO Approval

Approved by: Carlos Rocha (PO), 2026-06-01

Scope: one-time, this PE only.
"""


def _write_waiver(tmp_path: Path, pe_id: str, content: str) -> Path:
    waiver_dir = tmp_path / ".elis" / "pe" / pe_id
    waiver_dir.mkdir(parents=True, exist_ok=True)
    waiver_path = waiver_dir / "ALTERNATION_WAIVER.md"
    waiver_path.write_text(content, encoding="utf-8")
    return waiver_path


def test_alternation_pass_no_waiver_needed(tmp_path, monkeypatch, capsys):
    """Normal alternation PASS — no waiver consulted."""
    path = _write_current_pe(tmp_path, VALID_CURRENT_PE)
    monkeypatch.setenv("CURRENT_PE_PATH", str(path))
    assert MODULE.main() == 0
    out = capsys.readouterr().out
    assert "CURRENT_PE.md OK" in out
    assert "waiver" not in out.lower()


def test_alternation_fail_without_waiver(tmp_path, monkeypatch):
    """Alternation violation with no waiver file → fail."""
    path = _write_current_pe(tmp_path, ALTERNATION_VIOLATION_PE)
    monkeypatch.setenv("CURRENT_PE_PATH", str(path))
    assert MODULE.main() == 1


def test_alternation_pass_with_valid_waiver(tmp_path, monkeypatch, capsys):
    """Alternation violation + valid PE-local waiver → pass with warning."""
    path = _write_current_pe(tmp_path, ALTERNATION_VIOLATION_PE)
    _write_waiver(tmp_path, "PE-OPS-OPENCLAW-CLI-PATH-01", VALID_WAIVER_CONTENT)
    monkeypatch.setenv("CURRENT_PE_PATH", str(path))
    assert MODULE.main() == 0
    out = capsys.readouterr().out
    assert "WARNING" in out
    assert "waiver" in out.lower()
    assert "CURRENT_PE.md OK" in out


def test_waiver_fail_pe_id_mismatch(tmp_path, monkeypatch):
    """Waiver heading PE ID does not match active PE → fail."""
    path = _write_current_pe(tmp_path, ALTERNATION_VIOLATION_PE)
    bad_waiver = VALID_WAIVER_CONTENT.replace(
        "# ALTERNATION WAIVER — PE-OPS-OPENCLAW-CLI-PATH-01",
        "# ALTERNATION WAIVER — PE-OPS-OTHER-01",
    )
    _write_waiver(tmp_path, "PE-OPS-OPENCLAW-CLI-PATH-01", bad_waiver)
    monkeypatch.setenv("CURRENT_PE_PATH", str(path))
    assert MODULE.main() == 1


def test_waiver_fail_actual_implementer_mismatch(tmp_path, monkeypatch):
    """Waiver actual implementer does not match registry → fail."""
    path = _write_current_pe(tmp_path, ALTERNATION_VIOLATION_PE)
    bad_waiver = VALID_WAIVER_CONTENT.replace(
        "| Actual implementer | `infra-impl-b` (engine: claude) |",
        "| Actual implementer | `infra-impl-a` (engine: codex) |",
    )
    _write_waiver(tmp_path, "PE-OPS-OPENCLAW-CLI-PATH-01", bad_waiver)
    monkeypatch.setenv("CURRENT_PE_PATH", str(path))
    assert MODULE.main() == 1


def test_waiver_fail_expected_implementer_same_as_actual(tmp_path, monkeypatch):
    """Waiver expected implementer same as actual → fail."""
    path = _write_current_pe(tmp_path, ALTERNATION_VIOLATION_PE)
    bad_waiver = VALID_WAIVER_CONTENT.replace(
        "| Expected implementer (by alternation) | `infra-impl-a` (engine: codex) |",
        "| Expected implementer (by alternation) | `infra-impl-b` (engine: claude) |",
    )
    _write_waiver(tmp_path, "PE-OPS-OPENCLAW-CLI-PATH-01", bad_waiver)
    monkeypatch.setenv("CURRENT_PE_PATH", str(path))
    assert MODULE.main() == 1


def test_waiver_fail_status_not_granted(tmp_path, monkeypatch):
    """Waiver status is not GRANTED → fail."""
    path = _write_current_pe(tmp_path, ALTERNATION_VIOLATION_PE)
    bad_waiver = VALID_WAIVER_CONTENT.replace(
        "> Waiver status: GRANTED (PO, 2026-06-01)",
        "> Waiver status: PENDING (PO, 2026-06-01)",
    )
    _write_waiver(tmp_path, "PE-OPS-OPENCLAW-CLI-PATH-01", bad_waiver)
    monkeypatch.setenv("CURRENT_PE_PATH", str(path))
    assert MODULE.main() == 1


def test_waiver_fail_outside_pe_directory(tmp_path, monkeypatch):
    """Waiver placed outside .elis/pe/<PE_ID>/ is not found → fail as no-waiver."""
    path = _write_current_pe(tmp_path, ALTERNATION_VIOLATION_PE)
    # Write waiver in a different PE's directory — the loader won't find it
    wrong_dir = tmp_path / ".elis" / "pe" / "PE-OPS-OTHER-01"
    wrong_dir.mkdir(parents=True, exist_ok=True)
    (wrong_dir / "ALTERNATION_WAIVER.md").write_text(VALID_WAIVER_CONTENT, encoding="utf-8")
    monkeypatch.setenv("CURRENT_PE_PATH", str(path))
    assert MODULE.main() == 1
