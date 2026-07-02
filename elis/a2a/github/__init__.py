"""
ELIS GitHub A2A server.

Exports the GitHub A2A server components: GitHubExecutor, run helper,
and the ASGI ``app`` object for direct test mounting.

Usage (smoke-test only):

    from elis.a2a.github import GitHubExecutor, app, run
"""

from elis.a2a.github.executor import GitHubExecutor
from elis.a2a.github.server import app, run

__all__ = ["GitHubExecutor", "app", "run"]
