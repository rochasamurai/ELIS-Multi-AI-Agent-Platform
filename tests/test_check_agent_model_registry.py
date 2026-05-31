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
    check_model_in_global_allowlist,
    load_agent_models,
    load_global_model_allowlist,
    run_check,
    sync_agent_catalogue,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _write_openclaw_config(
    tmp_path: Path,
    agent_entries: list[dict],
    global_models: dict | None = None,
) -> Path:
    agents_section: dict = {"list": agent_entries}
    if global_models is not None:
        agents_section["defaults"] = {"models": global_models}
    cfg = {"agents": agents_section}
    p = tmp_path / "openclaw.json"
    p.write_text(json.dumps(cfg), encoding="utf-8")
    return p


def _agent_entry(agent_id: str, model: str | None = None) -> dict:
    entry: dict = {"id": agent_id, "workspace": f"/opt/elis/agent-worktrees/{agent_id}"}
    if model is not None:
        entry["model"] = model
    return entry


def _write_agent_models_json(
    agents_root: Path, agent_id: str, model_ids: list[str]
) -> Path:
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


def _all_test_global_models() -> dict:
    """Return agents.defaults.models dict covering all ELIS platform test models."""
    return {f"openrouter/test/{a}-model": {} for a in ELIS_PLATFORM_AGENTS}


# ---------------------------------------------------------------------------
# load_agent_models
# ---------------------------------------------------------------------------


class TestLoadAgentModels:
    def test_returns_dict_of_id_to_model(self, tmp_path):
        cfg = _write_openclaw_config(
            tmp_path,
            [
                _agent_entry("infra-impl-a", "openrouter/qwen/qwen3-coder-flash"),
                _agent_entry("infra-val-b", "openrouter/z-ai/glm-5.1"),
            ],
        )
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
# load_global_model_allowlist
# ---------------------------------------------------------------------------


class TestLoadGlobalModelAllowlist:
    def test_returns_set_of_model_ids(self, tmp_path):
        cfg = _write_openclaw_config(
            tmp_path,
            [_agent_entry("infra-impl-a", "openrouter/qwen/qwen3-coder-flash")],
            global_models={
                "openrouter/qwen/qwen3-coder-flash": {},
                "openrouter/z-ai/glm-5.1": {},
            },
        )
        result = load_global_model_allowlist(cfg)
        assert result == {
            "openrouter/qwen/qwen3-coder-flash",
            "openrouter/z-ai/glm-5.1",
        }

    def test_raises_when_key_missing(self, tmp_path):
        cfg = _write_openclaw_config(
            tmp_path, [_agent_entry("infra-impl-a", "openrouter/x/y")]
        )
        with pytest.raises(
            KeyError, match="agents.defaults.models missing from config"
        ):
            load_global_model_allowlist(cfg)

    def test_raises_when_not_dict(self, tmp_path):
        agents_section: dict = {
            "list": [_agent_entry("infra-impl-a", "openrouter/x/y")],
            "defaults": {"models": ["openrouter/x/y"]},
        }
        cfg_data = {"agents": agents_section}
        p = tmp_path / "openclaw.json"
        p.write_text(json.dumps(cfg_data), encoding="utf-8")
        with pytest.raises(ValueError, match="agents.defaults.models must be a dict"):
            load_global_model_allowlist(p)


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
# check_model_in_global_allowlist
# ---------------------------------------------------------------------------


class TestCheckModelInGlobalAllowlist:
    def test_exact_match_pass(self):
        allowlist = {"openrouter/qwen/qwen3-coder-flash", "openrouter/z-ai/glm-5.1"}
        found, detail = check_model_in_global_allowlist(
            "openrouter/qwen/qwen3-coder-flash", allowlist
        )
        assert found is True
        assert "exact match" in detail

    def test_exact_match_fail(self):
        allowlist = {"openrouter/other/model"}
        found, detail = check_model_in_global_allowlist(
            "openrouter/qwen/qwen3-coder-flash", allowlist
        )
        assert found is False
        assert "not found" in detail

    def test_wildcard_match_pass(self):
        allowlist = {"openrouter/*"}
        found, detail = check_model_in_global_allowlist(
            "openrouter/z-ai/glm-5.1", allowlist
        )
        assert found is True
        assert "wildcard" in detail
        assert "openrouter/*" in detail

    def test_wildcard_no_match(self):
        allowlist = {"claude-cli/*"}
        found, detail = check_model_in_global_allowlist(
            "openrouter/z-ai/glm-5.1", allowlist
        )
        assert found is False
        assert "not found" in detail


