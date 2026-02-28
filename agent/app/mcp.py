import asyncio
from urllib.parse import urlparse, urlunparse
from typing import Tuple, Optional

from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client


def normalize_mcp_url(url: str) -> str:
    parsed = urlparse(url)
    if not parsed.path or parsed.path == "/":
        parsed = parsed._replace(path="/mcp")
    return urlunparse(parsed)


async def wait_for_tcp(url: str, retries: int, delay: float, logger, name: str):
    parsed = urlparse(url)
    host = parsed.hostname or "localhost"
    port = parsed.port or 80
    last_exc: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            reader, writer = await asyncio.open_connection(host, port)
            writer.close()
            try:
                await writer.wait_closed()
            except Exception:
                pass
            return
        except Exception as exc:
            last_exc = exc
            logger.info(
                "Waiting for MCP agent port",
                extra={
                    "agent": name,
                    "host": host,
                    "port": port,
                    "attempt": attempt,
                    "error": str(exc),
                },
            )
            if attempt < retries:
                await asyncio.sleep(delay)
    raise RuntimeError(
        f"Timed out waiting for {name} MCP agent at {host}:{port}"
    ) from last_exc


async def start_mcp_session(
    url: str, name: str, retries: int, delay: float, logger
) -> Tuple[ClientSession, any]:
    url = normalize_mcp_url(url)
    await wait_for_tcp(url, retries, delay, logger, name)

    last_exc: Exception | None = None
    for attempt in range(1, retries + 1):
        cm = streamable_http_client(url)
        entered = False
        try:
            logger.info(
                "Attempting MCP session initialization",
                extra={"agent": name, "url": url, "attempt": attempt},
            )
            result = await cm.__aenter__()
            entered = True
            read, write = result[0], result[1]
            session = ClientSession(read, write)
            await session.__aenter__()
            await session.initialize()
            logger.info(
                "MCP session initialized successfully",
                extra={"agent": name, "url": url},
            )
            return session, cm
        except Exception as exc:
            last_exc = exc
            logger.warning(
                "MCP connect failed after port was reachable",
                extra={
                    "agent": name,
                    "url": url,
                    "attempt": attempt,
                    "error": str(exc),
                },
            )
            if entered:
                try:
                    await cm.__aexit__(None, None, None)
                except Exception:
                    pass
            if attempt < retries:
                try:
                    await asyncio.sleep(delay)
                except asyncio.CancelledError:
                    logger.warning(
                        "Startup was cancelled while waiting to retry MCP connection",
                        extra={"agent": name},
                    )
                    raise
    raise RuntimeError(f"Failed to connect to {name} MCP agent at {url}") from last_exc


async def register_tools(
    prefix: str,
    session: Optional[ClientSession],
    llm_tools: list,
    tool_routing: dict,
    logger,
):
    if session is None:
        logger.warning(
            "Session not available for tools registration", extra={"prefix": prefix}
        )
        return

    tools_response = await session.list_tools()
    mcp_tools = tools_response.tools
    logger.info("Tools listed", extra={"agent": prefix, "tool_count": len(mcp_tools)})

    for t in mcp_tools:
        logger.info(
            "Tool available",
            extra={
                "agent": prefix,
                "tool_name": t.name,
                "tool_description": t.description,
            },
        )

    for tool in mcp_tools:
        input_schema = tool.inputSchema or {}
        tool_name = f"{prefix}__{tool.name}"
        tool_routing[tool_name] = (session, tool.name)
        llm_tools.append(
            {
                "type": "function",
                "function": {
                    "name": tool_name,
                    "description": tool.description or "",
                    "parameters": {
                        "type": "object",
                        "properties": input_schema.get("properties", {}),
                        "required": input_schema.get("required", []),
                    },
                },
            }
        )
