import logging
import logging.config
import os

from fastmcp import FastMCP

from .db import init_db
from .tools import register_tools

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOGGING_CONF = os.path.join(BASE_DIR, "logging.conf")

if os.path.exists(LOGGING_CONF):
    logging.config.fileConfig(LOGGING_CONF)
else:
    logging.basicConfig(level=logging.INFO)

logger = logging.getLogger("server")

mcp = FastMCP(name="Travel Demo MCP Server")
register_tools(mcp)


def main() -> None:
    logger.info("Initializing database")
    init_db()
    logger.info("Starting Travel MCP Server (stdio)")
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
