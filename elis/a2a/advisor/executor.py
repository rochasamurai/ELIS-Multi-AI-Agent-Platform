"""
ELIS Advisor — Agent Executor.

Implements the AgentExecutor ABC from the official a2a-sdk.  This is the
minimal acknowledgement executor: it accepts any message, constructs a
plain-text acknowledgement Part, and completes the task immediately.

No external service calls, no governance actions, no production work.
"""

import logging

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.tasks.task_updater import TaskUpdater
from a2a.types import Part
from a2a.utils.proto_utils import ParseDict

logger = logging.getLogger(__name__)


class AdvisorExecutor(AgentExecutor):
    """
    Minimal ELIS Advisor executor.

    On ``execute``: acknowledges receipt of the incoming message and
    completes the task with a structured text response.

    On ``cancel``: cancels immediately with no side-effects.
    """

    async def execute(
        self,
        context: RequestContext,
        task_updater: TaskUpdater,
    ) -> None:
        """
        Handle an incoming A2A task.  Acknowledge and complete.
        """
        logger.info(
            "AdvisorExecutor.execute called — task_id=%s context_id=%s",
            context.task_id,
            context.context_id,
        )
        task_updater.start_work()

        # Build an acknowledgement Part (text/plain)
        ack_text = (
            "ELIS Advisor: acknowledgement received via A2A channel. "
            "This is a diagnostic response confirming the channel is operational."
        )
        part: Part = ParseDict(
            {"text": ack_text},
            Part(),
        )

        response_message = task_updater.new_agent_message(parts=[part])
        task_updater.complete(message=response_message)
        logger.info(
            "AdvisorExecutor.execute complete — task_id=%s",
            context.task_id,
        )

    async def cancel(
        self,
        context: RequestContext,
        task_updater: TaskUpdater,
    ) -> None:
        """Cancel the task immediately."""
        logger.info(
            "AdvisorExecutor.cancel called — task_id=%s",
            context.task_id,
        )
        task_updater.cancel()
