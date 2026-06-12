"""
ELIS Advisor — Agent Executor.

Implements the AgentExecutor ABC from the official a2a-sdk.

Official SDK pattern (a2a-sdk 1.1.0):
  - ``execute(self, context, event_queue)`` — second arg is ``EventQueue``,
    NOT a ``TaskUpdater``.  The framework (``LegacyRequestHandler``) passes the
    raw queue; the executor is responsible for constructing a ``TaskUpdater``
    itself if it wants the convenience wrapper.
  - For a new request, ``context.current_task`` is ``None``.
    ``context.task_id`` and ``context.context_id`` are always populated by
    ``RequestContext.__init__`` (generated if absent).
  - The executor must enqueue a ``Task`` proto first (Task-first protocol path),
    then use ``TaskUpdater`` for lifecycle updates.

No external service calls, no governance actions, no production work.
"""

import logging

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events.event_queue import EventQueue
from a2a.server.tasks.task_updater import TaskUpdater
from a2a.types import Part, Task, TaskState, TaskStatus
from a2a.utils.proto_utils import ParseDict

logger = logging.getLogger(__name__)


class AdvisorExecutor(AgentExecutor):
    """
    ELIS Advisor executor — official SDK pattern.

    On ``execute``:
      1. Retrieve ``context.current_task`` (``None`` for a fresh request).
      2. If no task exists, create one from ``context.task_id`` /
         ``context.context_id`` and enqueue it on ``event_queue``.
      3. Construct ``TaskUpdater(event_queue, task_id, context_id)``.
      4. Use ``TaskUpdater`` for all lifecycle updates.

    On ``cancel``: cancels immediately with no side-effects.
    """

    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        """
        Handle an incoming A2A task using the official SDK event-queue pattern.
        """
        # Step 1 — retrieve IDs; always populated by RequestContext.__init__
        task_id: str = context.task_id  # type: ignore[assignment]
        context_id: str = context.context_id  # type: ignore[assignment]

        logger.info(
            "AdvisorExecutor.execute called — task_id=%s context_id=%s",
            task_id,
            context_id,
        )

        # Step 2 — Task-first: enqueue a Task proto if no existing task
        task = context.current_task
        if task is None:
            task = ParseDict(
                {
                    "id": task_id,
                    "context_id": context_id,
                    "status": {
                        "state": TaskState.Value("TASK_STATE_SUBMITTED"),
                    },
                },
                Task(),
            )
            await event_queue.enqueue_event(task)
            logger.debug("AdvisorExecutor: enqueued new Task id=%s", task_id)

        # Step 3 — construct TaskUpdater as a convenience wrapper
        task_updater = TaskUpdater(event_queue, task_id, context_id)

        # Step 4 — lifecycle: working → complete with acknowledgement
        await task_updater.start_work()

        ack_text = (
            "ELIS Advisor: acknowledgement received via A2A channel. "
            "This is a diagnostic response confirming the channel is operational."
        )
        part: Part = ParseDict({"text": ack_text}, Part())
        response_message = task_updater.new_agent_message(parts=[part])
        await task_updater.complete(message=response_message)

        logger.info(
            "AdvisorExecutor.execute complete — task_id=%s",
            task_id,
        )

    async def cancel(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        """Cancel the task immediately."""
        task_id: str = context.task_id  # type: ignore[assignment]
        context_id: str = context.context_id  # type: ignore[assignment]
        logger.info(
            "AdvisorExecutor.cancel called — task_id=%s",
            task_id,
        )
        task_updater = TaskUpdater(event_queue, task_id, context_id)
        await task_updater.cancel()
