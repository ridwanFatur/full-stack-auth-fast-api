import json
import logging
from typing import Annotated, Any, Sequence

from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    SystemMessage,
    ToolMessage,
)
from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict

from .llm import get_llm
from .prompts import SYSTEM_PROMPT

logger = logging.getLogger(__name__)

# Maximum number of tool-call rounds before forcing a plain-text reply
MAX_TOOL_ROUNDS = 5

class UserState(TypedDict):
    """
    Per-request conversation state.

    messages    — full message history; add_messages reducer *appends*.
    tool_rounds — counts how many tool-execution cycles have happened
                  this request; reset per invocation via the initial state.
    """
    messages: Annotated[Sequence[BaseMessage], add_messages]
    tool_rounds: int
    
def create_graph(tools: list, checkpointer: Any):
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

        # Prepend system prompt for every LLM call (not stored in checkpointed state)
        if not messages or not isinstance(messages[0], SystemMessage):
            messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages

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
        
    langgraph_app = builder.compile(
		checkpointer=checkpointer
	)
    
    return langgraph_app

    