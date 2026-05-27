"""
AI Service — Manual LangGraph workflow (no prebuilt agents).

Graph topology
--------------
START → model_node
model_node ──(has tool calls?)──→ tool_node → model_node   (loop, max 5 tool rounds)
           └──(no tool calls)──→ END

Key design decision — two-mode model node
------------------------------------------
When the previous step produced ToolMessages (we just executed tools), the
model is invoked WITHOUT tool binding.  This forces it to synthesise the
tool results into a plain-text answer and breaks the tool-call loop that
llama-3.3-70b-versatile otherwise falls into.

When no tool results are present the model is invoked WITH tool binding so
it can still decide to call tools.

Streaming
---------
astream_events v2, filtered to on_chat_model_stream from "model" node only.
Tool-call-generation chunks (partial JSON) are suppressed — only final
answer text tokens are yielded.
"""

import json
import logging
from typing import Annotated, AsyncGenerator, Sequence

from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict

from app.core.config import settings

logger = logging.getLogger(__name__)

# Maximum number of tool-call rounds before forcing a plain-text reply
MAX_TOOL_ROUNDS = 5


# ════════════════════════════════════════════════════════════════════
# 1.  STATE
# ════════════════════════════════════════════════════════════════════

class UserState(TypedDict):
    """
    Per-request conversation state.

    messages    — full message history; add_messages reducer *appends*.
    tool_rounds — counts how many tool-execution cycles have happened
                  this request; reset per invocation via the initial state.
    """
    messages: Annotated[Sequence[BaseMessage], add_messages]
    tool_rounds: int


# ════════════════════════════════════════════════════════════════════
# 2.  LLM SINGLETON
# ════════════════════════════════════════════════════════════════════

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


# ════════════════════════════════════════════════════════════════════
# 3.  SYSTEM PROMPT
# ════════════════════════════════════════════════════════════════════

SYSTEM_PROMPT = """You are an intelligent HR Assistant for the HR Manager application.
You help users manage companies, employees, and HR data (attendance, leave, payroll,
performance evaluations).

When you have access to database tools, query the database to provide accurate,
real-time information.  Always prefer tools over guessing.

After you receive tool results, ALWAYS summarise those results in a helpful
plain-text (or markdown) response.  Do NOT call the same tool again if you
already have its results.

Guidelines:
- Be concise and professional.
- Use markdown tables and lists where helpful.
- If a question requires database data, call a tool first.
- If you are unsure, say so honestly.
"""


# ════════════════════════════════════════════════════════════════════
# 4.  MESSAGE BUILDER
# ════════════════════════════════════════════════════════════════════

def build_messages(
    history: Sequence[tuple[str, str]],
    user_message: str,
) -> list[BaseMessage]:
    """
    Convert stored (role, content) history + new user message to a
    LangChain message list, prepended with the system prompt.
    """
    msgs: list[BaseMessage] = [SystemMessage(content=SYSTEM_PROMPT)]
    for role, content in history:
        if role == "user":
            msgs.append(HumanMessage(content=content))
        else:
            msgs.append(AIMessage(content=content))
    msgs.append(HumanMessage(content=user_message))
    return msgs


# ════════════════════════════════════════════════════════════════════
# 5.  MCP TOOL LOADER
# ════════════════════════════════════════════════════════════════════

async def load_mcp_tools() -> list:
    """
    Fetch tools from the running FastMCP server.
    Returns [] if the server is unreachable or the adapter is not installed.
    """
    if not settings.MCP_SERVER_URL:
        return []

    try:
        from langchain_mcp_adapters.client import MultiServerMCPClient  # type: ignore

        client = MultiServerMCPClient(
            {
                "hr-database": {
                    "url": f"{settings.MCP_SERVER_URL}/sse",
                    "transport": "sse",
                }
            }
        )
        tools = await client.get_tools()
        logger.info("Loaded %d MCP tools from %s", len(tools), settings.MCP_SERVER_URL)
        return tools
    except ImportError:
        logger.warning("langchain-mcp-adapters not installed; no MCP tools")
        return []
    except Exception as exc:
        logger.warning("MCP server unreachable (%s); continuing without tools", exc)
        return []


# ════════════════════════════════════════════════════════════════════
# 6.  GRAPH BUILDER
# ════════════════════════════════════════════════════════════════════

