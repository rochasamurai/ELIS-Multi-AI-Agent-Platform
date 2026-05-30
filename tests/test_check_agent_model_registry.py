"""
Tests for scripts/check_agent_model_registry.py — PE-OPS-A2A-PRODUCTION-02
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
from check_agent_model_registry import (
    ELIS_PLATFORM_AGENTS,
    load_agent_models,
    run_check,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_config(tmp_path: Path, agent_entries: list[dict]) -> Path:
    cfg = {"agents": {"list": agent_entries}}
    p = tmp_path / "openclaw.json"
    p.write_text(json.dumps(cfg), encoding="utf-8")
    return p


def _full_agent_entry(agent_id: str, model: str) -> dict:
    return {"id": agent_id, "model": model, "workspace": f"/opt/elis/agent-worktrees/{agent_id}"}


def _all_agents_config(tmp_path: Path, extra: list[dict] | None = None) -> Path:
    entries = [_full_agent_entry(a, f"openrouter/test/{a}-model") for a in ELIS_PLATFORM_AGENTS]
    if extra:
        entries.extend(extra)
    return _write_config(tmp_path, entries)


# ---------------------------------------------------------------------------
# load_agent_models
# ---------------------------------------------------------------------------

class TestLoadAgentModels:
    def test_returns_dict_of_id_to_model(self, tmp_path):
        cfg = _write_config(tmp_path, [
            {"id": "infra-impl-a", "model": "openrouter/qwen/qwen3-coder-flash"},
            {"id": "infra-val-b", "model": "openrouter/z-ai/glm-5.1"},
        ])
        result = load_agent_models(cfg)
        assert result["infra-impl-a"] == "openrouter/qwen/qwen3-coder-flash"
        assert result["infra-val-b"] == "openrouter/z-ai/glm-5.1"

    def test_missing_model_returns_none(self, tmp_path):
        cfg = _write_config(tmp_path, [{"id": "infra-impl-a"}])
        result = load_agent_models(cfg)
        assert result["infra-impl-a"] is None

    def test_entries_without_id_are_skipped(self, tmp_path):
        cfg = _write_config(tmp_path, [{"model": "openrouter/x/y"}])
        result = load_agent_models(cfg)
        assert "" not in result or result.get("") is None


# ---------------------------------------------------------------------------
# run_check — PASS cases
# ---------------------------------------------------------------------------

class TestRunCheckPass:
    def test_all_agents_present_exits_0(self, tmp_path):
        cfg = _all_agents_config(tmp_path)
        assert run_check(cfg, c8=False) == 0

    def test_extra_agents_in_config_ignored(self, tmp_path):
        cfg = _all_agents_config(tmp_path, extra=[
            {"id": "harvest-impl-a", "model": "openrouter/slr/model"},
            {"id": "pm", "model": "claude-cli/claude-sonnet-4-6"},
        ])
        assert run_check(cfg, c8=False) == 0

    def test_c8_advisory_does_not_fail_on_known_prefix(self, tmp_path):
        cfg = _all_agents_config(tmp_path)
        assert run_check(cfg, c8=True) == 0


# ---------------------------------------------------------------------------
# run_check — FAIL cases
# ---------------------------------------------------------------------------

class TestRunCheckFail:
    def test_missing_one_agent_exits_1(self, tmp_path):
        entries = [
            _full_agent_entry(a, f"openrouter/test/{a}-model")
            for a in ELIS_PLATFORM_AGENTS
            if a != "infra-val-b"
        ]
        cfg = _write_config(tmp_path, entries)
        assert run_check(cfg, c8=False) == 1

    def test_agent_with_null_model_exits_1(self, tmp_path):
        entries = [_full_agent_entry(a, f"openrouter/test/{a}-model") for a in ELIS_PLATFORM_AGENTS]
        # Override one to have no model
        entries = [e if e["id"] != "infra-impl-b" else {"id": "infra-impl-b"} for e in entries]
        cfg = _write_config(tmp_path, entries)
        assert run_check(cfg, c8=False) == 1

    def test_missing_all_agents_exits_1(self, tmp_path):
        cfg = _write_config(tmp_path, [{"id": "pm", "model": "claude-cli/claude-sonnet-4-6"}])
        assert run_check(cfg, c8=False) == 1

    def test_bad_config_file_exits_1(self, tmp_path):
        bad = tmp_path / "bad.json"
        bad.write_text("{not valid json", encoding="utf-8")
        assert run_check(bad, c8=False) == 1

    def test_missing_config_file_exits_1(self, tmp_path):
        missing = tmp_path / "nonexistent.json"
        assert run_check(missing, c8=False) == 1


# ---------------------------------------------------------------------------
# --sync mode
# ---------------------------------------------------------------------------

class TestSyncMode:
    def test_main_sync_exits_2(self, monkeypatch, capsys):
        import check_agent_model_registry as mod
        monkeypatch.setattr(sys, "argv", ["check_agent_model_registry.py", "--sync"])
        with pytest.raises(SystemExit) as exc_info:
            mod.main()
        assert exc_info.value.code == 2
        out = capsys.readouterr().out
        assert "NOT IMPLEMENTED" in out
        assert "Supervisor" in out

    def test_sync_with_check_flag_still_exits_2(self, monkeypatch, capsys):
        import check_agent_model_registry as mod
        monkeypatch.setattr(sys, "argv", ["check_agent_model_registry.py", "--sync", "--check"])
        with pytest.raises(SystemExit) as exc_info:
            mod.main()
        assert exc_info.value.code == 2


# ---------------------------------------------------------------------------
# C8 advisory — non-fatal
# ---------------------------------------------------------------------------

class TestC8Advisory:
    def test_c8_unknown_prefix_is_warning_not_fail(self, tmp_path):
        entries = [
            _full_agent_entry(a, "unknown-provider/some-model") for a in ELIS_PLATFORM_AGENTS
        ]
        cfg = _write_config(tmp_path, entries)
        # C8 warning does not change exit code
        assert run_check(cfg, c8=True) == 0

    def test_c8_disabled_by_default(self, tmp_path):
        cfg = _all_agents_config(tmp_path)
        assert run_check(cfg, c8=False) == 0


# ---------------------------------------------------------------------------
# ELIS Platform agent scope
# ---------------------------------------------------------------------------

class TestAgentScope:
    def test_slr_agents_not_in_scope(self):
        slr = ["harvest-impl-a", "harvest-val-b", "screen-impl-b", "screen-val-a",
               "extract-impl-a", "extract-val-b", "synth-impl-b", "synth-val-a",
               "prisma-impl-b", "prisma-val-a"]
        for agent in slr:
            assert agent not in ELIS_PLATFORM_AGENTS, f"{agent} must not be in ELIS_PLATFORM_AGENTS"

    def test_github_agent_not_in_scope(self):
        assert "github-agent" not in ELIS_PLATFORM_AGENTS

    def test_pm_not_in_scope(self):
        assert "pm" not in ELIS_PLATFORM_AGENTS

    def test_infra_agents_in_scope(self):
        for agent in ["infra-impl-a", "infra-impl-b", "infra-val-a", "infra-val-b"]:
            assert agent in ELIS_PLATFORM_AGENTS

    def test_prog_agents_in_scope(self):
        for agent in ["prog-impl-a", "prog-impl-b", "prog-val-a", "prog-val-b"]:
            assert agent in ELIS_PLATFORM_AGENTS
