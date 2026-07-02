"""
ELIS GitHub — Agent Skill definition.

Defines the single GitHub-operations skill exposed by the
ELIS GitHub A2A server.  Uses the official SDK protobuf construction
pattern (ParseDict) — never Pydantic kwargs.
"""

from a2a.types import AgentSkill
from a2a.utils.proto_utils import ParseDict

# fmt: off
GITHUB_SKILL_DICT: dict = {
    "id": "elis-github-execute",
    "name": "GitHub Execute",
    "description": (
        "GitHub operations skill for ELIS GitHub agent.  "
        "Accepts structured GitHub operation requests from ELIS PM "
        "and returns operation results via the A2A channel.  "
        "All operations are scoped to the elis-core GitHub organisation."
    ),
    "tags": ["elis", "github", "operations"],
    "examples": ["create PR", "review PR", "merge PR", "check CI status"],
    "input_modes": ["application/json"],
    "output_modes": ["application/json"],
}
# fmt: on


def build_github_skill() -> AgentSkill:
    """Return the canonical ELIS GitHub AgentSkill protobuf object."""
    return ParseDict(GITHUB_SKILL_DICT, AgentSkill())
