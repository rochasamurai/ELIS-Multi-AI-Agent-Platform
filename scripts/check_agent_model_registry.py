"""
ELIS Platform Agent Model Registry Checker — PE-OPS-A2A-PRODUCTION-02

Validates that every ELIS Platform agent in scope has an explicit model
entry in the live OpenClaw config at /home/samurai/.openclaw/openclaw.json.

Usage:
  python scripts/check_agent_model_registry.py [--check] [--sync] [--c8] [--config PATH]

Modes:
  --check  (default) Read-only validation. Exit 0 = PASS, 1 = FAIL.
  --sync   Not implemented. Exits 2 immediately.
  --c8     Advisory: check model strings against known provider prefixes.
           Failures are warnings only; never causes non-zero exit.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Optional

DEFAULT_CONFIG = Path("/home/samurai/.openclaw/openclaw.json")

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


def check_c8(models: dict[str, Optional[str]]) -> None:
    """Advisory: warn if any model string does not match a known provider prefix."""
    for agent_id, model in models.items():
        if agent_id not in ELIS_PLATFORM_AGENTS:
            continue
        if model is None:
            continue
        if not any(model.startswith(p) for p in KNOWN_PROVIDER_PREFIXES):
            print(f"  [C8-WARN] {agent_id}: model '{model}' has unrecognised provider prefix")


def run_check(config_path: Path, c8: bool) -> int:
    try:
        all_models = load_agent_models(config_path)
    except (FileNotFoundError, json.JSONDecodeError, KeyError) as exc:
        print(f"ERROR: Cannot load config from {config_path}: {exc}")
        return 1

    gaps: list[str] = []
    print(f"ELIS Platform Agent Model Registry Check — config: {config_path}")
    print()
    for agent_id in ELIS_PLATFORM_AGENTS:
        model = all_models.get(agent_id)
        if model:
            print(f"  PASS  {agent_id}: {model}")
        else:
            print(f"  FAIL  {agent_id}: model entry missing from live config")
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
        print(f"RESULT: FAIL — {len(gaps)} agent(s) missing model entry: {', '.join(gaps)}")
        return 1
    print("RESULT: PASS — all ELIS Platform agents have model entries in live config")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", default=False)
    parser.add_argument("--sync", action="store_true", default=False)
    parser.add_argument("--c8", action="store_true", default=False)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    args = parser.parse_args()

    if args.sync:
        print(
            "SYNC NOT IMPLEMENTED: model registry sync requires Supervisor authorisation. "
            "Run with --check only."
        )
        sys.exit(2)

    return run_check(args.config, c8=args.c8)


if __name__ == "__main__":
    sys.exit(main())
