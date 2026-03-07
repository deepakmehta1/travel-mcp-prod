import logging
import logging.config
import os

from fastmcp import FastMCP

from tools import register_tools

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOGGING_CONF = os.path.join(BASE_DIR, "logging.conf")

if os.path.exists(LOGGING_CONF):
    logging.config.fileConfig(LOGGING_CONF)
else:
    logging.basicConfig(level=logging.INFO)

logger = logging.getLogger("admin-server")

mcp = FastMCP(name="Admin Server MCP")


def main() -> None:
    """Main entry point for the admin MCP server"""
    
    # Register all admin tools
    register_tools(mcp)
    
    transport = os.getenv("MCP_TRANSPORT", "stdio")
    host = os.getenv("MCP_HOST", "0.0.0.0")
    port = int(os.getenv("MCP_PORT", "9003"))

    if transport == "streamable-http":
        logger.info(
            "Starting Admin MCP Server",
            extra={"host": host, "port": port, "transport": "streamable-http"},
        )
        mcp.run(transport="streamable-http", host=host, port=port)
    else:
        logger.info("Starting Admin MCP Server (stdio mode)")
        mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
