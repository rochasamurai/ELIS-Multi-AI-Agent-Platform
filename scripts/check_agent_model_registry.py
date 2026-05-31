"""
ELIS Platform Agent Model Registry Checker — PE-OPS-A2A-PRODUCTION-02

Validates that every ELIS Platform agent in scope has an explicit model
entry in the live OpenClaw config, that the same model appears in the
global model allowlist, and that the model is registered in the agent's
per-agent models.json catalog.

Three-layer check:
  Layer 1 (L1): /home/samurai/.openclaw/openclaw.json → agents.list[].model
                agent exists with non-empty model field
  Layer 2 (L2): /home/samurai/.openclaw/openclaw.json → agents.defaults.models
                configured model appears in global allowlist (exact or provider wildcard)
  Layer 3 (L3): /home/samurai/.openclaw/agents/<agentId>/agent/models.json
                configured model registered in per-agent catalogue

Usage:
  python scripts/check_agent_model_registry.py [--check] [--sync] [--c8]
      [--config PATH] [--agents-root PATH]

Modes:
  --check       (default) Read-only validation. Exit 0 = PASS, 1 = FAIL.
  --sync        Not implemented. Exits 2 immediately.
  --c8          Advisory: check model strings against known provider prefixes.
                Failures are warnings only; never causes non-zero exit.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Optional

DEFAULT_CONFIG = Path("/home/samurai/.openclaw/openclaw.json")
DEFAULT_AGENTS_ROOT = Path("/home/samurai/.openclaw/agents")

ELIS_PLATFORM_AGENTS = [
    "infra-impl-a",
    "infra-impl-b",
    "infra-val-a",
    "infra-val-b",
    "prog-impl-a",
    "prog-impl-b",
    "prog-val-a",
    "prog-val-b",
]

KNOWN_PROVIDER_PREFIXES = [
    "openrouter/",
    "claude-cli/",
    "openai/",
    "openai-codex/",
    "anthropic/",
    "deepseek/",
    "google/",
]


def load_agent_models(config_path: Path) -> dict[str, Optional[str]]:
    """Return {agentId: model} for all agents in live config. Model is None if absent."""
    with config_path.open(encoding="utf-8") as fh:
        cfg = json.load(fh)
    agents = cfg.get("agents", {}).get("list", [])
    return {a.get("id", ""): a.get("model") for a in agents if a.get("id")}


def load_global_model_allowlist(config_path: Path) -> set[str]:
    """Return set of model IDs from agents.defaults.models (keys of the dict)."""
    with config_path.open(encoding="utf-8") as fh:
        cfg = json.load(fh)
    allowlist = cfg.get("agents", {}).get("defaults", {}).get("models", None)
    if allowlist is None:
        raise KeyError("agents.defaults.models missing from config")
    if not isinstance(allowlist, dict):
        raise ValueError("agents.defaults.models must be a dict")
    return set(allowlist.keys())


def check_model_in_global_allowlist(model: str, allowlist: set[str]) -> tuple[bool, str]:
    """
    Check that model is in the global allowlist.
    Supports exact match and provider wildcard (e.g. 'openrouter/*').
    Returns (found: bool, detail: str).
    """
    if model in allowlist:
        return True, "exact match in agents.defaults.models"
    provider = model.split("/")[0]
    wildcard = f"{provider}/*"
    if wildcard in allowlist:
        return True, f"wildcard match '{wildcard}' in agents.defaults.models"
    return False, f"model '{model}' not found in agents.defaults.models (no exact or wildcard match)"


def check_model_in_agent_catalog(
    agent_id: str, model: str, agents_root: Path
) -> tuple[bool, str]:
    """
    Check that `model` appears as an id in the per-agent models.json catalog.

    Returns (found: bool, detail: str).
    Never mutates any file.
    """
    mjs_path = agents_root / agent_id / "agent" / "models.json"
    if not mjs_path.exists():
        return False, f"models.json missing: {mjs_path}"
    try:
        data = json.loads(mjs_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return False, f"models.json invalid JSON at {mjs_path}: {exc}"
    providers = data.get("providers", {})
    if not isinstance(providers, dict):
        return False, f"models.json malformed (providers is not a dict): {mjs_path}"
    for provider_data in providers.values():
        for entry in provider_data.get("models", []):
            if entry.get("id") == model:
                return True, f"found in {mjs_path}"
    return False, f"model '{model}' not found in any provider list in {mjs_path}"


def check_c8(models: dict[str, Optional[str]]) -> None:
    """Advisory: warn if any model string does not match a known provider prefix."""
    for agent_id, model in models.items():
        if agent_id not in ELIS_PLATFORM_AGENTS:
            continue
        if model is None:
            continue
        if not any(model.startswith(p) for p in KNOWN_PROVIDER_PREFIXES):
            print(f"  [C8-WARN] {agent_id}: model '{model}' has unrecognised provider prefix")


def run_check(config_path: Path, agents_root: Path, c8: bool) -> int:
    try:
        all_models = load_agent_models(config_path)
    except (FileNotFoundError, json.JSONDecodeError, KeyError) as exc:
        print(f"ERROR: Cannot load config from {config_path}: {exc}")
        return 1

    try:
        global_allowlist = load_global_model_allowlist(config_path)
    except (KeyError, ValueError) as exc:
        print(f"ERROR: Cannot load global model allowlist: {exc}")
        return 1

    gaps: list[str] = []
    print("ELIS Platform Agent Model Registry Check")
    print(f"  openclaw config : {config_path}")
    print(f"  agents root     : {agents_root}")
    print()

    for agent_id in ELIS_PLATFORM_AGENTS:
        model = all_models.get(agent_id)

        # L1: openclaw.json — agent present with non-empty model
        if not model:
            print(f"  FAIL  {agent_id}")
            print(f"        L1: agent missing or model empty in {config_path}")
            gaps.append(agent_id)
            continue

        print(f"  CHECK {agent_id}: {model}")
        print(f"        L1: PASS (openclaw.json)")

        agent_failed = False

        # L2: global model allowlist — agents.defaults.models
        l2_ok, l2_detail = check_model_in_global_allowlist(model, global_allowlist)
        if l2_ok:
            print(f"        L2: PASS ({l2_detail})")
        else:
            print(f"        L2: FAIL ({l2_detail})")
            agent_failed = True

        # L3: per-agent models.json catalog
        l3_ok, l3_detail = check_model_in_agent_catalog(agent_id, model, agents_root)
        if l3_ok:
            print(f"        L3: PASS ({l3_detail})")
        else:
            print(f"        L3: FAIL ({l3_detail})")
            agent_failed = True

        if agent_failed:
            gaps.append(agent_id)

    if c8:
        print()
        print("C8 advisory check:")
        try:
            check_c8(all_models)
            print("  C8: no unrecognised provider prefixes found")
        except Exception as exc:
            print(f"  [C8-WARN] Advisory check error (non-fatal): {exc}")

    print()
    if gaps:
        print(f"RESULT: FAIL — {len(gaps)} agent(s) failed registry check: {', '.join(gaps)}")
        return 1
    print("RESULT: PASS — all ELIS Platform agents pass three-layer model registry check")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", default=False)
    parser.add_argument("--sync", action="store_true", default=False)
    parser.add_argument("--c8", action="store_true", default=False)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--agents-root", type=Path, default=DEFAULT_AGENTS_ROOT)
    args = parser.parse_args()

    if args.sync:
        print(
            "SYNC NOT IMPLEMENTED: model registry sync requires Supervisor authorisation. "
            "Run with --check only."
        )
        sys.exit(2)

    return run_check(args.config, args.agents_root, c8=args.c8)


if __name__ == "__main__":
    sys.exit(main())
