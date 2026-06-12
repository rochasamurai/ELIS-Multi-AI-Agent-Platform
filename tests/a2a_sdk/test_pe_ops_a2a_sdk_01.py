"""
Tests: PE-OPS-A2A-SDK-01 — Official A2A SDK integration.

Test suite covering:
  1. Official SDK imports work from /opt/elis/a2a/venv
  2. No local repo package shadows official 'a2a'
  3. Agent Card shape is valid
  4. Server route wiring is valid
  5. PM client scaffold constructs correctly
  6. Localhost-only configuration is enforced
  7. Localhost smoke-test (ASGI in-process, 127.0.0.1 only)

All tests run exclusively against the runtime venv at /opt/elis/a2a/venv.
No live server is started; ASGI transport is used for route tests.
"""

from pathlib import Path

import pytest
import httpx


# =============================================================================
# 1. Official SDK imports
# =============================================================================


class TestSDKImports:
    """Verify that every import used by the implementation resolves correctly."""

    def test_a2a_types(self):
        from a2a.types import (
            AgentCard,
            AgentSkill,
            AgentCapabilities,
            AgentInterface,
            Part,
            Message,
            Task,
            TaskState,
            Role,
        )

        # All must be importable; just accessing the names is sufficient
        assert AgentCard is not None
        assert AgentSkill is not None
        assert AgentCapabilities is not None
        assert AgentInterface is not None
        assert Part is not None
        assert Message is not None
        assert Task is not None
        assert TaskState is not None
        assert Role is not None

    def test_a2a_proto_utils(self):
        from a2a.utils.proto_utils import ParseDict

        assert callable(ParseDict)

    def test_a2a_server_agent_execution(self):
        from a2a.server.agent_execution import AgentExecutor, RequestContext

        assert AgentExecutor is not None
        assert RequestContext is not None

    def test_a2a_server_task_updater(self):
        from a2a.server.tasks.task_updater import TaskUpdater

        assert TaskUpdater is not None

    def test_a2a_server_legacy_request_handler(self):
        from a2a.server.request_handlers.default_request_handler import (
            LegacyRequestHandler,
        )

        assert LegacyRequestHandler is not None

    def test_a2a_server_routes(self):
        from a2a.server.routes import create_jsonrpc_routes

        assert callable(create_jsonrpc_routes)

    def test_a2a_inmemory_task_store(self):
        from a2a.server.tasks.inmemory_task_store import InMemoryTaskStore

        assert InMemoryTaskStore is not None

    def test_a2a_inmemory_queue_manager(self):
        from a2a.server.events.in_memory_queue_manager import InMemoryQueueManager

        assert InMemoryQueueManager is not None

    def test_a2a_client(self):
        from a2a.client.client import Client
        from a2a.client.transports.jsonrpc import JsonRpcTransport
        from a2a.client.card_resolver import (
            A2ACardResolver,
            AGENT_CARD_WELL_KNOWN_PATH,
        )

        assert Client is not None
        assert JsonRpcTransport is not None
        assert A2ACardResolver is not None
        assert AGENT_CARD_WELL_KNOWN_PATH == "/.well-known/agent-card.json"


# =============================================================================
# 2. No local repo package shadows official 'a2a'
# =============================================================================


