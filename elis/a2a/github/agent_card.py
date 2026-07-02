"""
ELIS GitHub — Agent Card definition.

Constructs the official A2A AgentCard protobuf object for the ELIS GitHub
agent.  Localhost-only: ``url`` is always ``http://127.0.0.1:9503``.
No public bind.  No production service install.
"""

from a2a.types import AgentCard
from a2a.utils.proto_utils import ParseDict

from elis.a2a.github.agent_skill import GITHUB_SKILL_DICT

# Localhost-only base URL — never 0.0.0.0 or a public host.
GITHUB_BASE_URL: str = "http://127.0.0.1:9503"
GITHUB_RPC_PATH: str = "/a2a"
# Full RPC endpoint URL — ClientFactory.create() posts to supported_interfaces[0].url
# verbatim, so this must be the complete endpoint path, not just the base URL.
GITHUB_RPC_URL: str = (
    GITHUB_BASE_URL + GITHUB_RPC_PATH
)  # "http://127.0.0.1:9503/a2a"

# fmt: off
_AGENT_CARD_DICT: dict = {
    "name": "ELIS GitHub",
    "description": (
        "ELIS GitHub A2A endpoint.  Provides GitHub operations capability "
        "to ELIS PM via the official Google A2A JSON-RPC protocol.  "
        "All operations are scoped to the elis-core GitHub organisation."
    ),
    "version": "0.1.0",
    "capabilities": {
        "streaming": False,
        "push_notifications": False,
    },
    "skills": [GITHUB_SKILL_DICT],
    "supported_interfaces": [
        {
            "url": GITHUB_RPC_URL,
            # Must be 'JSONRPC' — matches TransportProtocol.JSONRPC (StrEnum).
            # ClientFactory.create() compares i.protocol_binding against
            # TransportProtocol values using string equality; 'A2A_JSONRPC_1_0'
            # does not match and causes "no compatible transports found".
            "protocol_binding": "JSONRPC",
            "protocol_version": "1.0",
        }
    ],
    "default_input_modes": ["application/json"],
    "default_output_modes": ["application/json"],
}
# fmt: on


def build_agent_card() -> AgentCard:
    """Return the canonical ELIS GitHub AgentCard protobuf object."""
    return ParseDict(_AGENT_CARD_DICT, AgentCard())
