import asyncio
import logging
from typing import AsyncGenerator, Optional

from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.postgres import PostgresSaver
from psycopg_pool import ConnectionPool

from app.agents.react_graph import create_graph
from app.agents.tools import load_mcp_tools
from app.core.config import settings

logger = logging.getLogger(__name__)

_agent: Optional["Agent"] = None
_lock = asyncio.Lock()


class Agent:
    def __init__(self, checkpointer: MemorySaver, app) -> None:
        self._checkpointer = checkpointer
        self._app = app

    @classmethod
    async def create(cls) -> "Agent":
        conn_str = settings.DATABASE_URL.replace(
            "postgresql+asyncpg://", "postgresql://")

        loop = asyncio.get_event_loop()
        pool = ConnectionPool(conninfo=conn_str, open=False)
        await loop.run_in_executor(None, pool.open)

        checkpointer = PostgresSaver(pool)
        await loop.run_in_executor(None, checkpointer.setup)

        tools = await load_mcp_tools()
        app = create_graph(
            tools=tools,
            checkpointer=checkpointer
        )

        logger.info("Agent initialised with %d MCP tool(s)", len(tools))
        return cls(checkpointer, app)

    def get_config(self, user_id: str, chat_id: str):
        config = {
            "configurable": {
                "thread_id": f"{user_id}-{chat_id}",
                "checkpoint_ns": ""
            }
        }
        return config

    async def init_chat(self, user_id: str, chat_id: str):
        config = self.get_config(user_id, chat_id)
        self._app.update_state(config, {"messages": [], "tool_rounds": 0})

    async def invoke(
        self, user_id: str, chat_id: str, user_message: Optional[str]
    ):
        """Keep using invoke instead of astream"""
        config = self.get_config(user_id, chat_id)

        if user_message:
            user_query = [HumanMessage(content=user_message)]
            app_input = {"messages": user_query}
        else:
            app_input = None

        final_state = await self._app.ainvoke(
            app_input,
            config=config,
        )
        messages = final_state["messages"]
        last_message = messages[-1]
        output = last_message.content
        yield output


async def get_agent() -> Agent:
    """Return the module-level Agent singleton, creating it on first call."""
    global _agent
    if _agent is None:
        async with _lock:
            if _agent is None:
                _agent = await Agent.create()
    return _agent
