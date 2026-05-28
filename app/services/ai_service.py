import logging
from typing import AsyncGenerator

from app.agents.agent import get_agent

logger = logging.getLogger(__name__)

async def init_chat(
	user_id: str, chat_id: str,
):
    agent = await get_agent()
    await agent.init_chat(user_id, chat_id)


async def stream_agent_response(
    user_id: str, chat_id: str, user_message: str
) -> AsyncGenerator[str, None]:
    """
    Stream AI response tokens for a single user turn.

    Delegates to the module-level Agent singleton which holds a PostgreSQL-backed
    checkpointer.  Conversation history is persisted per thread_id = "{user_id}-{chat_id}".
    """
    agent = await get_agent()
    async for chunk in agent.invoke(user_id, chat_id, user_message):
        yield chunk
