"""A2A AgentExecutor that runs an async callback and returns a text artifact."""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.types import Part, TextPart
from a2a.utils.message import new_agent_text_message

logger = logging.getLogger(__name__)

RunFn = Callable[[str], Awaitable[str]]


class CallbackAgentExecutor(AgentExecutor):
    """Executes `run(user_text) -> str` and publishes a single text artifact."""

    def __init__(self, run: RunFn) -> None:
        self._run = run

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        user_text = context.get_user_input()
        tid = context.task_id or ""
        cid = context.context_id or ""
        updater = TaskUpdater(event_queue, tid, cid)
        await updater.start_work()
        try:
            result_text = await self._run(user_text)
            await updater.add_artifact(
                parts=[Part(root=TextPart(text=result_text))],
                name="agent_result",
                last_chunk=True,
            )
            await updater.complete(
                message=new_agent_text_message(
                    f"Completed. Result length: {len(result_text)} chars.",
                    context_id=context.context_id,
                    task_id=context.task_id,
                )
            )
        except Exception:
            logger.exception("Agent execution failed")
            await updater.failed(
                message=new_agent_text_message(
                    "Agent failed — see server logs.",
                    context_id=context.context_id,
                    task_id=context.task_id,
                )
            )

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        tid = context.task_id or ""
        cid = context.context_id or ""
        updater = TaskUpdater(event_queue, tid, cid)
        await updater.cancel()
