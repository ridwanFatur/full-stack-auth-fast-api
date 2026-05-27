"""
AI Service — LangGraph ReAct agent with optional MCP tool integration.

Architecture:
  - LLM: Groq (llama-3.3-70b-versatile) via OpenAI-compatible API
  - Agent: LangGraph ReAct agent (create_react_agent)
  - Tools: Loaded from FastMCP server via langchain-mcp-adapters (optional)
  - Streaming: astream_events v2 → yields token chunks
"""

import asyncio
import logging
from typing import AsyncGenerator, Sequence

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from app.core.config import settings

logger = logging.getLogger(__name__)

# ------------------------------------------------------------------ #
#  LLM singleton                                                        #
# ------------------------------------------------------------------ #

_llm: ChatOpenAI | None = None


def get_llm() -> ChatOpenAI:
    global _llm
    if _llm is None:
        _llm = ChatOpenAI(
            openai_api_base="https://api.groq.com/openai/v1",
            openai_api_key=settings.GROQ_API_KEY,
            temperature=0,
            model_name="llama-3.3-70b-versatile",
            top_p=1,
            max_retries=3,
            request_timeout=60,
        )
    return _llm


# ------------------------------------------------------------------ #
#  System prompt                                                        #
# ------------------------------------------------------------------ #

SYSTEM_PROMPT = """You are an intelligent HR Assistant for the HR Manager application.
You help users manage companies, employees, and HR data (attendance, leave, payroll, performance).

When you have access to database tools, you can query the database to provide accurate,
real-time information. Always use these tools to answer data-related questions.

Guidelines:
- Be concise and professional
- For data questions, always check the database first
- Format tables and lists clearly using markdown
- If you're unsure about something, say so honestly
- Help users understand their HR data and make informed decisions
"""


# ------------------------------------------------------------------ #
#  Build LangChain message history                                      #
# ------------------------------------------------------------------ #

def build_messages(
    history: Sequence[tuple[str, str]],
    user_message: str,
) -> list[BaseMessage]:
    """
    Convert [(role, content), ...] history + new user message to LangChain messages.
    history entries have role "user" or "assistant".
    """
    msgs: list[BaseMessage] = [SystemMessage(content=SYSTEM_PROMPT)]
    for role, content in history:
        if role == "user":
            msgs.append(HumanMessage(content=content))
        else:
            msgs.append(AIMessage(content=content))
    msgs.append(HumanMessage(content=user_message))
    return msgs


# ------------------------------------------------------------------ #
#  Load MCP tools (optional)                                            #
# ------------------------------------------------------------------ #

async def load_mcp_tools() -> list:
    """
    Try to load tools from the MCP server.
    Returns an empty list if the server is not reachable.
    """
    if not settings.MCP_SERVER_URL:
        return []

    try:
        from langchain_mcp_adapters.client import MultiServerMCPClient

        async with MultiServerMCPClient(
            {
                "hr-database": {
                    "url": f"{settings.MCP_SERVER_URL}/sse",
                    "transport": "sse",
                }
            }
        ) as client:
            tools = client.get_tools()
            logger.info("Loaded %d tools from MCP server", len(tools))
            return tools
    except ImportError:
        logger.warning(
            "langchain-mcp-adapters not installed; running without MCP tools"
        )
        return []
    except Exception as exc:
        logger.warning("MCP server not reachable (%s); running without tools", exc)
        return []


# ------------------------------------------------------------------ #
#  Streaming agent invocation                                           #
# ------------------------------------------------------------------ #

async def stream_agent_response(
    history: Sequence[tuple[str, str]],
    user_message: str,
) -> AsyncGenerator[str, None]:
    """
    Run the LangGraph ReAct agent and yield token chunks as they arrive.

    Each yielded string is a partial token string. The caller accumulates
    them to build the full assistant response.
    """
    from langgraph.prebuilt import create_react_agent

    llm = get_llm()
    tools = await load_mcp_tools()

    # Build LangGraph agent with (optional) MCP tools
    agent = create_react_agent(llm, tools)

    messages = build_messages(history, user_message)
    input_state = {"messages": messages}

    full_response = ""

    try:
        async for event in agent.astream_events(input_state, version="v2"):
            kind = event.get("event")
            if kind == "on_chat_model_stream":
                chunk = event.get("data", {}).get("chunk")
                if chunk and hasattr(chunk, "content") and chunk.content:
                    token = chunk.content
                    if isinstance(token, str):
                        full_response += token
                        yield token
                    elif isinstance(token, list):
                        # Handle list-type content blocks
                        for block in token:
                            if isinstance(block, dict):
                                text = block.get("text", "")
                                if text:
                                    full_response += text
                                    yield text
    except Exception as exc:
        logger.error("Agent streaming error: %s", exc, exc_info=True)
        error_msg = f"\n\n[Error: {exc}]"
        yield error_msg


async def get_agent_response(
    history: Sequence[tuple[str, str]],
    user_message: str,
) -> str:
    """
    Non-streaming version — accumulates the full response and returns it.
    Useful for testing.
    """
    chunks = []
    async for chunk in stream_agent_response(history, user_message):
        chunks.append(chunk)
    return "".join(chunks)
