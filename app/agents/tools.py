import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

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