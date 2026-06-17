"""ELIS PM A2A client package."""

from elis.a2a.pm.client import AdvisorClient, SupervisorClient, _build_governed_metadata

__all__ = ["AdvisorClient", "SupervisorClient", "_build_governed_metadata"]
