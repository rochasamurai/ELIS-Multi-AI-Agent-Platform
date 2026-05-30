"""
Tests for scripts/check_agent_model_registry.py — PE-OPS-A2A-PRODUCTION-02

All tests use tmp_path fixtures. No live config is accessed.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
from check_agent_model_registry import (
    ELIS_PLATFORM_AGENTS,
    check_model_in_agent_catalog,
    load_agent_models,
    run_check,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _write_openclaw_config(tmp_path: Path, agent_entries: list[dict]) -> Path:
    cfg = {"agents": {"list": agent_entries}}
    p = tmp_path / "openclaw.json"
    p.write_text(json.dumps(cfg), encoding="utf-8")
    return p


def _agent_entry(agent_id: str, model: str | None = None) -> dict:
    entry: dict = {"id": agent_id, "workspace": f"/opt/elis/agent-worktrees/{agent_id}"}
    if model is not None:
        entry["model"] = model
    return entry


def _write_agent_models_json(agents_root: Path, agent_id: str, model_ids: list[str]) -> Path:
    """Write a per-agent models.json with the given model ids under a fake provider."""
    agent_dir = agents_root / agent_id / "agent"
    agent_dir.mkdir(parents=True, exist_ok=True)
    mjs = agent_dir / "models.json"
    data = {
        "providers": {
            "openrouter": {
                "baseUrl": "https://openrouter.ai/v1",
                "models": [{"id": mid, "name": mid} for mid in model_ids],
            }
        }
    }
    mjs.write_text(json.dumps(data), encoding="utf-8")
    return mjs


def _all_agents_openclaw(tmp_path: Path) -> Path:
    entries = [
        _agent_entry(a, f"openrouter/test/{a}-model") for a in ELIS_PLATFORM_AGENTS
    ]
    return _write_openclaw_config(tmp_path, entries)


def _all_agents_models_json(agents_root: Path) -> None:
    for a in ELIS_PLATFORM_AGENTS:
        _write_agent_models_json(agents_root, a, [f"openrouter/test/{a}-model"])


# ---------------------------------------------------------------------------
# load_agent_models
# ---------------------------------------------------------------------------


class TestLoadAgentModels:
    def test_returns_dict_of_id_to_model(self, tmp_path):
        cfg = _write_openclaw_config(tmp_path, [
            _agent_entry("infra-impl-a", "openrouter/qwen/qwen3-coder-flash"),
            _agent_entry("infra-val-b", "openrouter/z-ai/glm-5.1"),
        ])
        result = load_agent_models(cfg)
        assert result["infra-impl-a"] == "openrouter/qwen/qwen3-coder-flash"
        assert result["infra-val-b"] == "openrouter/z-ai/glm-5.1"

    def test_missing_model_returns_none(self, tmp_path):
        cfg = _write_openclaw_config(tmp_path, [{"id": "infra-impl-a"}])
        result = load_agent_models(cfg)
        assert result["infra-impl-a"] is None

    def test_entries_without_id_are_skipped(self, tmp_path):
        cfg = _write_openclaw_config(tmp_path, [{"model": "openrouter/x/y"}])
        result = load_agent_models(cfg)
        assert "" not in result


# ---------------------------------------------------------------------------
# check_model_in_agent_catalog
# ---------------------------------------------------------------------------


class TestCheckModelInAgentCatalog:
    def test_pass_when_model_present(self, tmp_path):
        _write_agent_models_json(tmp_path, "infra-val-b", ["openrouter/z-ai/glm-5.1"])
        found, detail = check_model_in_agent_catalog(
            "infra-val-b", "openrouter/z-ai/glm-5.1", tmp_path
        )
        assert found is True
        assert "found" in detail

    def test_fail_when_model_absent(self, tmp_path):
        _write_agent_models_json(tmp_path, "infra-val-b", ["openrouter/other/model"])
        found, detail = check_model_in_agent_catalog(
            "infra-val-b", "openrouter/z-ai/glm-5.1", tmp_path
        )
        assert found is False
        assert "not found" in detail

    def test_fail_when_models_json_missing(self, tmp_path):
        found, detail = check_model_in_agent_catalog(
            "infra-val-b", "openrouter/z-ai/glm-5.1", tmp_path
        )
        assert found is False
        assert "missing" in detail

    def test_fail_when_models_json_invalid_json(self, tmp_path):
        agent_dir = tmp_path / "infra-val-b" / "agent"
        agent_dir.mkdir(parents=True)
        (agent_dir / "models.json").write_text("{not valid json", encoding="utf-8")
        found, detail = check_model_in_agent_catalog(
            "infra-val-b", "openrouter/z-ai/glm-5.1", tmp_path
        )
        assert found is False
        assert "invalid JSON" in detail

    def test_fail_when_agent_directory_missing(self, tmp_path):
        # agents_root exists but agent subdirectory does not
        found, detail = check_model_in_agent_catalog(
            "nonexistent-agent", "openrouter/z-ai/glm-5.1", tmp_path
        )
        assert found is False
        assert "missing" in detail

    def test_multiple_providers_checked(self, tmp_path):
        agent_dir = tmp_path / "infra-impl-a" / "agent"
        agent_dir.mkdir(parents=True)
        data = {
            "providers": {
                "openrouter": {"models": [{"id": "openrouter/other/model"}]},
                "anthropic": {"models": [{"id": "openrouter/qwen/qwen3-coder-flash"}]},
            }
        }
        (agent_dir / "models.json").write_text(json.dumps(data), encoding="utf-8")
        found, _ = check_model_in_agent_catalog(
            "infra-impl-a", "openrouter/qwen/qwen3-coder-flash", tmp_path
        )
        assert found is True


# ---------------------------------------------------------------------------
# run_check — two-layer PASS
# ---------------------------------------------------------------------------


class TestRunCheckPass:
    def test_all_agents_both_layers_pass(self, tmp_path):
        cfg_dir = tmp_path / "cfg"
        agents_dir = tmp_path / "agents"
        cfg_dir.mkdir()
        cfg = _write_openclaw_config(
            cfg_dir,
            [_agent_entry(a, f"openrouter/test/{a}-model") for a in ELIS_PLATFORM_AGENTS],
        )
        _all_agents_models_json(agents_dir)
        assert run_check(cfg, agents_dir, c8=False) == 0

    def test_extra_agents_in_openclaw_ignored(self, tmp_path):
        cfg_dir = tmp_path / "cfg"
        agents_dir = tmp_path / "agents"
        cfg_dir.mkdir()
        entries = [_agent_entry(a, f"openrouter/test/{a}-model") for a in ELIS_PLATFORM_AGENTS]
        entries.append(_agent_entry("github-agent", "openai-codex/gpt-5.4-mini"))
        entries.append(_agent_entry("pm", "claude-cli/claude-sonnet-4-6"))
        cfg = _write_openclaw_config(cfg_dir, entries)
        _all_agents_models_json(agents_dir)
        assert run_check(cfg, agents_dir, c8=False) == 0


# ---------------------------------------------------------------------------
# run_check — Layer 1 failures (openclaw.json)
# ---------------------------------------------------------------------------


class TestRunCheckLayer1Fail:
    def test_agent_missing_from_openclaw_exits_1(self, tmp_path):
        cfg_dir = tmp_path / "cfg"
        agents_dir = tmp_path / "agents"
        cfg_dir.mkdir()
        entries = [
            _agent_entry(a, f"openrouter/test/{a}-model")
            for a in ELIS_PLATFORM_AGENTS
            if a != "infra-val-b"
        ]
        cfg = _write_openclaw_config(cfg_dir, entries)
        _all_agents_models_json(agents_dir)
        assert run_check(cfg, agents_dir, c8=False) == 1

    def test_agent_model_empty_exits_1(self, tmp_path):
        cfg_dir = tmp_path / "cfg"
        agents_dir = tmp_path / "agents"
        cfg_dir.mkdir()
        entries = [_agent_entry(a, f"openrouter/test/{a}-model") for a in ELIS_PLATFORM_AGENTS]
        entries = [
            e if e["id"] != "infra-impl-b" else {"id": "infra-impl-b"}
            for e in entries
        ]
        cfg = _write_openclaw_config(cfg_dir, entries)
        _all_agents_models_json(agents_dir)
        assert run_check(cfg, agents_dir, c8=False) == 1

    def test_bad_openclaw_config_exits_1(self, tmp_path):
        bad = tmp_path / "bad.json"
        bad.write_text("{not valid json", encoding="utf-8")
        assert run_check(bad, tmp_path / "agents", c8=False) == 1

    def test_missing_openclaw_config_exits_1(self, tmp_path):
        assert run_check(tmp_path / "nonexistent.json", tmp_path / "agents", c8=False) == 1


# ---------------------------------------------------------------------------
# run_check — Layer 2 failures (per-agent models.json)
# ---------------------------------------------------------------------------


class TestRunCheckLayer2Fail:
    def test_models_json_missing_exits_1(self, tmp_path):
        cfg_dir = tmp_path / "cfg"
        agents_dir = tmp_path / "agents"
        cfg_dir.mkdir()
        cfg = _write_openclaw_config(
            cfg_dir,
            [_agent_entry(a, f"openrouter/test/{a}-model") for a in ELIS_PLATFORM_AGENTS],
        )
        # Write models.json for all except infra-val-b
        for a in ELIS_PLATFORM_AGENTS:
            if a != "infra-val-b":
                _write_agent_models_json(agents_dir, a, [f"openrouter/test/{a}-model"])
        assert run_check(cfg, agents_dir, c8=False) == 1

    def test_models_json_invalid_json_exits_1(self, tmp_path):
        cfg_dir = tmp_path / "cfg"
        agents_dir = tmp_path / "agents"
        cfg_dir.mkdir()
        cfg = _write_openclaw_config(
            cfg_dir,
            [_agent_entry(a, f"openrouter/test/{a}-model") for a in ELIS_PLATFORM_AGENTS],
        )
        _all_agents_models_json(agents_dir)
        # Corrupt one
        corrupt = agents_dir / "infra-impl-a" / "agent" / "models.json"
        corrupt.write_text("{invalid", encoding="utf-8")
        assert run_check(cfg, agents_dir, c8=False) == 1

    def test_model_absent_from_models_json_exits_1(self, tmp_path):
        cfg_dir = tmp_path / "cfg"
        agents_dir = tmp_path / "agents"
        cfg_dir.mkdir()
        cfg = _write_openclaw_config(
            cfg_dir,
            [_agent_entry(a, f"openrouter/test/{a}-model") for a in ELIS_PLATFORM_AGENTS],
        )
        _all_agents_models_json(agents_dir)
        # Override infra-val-a with wrong model in models.json
        _write_agent_models_json(agents_dir, "infra-val-a", ["openrouter/other/wrong-model"])
        assert run_check(cfg, agents_dir, c8=False) == 1

    def test_agent_directory_missing_exits_1(self, tmp_path):
        cfg_dir = tmp_path / "cfg"
        agents_dir = tmp_path / "agents"
        cfg_dir.mkdir()
        cfg = _write_openclaw_config(
            cfg_dir,
            [_agent_entry(a, f"openrouter/test/{a}-model") for a in ELIS_PLATFORM_AGENTS],
        )
        # Write models.json for all but leave prog-impl-b directory absent
        for a in ELIS_PLATFORM_AGENTS:
            if a != "prog-impl-b":
                _write_agent_models_json(agents_dir, a, [f"openrouter/test/{a}-model"])
        assert run_check(cfg, agents_dir, c8=False) == 1


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

    def test_sync_does_not_mutate(self, tmp_path, monkeypatch, capsys):
        import check_agent_model_registry as mod
        # Even with a valid config path, --sync must not read or write it
        cfg = tmp_path / "openclaw.json"
        cfg.write_text('{"agents": {"list": []}}', encoding="utf-8")
        mtime_before = cfg.stat().st_mtime
        monkeypatch.setattr(sys, "argv", [
            "check_agent_model_registry.py", "--sync", "--config", str(cfg)
        ])
        with pytest.raises(SystemExit):
            mod.main()
        assert cfg.stat().st_mtime == mtime_before


# ---------------------------------------------------------------------------
# C8 advisory — non-fatal
# ---------------------------------------------------------------------------


class TestC8Advisory:
    def test_c8_unknown_prefix_is_warning_not_fail(self, tmp_path):
        cfg_dir = tmp_path / "cfg"
        agents_dir = tmp_path / "agents"
        cfg_dir.mkdir()
        entries = [_agent_entry(a, "unknown-provider/some-model") for a in ELIS_PLATFORM_AGENTS]
        cfg = _write_openclaw_config(cfg_dir, entries)
        for a in ELIS_PLATFORM_AGENTS:
            _write_agent_models_json(agents_dir, a, ["unknown-provider/some-model"])
        # C8 warning does not change exit code — still 0 (both layers pass)
        assert run_check(cfg, agents_dir, c8=True) == 0


# ---------------------------------------------------------------------------
# Agent scope
# ---------------------------------------------------------------------------


class TestAgentScope:
    def test_slr_agents_not_in_scope(self):
        slr = [
            "harvest-impl-a", "harvest-val-b", "screen-impl-b", "screen-val-a",
            "extract-impl-a", "extract-val-b", "synth-impl-b", "synth-val-a",
            "prisma-impl-b", "prisma-val-a",
        ]
        for agent in slr:
            assert agent not in ELIS_PLATFORM_AGENTS

    def test_github_agent_not_in_scope(self):
        assert "github-agent" not in ELIS_PLATFORM_AGENTS

    def test_pm_not_in_scope(self):
        assert "pm" not in ELIS_PLATFORM_AGENTS

    def test_infra_agents_in_scope(self):
        for a in ["infra-impl-a", "infra-impl-b", "infra-val-a", "infra-val-b"]:
            assert a in ELIS_PLATFORM_AGENTS

    def test_prog_agents_in_scope(self):
        for a in ["prog-impl-a", "prog-impl-b", "prog-val-a", "prog-val-b"]:
            assert a in ELIS_PLATFORM_AGENTS