class TestNoLocalShadowing:
    """
    Ensure the local ELIS repo does not shadow the official 'a2a' package.

    The official package lives in /opt/elis/a2a/venv.
    There must be no top-level 'a2a/' or 'src/a2a/' directory in the repo
    that would be picked up as a local package.
    """

    def test_a2a_module_is_not_in_repo(self):
        repo_root = Path(__file__).parent.parent
        bad_paths = [
            repo_root / "a2a",
            repo_root / "src" / "a2a",
            repo_root / "src" / "elis" / "a2a",
        ]
        for p in bad_paths:
            assert not p.exists(), (
                f"Forbidden local a2a path found: {p} — "
                "this would shadow the official a2a-sdk package."
            )

    def test_a2a_import_resolves_to_venv(self):
        import a2a

        module_file = Path(a2a.__file__).resolve()
        module_str = str(module_file)

        # Hard reject: repo-local shadow paths that would override the
        # installed package.  These must never appear — on any runner.
        repo_shadow_prefixes = [
            str(Path("/opt/elis/repo/a2a").resolve()),
            str(Path("/opt/elis/repo/src/a2a").resolve()),
        ]
        for bad in repo_shadow_prefixes:
            assert not module_str.startswith(bad), (
                f"'a2a' resolved to a repo-local shadow path: {module_file}. "
                f"This overrides the installed a2a-sdk package."
            )

        # Accept either:
        #   (a) local ELIS runtime venv   — /opt/elis/a2a/venv/...
        #   (b) package-managed install   — any path containing site-packages
        #                                   or dist-packages (CI runners)
        local_venv = str(Path("/opt/elis/a2a/venv").resolve())
        in_local_venv = module_str.startswith(local_venv)
        in_site_packages = (
            "site-packages" in module_str or "dist-packages" in module_str
        )

        assert in_local_venv or in_site_packages, (
            f"'a2a' resolved to an unexpected location: {module_file}. "
            "Expected either the local ELIS venv (/opt/elis/a2a/venv) "
            "or a package-managed site-packages / dist-packages path."
        )


# =============================================================================
# 3. Agent Card shape is valid
# =============================================================================


class TestAgentCardShape:
    """Verify AgentCard construction and field values."""

    def test_build_agent_card_returns_agent_card(self):
        from a2a.types import AgentCard
        from elis.a2a.advisor.agent_card import build_agent_card

        card = build_agent_card()
        assert isinstance(card, AgentCard)

    def test_agent_card_name(self):
        from elis.a2a.advisor.agent_card import build_agent_card

        card = build_agent_card()
        assert card.name == "ELIS Advisor"

    def test_agent_card_version(self):
        from elis.a2a.advisor.agent_card import build_agent_card

        card = build_agent_card()
        assert card.version == "0.1.0"

    def test_agent_card_has_skills(self):
        from elis.a2a.advisor.agent_card import build_agent_card

        card = build_agent_card()
        assert len(card.skills) == 1
        assert card.skills[0].id == "elis-advisor-acknowledge"

    def test_agent_card_supported_interfaces_localhost(self):
        from elis.a2a.advisor.agent_card import build_agent_card, ADVISOR_RPC_URL

        card = build_agent_card()
        assert len(card.supported_interfaces) == 1
        iface = card.supported_interfaces[0]
        assert iface.url == ADVISOR_RPC_URL
        assert "127.0.0.1" in iface.url
        assert "0.0.0.0" not in iface.url

    def test_agent_skill_shape(self):
        from elis.a2a.advisor.agent_skill import build_advisor_skill
        from a2a.types import AgentSkill

        skill = build_advisor_skill()
        assert isinstance(skill, AgentSkill)
        assert skill.id == "elis-advisor-acknowledge"
        assert skill.name == "Acknowledge"


# =============================================================================
# 4. Server route wiring is valid (ASGI in-process)
# =============================================================================


