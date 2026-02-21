import asyncio
import json
import logging
import logging.config
import os
from typing import Optional

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp import types  # noqa: F401
from openai import AsyncOpenAI


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOGGING_CONF = os.path.join(BASE_DIR, "logging.conf")

if os.path.exists(LOGGING_CONF):
    logging.config.fileConfig(LOGGING_CONF)
else:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
    )

logger = logging.getLogger("agent")

SERVER_IMAGE = os.getenv("SERVER_IMAGE", "travel-mcp-server:latest")

RESERVED_LOG_ATTRS = {
    "name", "msg", "args", "created", "filename", "funcName", "levelname", 
    "levelno", "lineno", "module", "pathname", "process", "processName",
    "relativeCreated", "thread", "threadName", "exc_info", "exc_text",
    "stack_info", "getMessage", "message", "asctime", "msecs"
}


def safe_log_extra(data: dict) -> dict:
    if not data:
        return data
    safe_data = {}
    for key, value in data.items():
        if key in RESERVED_LOG_ATTRS:
            safe_data[f"data_{key}"] = value
        else:
            safe_data[key] = value
    return safe_data


async def run_agent_flow():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set")

    client = AsyncOpenAI(api_key=api_key)
    model = os.getenv("LLM_MODEL", "gpt-4o")

    logger.info("Starting LLM-based agent", extra={"model": model})
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
            tools_response = await session.list_tools()
            mcp_tools = tools_response.tools
            logger.info("Tools listed", extra={"tool_count": len(mcp_tools)})

            for t in mcp_tools:
                logger.info(
                    "Tool available",
                    extra={"tool_name": t.name, "tool_description": t.description},
                )

            # Convert MCP tools → OpenAI tools format
            llm_tools = []
            for tool in mcp_tools:
                input_schema = tool.inputSchema or {}
                llm_tools.append(
                    {
                        "type": "function",
                        "function": {
                            "name": tool.name,
                            "description": tool.description or "",
                            "parameters": {
                                "type": "object",
                                "properties": input_schema.get("properties", {}),
                                "required": input_schema.get("required", []),
                            },
                        },
                    }
                )

            logger.info(
                "Converted tools for LLM",
                extra={"tool_count": len(llm_tools)},
            )

            system_prompt = """You are a travel booking assistant. Your goal is to help customers book travel tours.
You have access to tools to:
1. Look up customer information by phone number
2. Search for available tours based on destination and budget
3. Book a tour for a customer

Be proactive and ask for information if needed. Use the tools strategically to complete the booking process.
When you have enough information and have successfully booked a tour, conclude the conversation.
"""

            user_request = (
                "I want to book a travel tour. My phone number is +919999999999. "
                "I'm interested in Goa with a budget of 40000."
            )
            logger.info(
                "Starting agent conversation",
                extra={"user_request": user_request},
            )

            conversation_history: list[dict] = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_request},
            ]

            max_iterations = 20
            iteration = 0

            while iteration < max_iterations:
                iteration += 1
                logger.info("Agent iteration", extra={"iteration": iteration})

                response = await client.chat.completions.create(
                    model=model,
                    messages=conversation_history,
                    tools=llm_tools,
                    tool_choice="auto",
                )

                choice = response.choices[0]
                assistant_message = choice.message

                logger.info(
                    "LLM response received",
                    extra={
                        "stop_reason": choice.finish_reason,
                        "tool_calls_count": len(assistant_message.tool_calls or []),
                    },
                )

                # --- THE FIX IS HERE ---
                # Append assistant message to history, ensuring content is a string
                assistant_msg = {
                    "role": "assistant",
                    "content": assistant_message.content or "", 
                }
                
                # We MUST include the tool_calls in the history so OpenAI can match 
                # them with the tool results we are about to send.
                if assistant_message.tool_calls:
                    assistant_msg["tool_calls"] = [
                        {
                            "id": tc.id,
                            "type": tc.type,
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments
                            }
                        }
                        for tc in assistant_message.tool_calls
                    ]

                conversation_history.append(assistant_msg)
                # -----------------------

                # If LLM wants to call tools
                if assistant_message.tool_calls:
                    tool_results_messages: list[dict] = []

                    for tool_call in assistant_message.tool_calls:
                        tool_name = tool_call.function.name
                        tool_args = json.loads(tool_call.function.arguments or "{}")

                        logger.info(
                            "Calling tool via MCP",
                            extra={
                                "tool_name": tool_name,
                                "tool_args": safe_log_extra(tool_args),
                            },
                        )

                        mcp_result = await session.call_tool(
                            tool_name, arguments=tool_args
                        )
                        result_data = json.loads(mcp_result.content[0].text)

                        logger.info(
                            "Tool result received",
                            extra={
                                "tool_name": tool_name,
                                "result_keys": list(result_data.keys()),
                            },
                        )

                        # Add as tool message for the LLM to read
                        tool_results_messages.append(
                            {
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "name": tool_name,
                                "content": json.dumps(result_data),
                            }
                        )

                    # Feed tool results back into LLM
                    conversation_history.extend(tool_results_messages)
                    continue  # next iteration

                # No tool calls -> LLM is giving final answer
                logger.info(
                    "Agent completed reasoning",
                    extra={
                        "final_message": (
                            assistant_message.content[:200]
                            if assistant_message.content
                            else "No content"
                        )
                    },
                )
                logger.info("Agent flow completed")
                break

            if iteration >= max_iterations:
                logger.warning(
                    "Agent reached max iterations without completing",
                    extra={"max_iterations": max_iterations},
                )


def main():
    logger.info("Starting agent")
    asyncio.run(run_agent_flow())
    logger.info("Agent finished")


if __name__ == "__main__":
    main()
