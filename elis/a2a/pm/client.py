"""
ELIS PM → ELIS Advisor — A2A client scaffold.

Provides the minimal official SDK client path from ELIS PM to ELIS Advisor.
Uses:
  - ``A2ACardResolver`` to fetch the agent card from the well-known endpoint
  - ``JsonRpcTransport`` for JSON-RPC message delivery
  - ``Client`` as the top-level send interface

This is a scaffold: ``send_message`` demonstrates construction of the
client stack and verifies the well-known card is reachable, but does not
implement full PM message routing.  That is deferred to subsequent gates.

Localhost-only: ``base_url`` must be ``http://127.0.0.1:<port>``.
No public URL accepted.
"""
import logging
from urllib.parse import urlparse

import httpx

from a2a.client.card_resolver import A2ACardResolver, AGENT_CARD_WELL_KNOWN_PATH
from a2a.client.client import Client
from a2a.client.client_factory import ClientFactory
from a2a.client.transports.jsonrpc import JsonRpcTransport
from a2a.types import AgentCard

logger = logging.getLogger(__name__)

_ALLOWED_HOST = "127.0.0.1"


def _assert_localhost(url: str) -> None:
    """Raise ValueError if *url* is not a localhost URL."""
    parsed = urlparse(url)
    if parsed.hostname != _ALLOWED_HOST:
        raise ValueError(
            f"Localhost-only policy: host must be '{_ALLOWED_HOST}', "
            f"got {parsed.hostname!r} in {url!r}"
        )


class AdvisorClient:
    """
    Minimal A2A client scaffold for ELIS PM → ELIS Advisor communication.

    Args:
        base_url: Advisor server base URL.  Must be ``http://127.0.0.1:<port>``.
        rpc_path: JSON-RPC endpoint path (default ``/rpc``).
    """

    def __init__(
        self,
        base_url: str = "http://127.0.0.1:9500",
        rpc_path: str = "/rpc",
    ) -> None:
        _assert_localhost(base_url)
        self.base_url = base_url.rstrip("/")
        self.rpc_url = self.base_url + rpc_path
        self._rpc_path = rpc_path

    async def resolve_card(self) -> AgentCard:
        """
        Fetch and return the ELIS Advisor AgentCard from the well-known endpoint.

        Requires a live server at ``self.base_url``.
        """
        async with httpx.AsyncClient(base_url=self.base_url) as http:
            resolver = A2ACardResolver(http)
            card = await resolver.get_agent_card()
        logger.info(
            "AdvisorClient.resolve_card: resolved card name=%r version=%r",
            card.name,
            card.version,
        )
        return card

    def build_transport(
        self,
        http_client: httpx.AsyncClient,
        card: AgentCard,
    ) -> JsonRpcTransport:
        """
        Construct and return a JsonRpcTransport bound to the given card and HTTP client.

        The caller is responsible for the ``http_client`` lifecycle.
        """
        return JsonRpcTransport(
            httpx_client=http_client,
            agent_card=card,
            url=self.rpc_url,
        )

    def build_client(self, card: AgentCard) -> Client:
        """
        Return a concrete ``Client`` instance via the official SDK factory.

        Uses ``ClientFactory.create(card)`` — the SDK-approved construction
        path.  ``a2a.client.client.Client`` is abstract in a2a-sdk 1.1.0
        and cannot be instantiated directly; ``ClientFactory`` returns a
        ``BaseClient`` (concrete ``Client`` subclass) wired with the
        appropriate transport derived from the card's ``supported_interfaces``.

        Args:
            card: An ``AgentCard`` with at least one compatible interface
                  (protocol_binding='JSONRPC', protocol_version='1.0').

        Returns:
            A concrete ``Client`` instance (``BaseClient``).
        """
        factory = ClientFactory()
        return factory.create(card)

    def __repr__(self) -> str:
        return (
            f"AdvisorClient(base_url={self.base_url!r}, rpc_url={self.rpc_url!r})"
        )