# ---------------------------------------------------------------------------
# run_check — three-layer PASS
# ---------------------------------------------------------------------------


class TestRunCheckPass:
    def test_all_agents_both_layers_pass(self, tmp_path):
        cfg_dir = tmp_path / "cfg"
        agents_dir = tmp_path / "agents"
        cfg_dir.mkdir()
        cfg = _write_openclaw_config(
            cfg_dir,
            [
                _agent_entry(a, f"openrouter/test/{a}-model")
                for a in ELIS_PLATFORM_AGENTS
            ],
            global_models=_all_test_global_models(),
        )
        _all_agents_models_json(agents_dir)
        assert run_check(cfg, agents_dir, c8=False) == 0

    def test_extra_agents_in_openclaw_ignored(self, tmp_path):
        cfg_dir = tmp_path / "cfg"
        agents_dir = tmp_path / "agents"
        cfg_dir.mkdir()
        entries = [
            _agent_entry(a, f"openrouter/test/{a}-model") for a in ELIS_PLATFORM_AGENTS
        ]
        entries.append(_agent_entry("github-agent", "openai-codex/gpt-5.4-mini"))
        entries.append(_agent_entry("pm", "claude-cli/claude-sonnet-4-6"))
        cfg = _write_openclaw_config(
            cfg_dir, entries, global_models=_all_test_global_models()
        )
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
        present_models = {
            f"openrouter/test/{a}-model": {}
            for a in ELIS_PLATFORM_AGENTS
            if a != "infra-val-b"
        }
        cfg = _write_openclaw_config(cfg_dir, entries, global_models=present_models)
        _all_agents_models_json(agents_dir)
        assert run_check(cfg, agents_dir, c8=False) == 1

    def test_agent_model_empty_exits_1(self, tmp_path):
        cfg_dir = tmp_path / "cfg"
        agents_dir = tmp_path / "agents"
        cfg_dir.mkdir()
        entries = [
            _agent_entry(a, f"openrouter/test/{a}-model") for a in ELIS_PLATFORM_AGENTS
        ]
        entries = [
            e if e["id"] != "infra-impl-b" else {"id": "infra-impl-b"} for e in entries
        ]
        present_models = {
            f"openrouter/test/{a}-model": {}
            for a in ELIS_PLATFORM_AGENTS
            if a != "infra-impl-b"
        }
        cfg = _write_openclaw_config(cfg_dir, entries, global_models=present_models)
        _all_agents_models_json(agents_dir)
        assert run_check(cfg, agents_dir, c8=False) == 1

    def test_bad_openclaw_config_exits_1(self, tmp_path):
        bad = tmp_path / "bad.json"
        bad.write_text("{not valid json", encoding="utf-8")
        assert run_check(bad, tmp_path / "agents", c8=False) == 1

    def test_missing_openclaw_config_exits_1(self, tmp_path):
        assert (
            run_check(tmp_path / "nonexistent.json", tmp_path / "agents", c8=False) == 1
        )


# ---------------------------------------------------------------------------
# run_check — Layer 2 failures (global model allowlist)
# ---------------------------------------------------------------------------


class TestRunCheckLayer2GlobalAllowlistFail:
    def test_l2_fail_when_model_absent_from_allowlist(self, tmp_path):
        cfg_dir = tmp_path / "cfg"
        agents_dir = tmp_path / "agents"
        cfg_dir.mkdir()
        entries = [
            _agent_entry(a, f"openrouter/test/{a}-model") for a in ELIS_PLATFORM_AGENTS
        ]
        # Global allowlist contains a different model — agents' test models are absent
        cfg = _write_openclaw_config(
            cfg_dir, entries, global_models={"openrouter/other/model": {}}
        )
        _all_agents_models_json(agents_dir)
        assert run_check(cfg, agents_dir, c8=False) == 1

    def test_l2_fail_when_agents_defaults_models_missing(self, tmp_path):
        cfg_dir = tmp_path / "cfg"
        agents_dir = tmp_path / "agents"
        cfg_dir.mkdir()
        entries = [
            _agent_entry(a, f"openrouter/test/{a}-model") for a in ELIS_PLATFORM_AGENTS
        ]
        # No global_models → agents.defaults.models key absent → KeyError → exit 1
        cfg = _write_openclaw_config(cfg_dir, entries)
        _all_agents_models_json(agents_dir)
        assert run_check(cfg, agents_dir, c8=False) == 1


# ---------------------------------------------------------------------------
# run_check — Layer 3 failures (per-agent models.json)
# ---------------------------------------------------------------------------