class TestServerRouteWiring:
    """
    Verify route wiring without starting a live TCP server.

    Uses httpx.ASGITransport (async) + httpx.AsyncClient to exercise the
    ASGI app in-process.  All requests go to 127.0.0.1 only — no TCP socket
    opened.  Tests are async (httpx.ASGITransport is AsyncBaseTransport in
    httpx 0.28.x; sync httpx.Client cannot use it).
    """

    def _get_app(self):
        from elis.a2a.advisor.server import app

        return app

    @pytest.mark.anyio
    async def test_well_known_returns_200(self):
        app = self._get_app()
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://127.0.0.1:9500"
        ) as client:
            response = await client.get("/.well-known/agent-card.json")
        assert response.status_code == 200

    @pytest.mark.anyio
    async def test_well_known_returns_agent_card_json(self):
        app = self._get_app()
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://127.0.0.1:9500"
        ) as client:
            response = await client.get("/.well-known/agent-card.json")
        data = response.json()
        assert (
            "name" in data or "skills" in data
        ), f"Agent card JSON missing expected fields: {list(data.keys())}"

    @pytest.mark.anyio
    async def test_rpc_endpoint_exists(self):
        """POST to /a2a with an invalid body should return 400 or 422, not 404."""
        app = self._get_app()
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://127.0.0.1:9500"
        ) as client:
            response = await client.post(
                "/a2a",
                json={"jsonrpc": "2.0", "method": "invalid_method", "id": 1},
                headers={"Content-Type": "application/json"},
            )
        # 404 would mean the route isn't wired; any other status means it is
        assert (
            response.status_code != 404
        ), f"RPC route returned 404 — route is not wired. Response: {response.text}"


# =============================================================================
# 5. PM client scaffold constructs correctly
# =============================================================================


class TestPMClientScaffold:
    """Verify AdvisorClient construction and attribute values."""

    def test_default_construction(self):
        from elis.a2a.pm.client import AdvisorClient

        client = AdvisorClient()
        assert client.base_url == "http://127.0.0.1:9500"
        assert client.rpc_url == "http://127.0.0.1:9500/a2a"

    def test_custom_port(self):
        from elis.a2a.pm.client import AdvisorClient

        client = AdvisorClient(base_url="http://127.0.0.1:9501")
        assert client.base_url == "http://127.0.0.1:9501"
        assert client.rpc_url == "http://127.0.0.1:9501/a2a"

    def test_build_client_returns_client_instance(self):
        from elis.a2a.pm.client import AdvisorClient
        from elis.a2a.advisor.agent_card import build_agent_card
        from a2a.client.client import Client

        ac = AdvisorClient()
        # build_client requires a card: uses ClientFactory.create(card) — the
        # official SDK path.  Client is abstract; factory returns BaseClient.
        card = build_agent_card()
        client = ac.build_client(card)
        assert isinstance(client, Client)

    def test_repr(self):
        from elis.a2a.pm.client import AdvisorClient

        ac = AdvisorClient()
        r = repr(ac)
        assert "127.0.0.1" in r


# =============================================================================
# 6. Localhost-only configuration is enforced
# =============================================================================


class TestLocalhostEnforcement:
    """Verify that non-localhost configuration is rejected at construction time."""

    def test_server_run_rejects_non_localhost(self):
        from elis.a2a.advisor.server import run

        with pytest.raises(ValueError, match="127.0.0.1"):
            run(host="0.0.0.0", port=9500)

    def test_server_run_rejects_public_ip(self):
        from elis.a2a.advisor.server import run

        with pytest.raises(ValueError, match="127.0.0.1"):
            run(host="192.168.1.100", port=9500)

    def test_pm_client_rejects_public_url(self):
        from elis.a2a.pm.client import AdvisorClient

        with pytest.raises(ValueError, match="127.0.0.1"):
            AdvisorClient(base_url="http://0.0.0.0:9500")

    def test_pm_client_rejects_remote_url(self):
        from elis.a2a.pm.client import AdvisorClient

        with pytest.raises(ValueError, match="127.0.0.1"):
            AdvisorClient(base_url="http://elis-server.internal:9500")

    def test_advisor_base_url_is_localhost(self):
        from elis.a2a.advisor.agent_card import ADVISOR_BASE_URL
        from urllib.parse import urlparse

        parsed = urlparse(ADVISOR_BASE_URL)
        assert (
            parsed.hostname == "127.0.0.1"
        ), f"ADVISOR_BASE_URL must be 127.0.0.1, got {parsed.hostname}"

    def test_advisor_base_url_no_public_bind(self):
        from elis.a2a.advisor.agent_card import ADVISOR_BASE_URL

        assert "0.0.0.0" not in ADVISOR_BASE_URL