def _build_graph(tools: list):
    """
    Assemble the LangGraph StateGraph manually.

    Nodes
    -----
    model  — invokes the LLM in either tool-enabled or plain mode
    tools  — executes every tool call in the last AIMessage

    Edges
    -----
    START → model
    model → tools   (conditional: last message has tool_calls AND tool_rounds < MAX)
    model → END     (conditional: no tool calls, or max rounds reached)
    tools → model   (always — loop back for the synthesised answer)
    """
    llm = get_llm()
    model_with_tools = llm.bind_tools(tools) if tools else llm
    tools_by_name: dict = {t.name: t for t in tools}

    # ── Node: model ──────────────────────────────────────────────────
    async def model_node(state: UserState, config: RunnableConfig) -> dict:
        """
        Invoke the LLM.

        Mode selection:
        • If the last message is a ToolMessage → the previous step ran tools;
          call the LLM WITHOUT tool binding to force a plain-text synthesis.
        • Otherwise → call with tools bound so the model can decide to use them.

        This two-mode approach prevents the infinite tool-call loop that
        llama-3.3-70b-versatile falls into when receiving tool results.
        """
        messages = list(state["messages"])
        last_is_tool_result = messages and isinstance(messages[-1], ToolMessage)

        if last_is_tool_result or state["tool_rounds"] >= MAX_TOOL_ROUNDS:
            # Synthesis mode: no more tool calls allowed
            response: AIMessage = await llm.ainvoke(messages, config)
        else:
            # Reasoning mode: model may call tools
            response = await model_with_tools.ainvoke(messages, config)

        return {"messages": [response]}

    # ── Node: tools ──────────────────────────────────────────────────
    async def tool_node(state: UserState, config: RunnableConfig) -> dict:
        """
        Execute every tool call from the latest AIMessage and return
        ToolMessages so the model can incorporate the results.
        """
        last_msg: AIMessage = state["messages"][-1]  # type: ignore[assignment]
        tool_results: list[ToolMessage] = []

        for call in last_msg.tool_calls:
            name = call["name"]
            args = call["args"]
            call_id = call["id"]

            tool = tools_by_name.get(name)
            if tool is None:
                content = f"[Error] Unknown tool: {name!r}"
            else:
                try:
                    raw = await tool.ainvoke(args, config)
                    content = (
                        raw if isinstance(raw, str)
                        else json.dumps(raw, default=str)
                    )
                except Exception as exc:
                    logger.warning("Tool %r raised: %s", name, exc)
                    content = f"[Tool error] {exc}"

            tool_results.append(
                ToolMessage(content=content, tool_call_id=call_id, name=name)
            )

        return {
            "messages": tool_results,
            "tool_rounds": state["tool_rounds"] + 1,
        }

    # ── Routing logic ────────────────────────────────────────────────
    def should_continue(state: UserState) -> str:
        """
        Route to 'tools' only if:
          - the last AIMessage contains tool calls, AND
          - we have not yet hit the MAX_TOOL_ROUNDS limit.
        Otherwise end the graph.
        """
        last = state["messages"][-1]
        if (
            isinstance(last, AIMessage)
            and getattr(last, "tool_calls", None)
            and state["tool_rounds"] < MAX_TOOL_ROUNDS
        ):
            return "tools"
        return "end"

    # ── Graph assembly ───────────────────────────────────────────────
    builder = StateGraph(UserState)
    builder.add_node("model", model_node)

    if tools:
        builder.add_node("tools", tool_node)
        builder.add_edge(START, "model")
        builder.add_conditional_edges(
            "model",
            should_continue,
            {"tools": "tools", "end": END},
        )
        # After tool execution, always return to model for the final answer
        builder.add_edge("tools", "model")
    else:
        builder.add_edge(START, "model")
        builder.add_edge("model", END)

    return builder.compile()


# ════════════════════════════════════════════════════════════════════
# 7.  STREAMING HELPERS
# ════════════════════════════════════════════════════════════════════

def _extract_text(chunk: AIMessage) -> str:
    """
    Pull plain text from an AIMessage chunk.
    Suppress tool-call-generation fragments (partial JSON).
    """
    if getattr(chunk, "tool_call_chunks", None):
        return ""
    content = getattr(chunk, "content", "")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "".join(
            block.get("text", "")
            for block in content
            if isinstance(block, dict)
        )
    return ""


async def _stream_graph(graph, initial_state: UserState) -> AsyncGenerator[str, None]:
    """
    Stream token chunks from the compiled graph via astream_events v2.

    Only on_chat_model_stream events from the "model" node are forwarded;
    everything else (tool execution, routing) is silent.
    """
    async for event in graph.astream_events(initial_state, version="v2"):
        if event.get("event") != "on_chat_model_stream":
            continue
        if event.get("metadata", {}).get("langgraph_node") != "model":
            continue

        chunk = event.get("data", {}).get("chunk")
        if chunk is None:
            continue

        token = _extract_text(chunk)
        if token:
            yield token


# ════════════════════════════════════════════════════════════════════
# 8.  PUBLIC ENTRY POINTS
# ════════════════════════════════════════════════════════════════════

async def stream_agent_response(
    history: Sequence[tuple[str, str]],
    user_message: str,
) -> AsyncGenerator[str, None]:
    """
    Main public entry point.

    Builds the graph, feeds it the conversation history + new message,
    and yields token chunks as they arrive from the LLM.

    Falls back to a tool-less graph if the primary graph fails.
    """
    messages = build_messages(history, user_message)
    tools = await load_mcp_tools()

    graph = _build_graph(tools)
    initial_state: UserState = {"messages": messages, "tool_rounds": 0}

    try:
        got_any = False
        async for token in _stream_graph(graph, initial_state):
            got_any = True
            yield token

        if not got_any and tools:
            # Graph ran (possibly tool calls happened) but no text was streamed.
            # Retry without tools so the user always gets a response.
            logger.warning("Graph produced no text; retrying without tools")
            fallback = _build_graph([])
            async for token in _stream_graph(
                fallback, {"messages": messages, "tool_rounds": 0}
            ):
                yield token

    except Exception as exc:
        logger.error(
            "Graph streaming failed (%s); falling back to no-tool graph",
            exc,
            exc_info=True,
        )
        try:
            fallback = _build_graph([])
            async for token in _stream_graph(
                fallback, {"messages": messages, "tool_rounds": 0}
            ):
                yield token
        except Exception as inner:
            logger.error("Fallback graph also failed: %s", inner)
            yield f"\n\n[Assistant error: {exc}]"


async def get_agent_response(
    history: Sequence[tuple[str, str]],
    user_message: str,
) -> str:
    """Non-streaming helper — returns the full accumulated response."""
    parts: list[str] = []
    async for token in stream_agent_response(history, user_message):
        parts.append(token)
    return "".join(parts)