class TestRunCheckLayer2Fail:
    def test_models_json_missing_exits_1(self, tmp_path):
        cfg_dir = tmp_path / "cfg"
        agents_dir = tmp_path / "agents"
        cfg_dir.mkdir()
        cfg = _write_openclaw_config(
            cfg_dir,
            [
                _agent_entry(a, f"openrouter/test/{a}-model")
                for a in ELIS_PLATFORM_AGENTS
            ],
            global_models=_all_test_global_models(),
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
            [
                _agent_entry(a, f"openrouter/test/{a}-model")
                for a in ELIS_PLATFORM_AGENTS
            ],
            global_models=_all_test_global_models(),
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
            [
                _agent_entry(a, f"openrouter/test/{a}-model")
                for a in ELIS_PLATFORM_AGENTS
            ],
            global_models=_all_test_global_models(),
        )
        _all_agents_models_json(agents_dir)
        # Override infra-val-a with wrong model in models.json
        _write_agent_models_json(
            agents_dir, "infra-val-a", ["openrouter/other/wrong-model"]
        )
        assert run_check(cfg, agents_dir, c8=False) == 1

    def test_agent_directory_missing_exits_1(self, tmp_path):
        cfg_dir = tmp_path / "cfg"
        agents_dir = tmp_path / "agents"
        cfg_dir.mkdir()
        cfg = _write_openclaw_config(
            cfg_dir,
            [
                _agent_entry(a, f"openrouter/test/{a}-model")
                for a in ELIS_PLATFORM_AGENTS
            ],
            global_models=_all_test_global_models(),
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
        monkeypatch.setattr(
            sys,
            "argv",
            ["check_agent_model_registry.py", "--sync", "--config", str(cfg)],
        )
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
        entries = [
            _agent_entry(a, "unknown-provider/some-model") for a in ELIS_PLATFORM_AGENTS
        ]
        cfg = _write_openclaw_config(
            cfg_dir,
            entries,
            global_models={"unknown-provider/some-model": {}},
        )
        for a in ELIS_PLATFORM_AGENTS:
            _write_agent_models_json(agents_dir, a, ["unknown-provider/some-model"])
        # C8 warning does not change exit code — still 0 (all three layers pass)
        assert run_check(cfg, agents_dir, c8=True) == 0


# ---------------------------------------------------------------------------
# Agent scope
# ---------------------------------------------------------------------------


class TestAgentScope:
    def test_slr_agents_not_in_scope(self):
        slr = [
            "harvest-impl-a",
            "harvest-val-b",
            "screen-impl-b",
            "screen-val-a",
            "extract-impl-a",
            "extract-val-b",
            "synth-impl-b",
            "synth-val-a",
            "prisma-impl-b",
            "prisma-val-a",
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


# ---------------------------------------------------------------------------
# --sync-agent-catalogue mode
# ---------------------------------------------------------------------------


def _full_fixture(
    tmp_path: Path,
    agent_id: str = "infra-val-b",
    model: str = "openrouter/z-ai/glm-5.1",
    include_model_in_catalog: bool = False,
):
    """Build a self-contained fixture: openclaw.json + all agents' models.json."""
    cfg_dir = tmp_path / "cfg"
    agents_dir = tmp_path / "agents"
    cfg_dir.mkdir()

    entries = [
        _agent_entry(a, f"openrouter/test/{a}-model") for a in ELIS_PLATFORM_AGENTS
    ]
    # Override the target agent's model
    entries = [
        e if e["id"] != agent_id else _agent_entry(agent_id, model) for e in entries
    ]

    global_models = {f"openrouter/test/{a}-model": {} for a in ELIS_PLATFORM_AGENTS}
    global_models[model] = {}

    cfg = _write_openclaw_config(cfg_dir, entries, global_models=global_models)

    for a in ELIS_PLATFORM_AGENTS:
        if a == agent_id:
            # Write minimal models.json without the target model (L3 gap)
            agent_dir = agents_dir / a / "agent"
            agent_dir.mkdir(parents=True, exist_ok=True)
            existing_ids = (
                [model] if include_model_in_catalog else ["openrouter/other/old"]
            )
            data = {
                "providers": {
                    "openrouter": {
                        "baseUrl": "https://openrouter.ai/v1",
                        "models": [{"id": mid, "name": mid} for mid in existing_ids],
                    }
                }
            }
            (agent_dir / "models.json").write_text(json.dumps(data), encoding="utf-8")
        else:
            _write_agent_models_json(agents_dir, a, [f"openrouter/test/{a}-model"])

    return cfg, agents_dir


class TestSyncAgentCatalogue:
    def test_requires_approve_flag(self, monkeypatch, capsys):
        import check_agent_model_registry as mod

        monkeypatch.setattr(
            sys,
            "argv",
            [
                "check_agent_model_registry.py",
                "--sync-agent-catalogue",
                "--agent",
                "infra-val-b",
            ],
        )
        with pytest.raises(SystemExit) as exc_info:
            mod.main()
        assert exc_info.value.code == 2
        assert "--approve" in capsys.readouterr().out

    def test_requires_agent_flag(self, monkeypatch, capsys):
        import check_agent_model_registry as mod

        monkeypatch.setattr(
            sys,
            "argv",
            [
                "check_agent_model_registry.py",
                "--sync-agent-catalogue",
                "--approve",
            ],
        )
        with pytest.raises(SystemExit) as exc_info:
            mod.main()
        assert exc_info.value.code == 2
        assert "--agent" in capsys.readouterr().out

    def test_creates_backup(self, tmp_path):
        cfg, agents_dir = _full_fixture(tmp_path, agent_id="infra-val-b")
        mjs_path = agents_dir / "infra-val-b" / "agent" / "models.json"
        result = sync_agent_catalogue("infra-val-b", cfg, agents_dir)
        assert result == 0
        backups = list(mjs_path.parent.glob("models.json.bak.*"))
        assert len(backups) == 1

    def test_adds_model_to_existing_provider(self, tmp_path):
        model = "openrouter/z-ai/glm-5.1"
        cfg, agents_dir = _full_fixture(tmp_path, agent_id="infra-val-b", model=model)
        result = sync_agent_catalogue("infra-val-b", cfg, agents_dir)
        assert result == 0
        mjs_path = agents_dir / "infra-val-b" / "agent" / "models.json"
        data = json.loads(mjs_path.read_text(encoding="utf-8"))
        ids = [e["id"] for e in data["providers"]["openrouter"]["models"]]
        assert model in ids

    def test_skips_duplicate(self, tmp_path, capsys):
        model = "openrouter/z-ai/glm-5.1"
        cfg, agents_dir = _full_fixture(
            tmp_path, agent_id="infra-val-b", model=model, include_model_in_catalog=True
        )
        mjs_path = agents_dir / "infra-val-b" / "agent" / "models.json"
        content_before = mjs_path.read_text(encoding="utf-8")
        result = sync_agent_catalogue("infra-val-b", cfg, agents_dir)
        assert result == 0
        assert mjs_path.read_text(encoding="utf-8") == content_before
        assert "already present" in capsys.readouterr().out

    def test_validates_written_json(self, tmp_path):
        cfg, agents_dir = _full_fixture(tmp_path, agent_id="infra-val-b")
        result = sync_agent_catalogue("infra-val-b", cfg, agents_dir)
        assert result == 0
        mjs_path = agents_dir / "infra-val-b" / "agent" / "models.json"
        # Must be valid JSON (no JSONDecodeError)
        parsed = json.loads(mjs_path.read_text(encoding="utf-8"))
        assert "providers" in parsed

    def test_check_mode_unaffected(self, tmp_path):
        """--check still exits 0 after a successful sync (fixture config)."""
        cfg, agents_dir = _full_fixture(tmp_path)
        # Sync first
        sync_agent_catalogue("infra-val-b", cfg, agents_dir)
        # All agents in fixture have correct models; run_check must pass
        assert run_check(cfg, agents_dir, c8=False) == 0

    def test_check_mode_still_readonly(self, monkeypatch, capsys):
        """--check must not create any backup files."""
        import check_agent_model_registry as mod
        import tempfile

        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            cfg_dir = td_path / "cfg"
            agents_dir = td_path / "agents"
            cfg_dir.mkdir()
            entries = [
                _agent_entry(a, f"openrouter/test/{a}-model")
                for a in ELIS_PLATFORM_AGENTS
            ]
            cfg = _write_openclaw_config(
                cfg_dir, entries, global_models=_all_test_global_models()
            )
            _all_agents_models_json(agents_dir)
            monkeypatch.setattr(
                sys,
                "argv",
                [
                    "check_agent_model_registry.py",
                    "--check",
                    "--config",
                    str(cfg),
                    "--agents-root",
                    str(agents_dir),
                ],
            )
            mod.main()
            # Confirm no backup files created anywhere under agents_dir
            backups = list(agents_dir.rglob("models.json.bak.*"))
            assert backups == []
