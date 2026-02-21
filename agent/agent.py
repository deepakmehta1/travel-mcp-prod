import asyncio
import json
import logging
import logging.config
import os
import shlex
import subprocess
from typing import Optional

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp import types  # noqa: F401

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOGGING_CONF = os.path.join(BASE_DIR, "logging.conf")

if os.path.exists(LOGGING_CONF):
    logging.config.fileConfig(LOGGING_CONF)
else:
    logging.basicConfig(level=logging.INFO)

logger = logging.getLogger("agent")

# Name of the built server image (see docker-compose.yml)
SERVER_IMAGE = os.getenv("SERVER_IMAGE", "travel-mcp-server:latest")

# Reserved LogRecord attribute names that cannot be used as extra field keys
RESERVED_LOG_ATTRS = {
    "name", "msg", "args", "created", "filename", "funcName", "levelname", 
    "levelno", "lineno", "module", "pathname", "process", "processName",
    "relativeCreated", "thread", "threadName", "exc_info", "exc_text",
    "stack_info", "getMessage", "message", "asctime", "msecs"
}

def safe_log_extra(data: dict) -> dict:
    """Rename LogRecord reserved attributes in extra dict to avoid conflicts."""
    if not data:
        return data
    
    safe_data = {}
    for key, value in data.items():
        if key in RESERVED_LOG_ATTRS:
            # Prefix with 'data_' to avoid conflicts
            safe_data[f"data_{key}"] = value
        else:
            safe_data[key] = value
    return safe_data


async def run_agent_flow():
    # We will use docker to launch the server image with stdio (-i) as recommended.[web:82][web:90]
    logger.info("Starting server container via docker run", extra={"image": SERVER_IMAGE})

    server_params = StdioServerParameters(
        command="docker",
        args=[
            "run",
            "-i",
            "--rm",
            SERVER_IMAGE,
        ],
        env=None,
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            logger.info("Tools listed", extra={"tool_count": len(tools.tools)})

            for t in tools.tools:
                logger.info("Tool available", extra={"tool_name": t.name, "tool_description": t.description})

            # 1. lookupCustomerByPhone
            phone = "+919999999999"
            logger.info("Calling lookupCustomerByPhone", extra={"phone": phone})
            result = await session.call_tool(
                "lookupCustomerByPhone",
                arguments={"phone": phone},
            )
            data = json.loads(result.content[0].text)
            logger.info("lookupCustomerByPhone result", extra=safe_log_extra(data))

            if not data.get("found"):
                logger.warning("Customer not found, stopping flow", extra={"phone": phone})
                return
            customer = data["customer"]

            # 2. searchTours
            logger.info("Calling searchTours", extra={"destination": "Goa", "budget": 40000})
            result = await session.call_tool(
                "searchTours",
                arguments={"destination": "Goa", "budget": 40000},
            )
            tours = json.loads(result.content[0].text)["tours"]
            logger.info("searchTours result", extra=safe_log_extra({"tour_count": len(tours)}))

            if not tours:
                logger.warning("No tours found under budget, stopping flow")
                return

            chosen = tours[0]
            logger.info("Chosen tour", extra=safe_log_extra(chosen))

            # 3. bookTour
            logger.info(
                "Calling bookTour",
                extra={
                    "customer_id": customer["id"],
                    "tour_code": chosen["code"],
                    "start_date": "2026-03-10",
                    "end_date": "2026-03-15",
                },
            )
            result = await session.call_tool(
                "bookTour",
                arguments={
                    "customer_id": customer["id"],
                    "tour_code": chosen["code"],
                    "start_date": "2026-03-10",
                    "end_date": "2026-03-15",
                },
            )
            booking_resp = json.loads(result.content[0].text)
            logger.info("bookTour result", extra=safe_log_extra(booking_resp))

            logger.info("Agent flow completed")


def main():
    logger.info("Starting agent")
    asyncio.run(run_agent_flow())
    logger.info("Agent finished")


if __name__ == "__main__":
    main()
