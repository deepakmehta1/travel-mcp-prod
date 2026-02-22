import asyncio
import json
import logging
import logging.config
import os
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

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


# Pydantic models for request/response
class QueryRequest(BaseModel):
    query: str


class QueryResponse(BaseModel):
    success: bool
    response: str
    error: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    model: str


# Global state for session
_session: Optional[ClientSession] = None
_client: Optional[AsyncOpenAI] = None
_llm_tools: list = []
_stdio_client_cm = None  # Keep the context manager alive
_conversation_history: list[dict] = []  # Persistent conversation history


async def initialize_session():
    """Initialize MCP session and OpenAI client on startup"""
    global _session, _client, _llm_tools, _stdio_client_cm, _conversation_history
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set")

    _client = AsyncOpenAI(api_key=api_key)
    model = os.getenv("LLM_MODEL", "gpt-4o")

    logger.info("Starting LLM-based agent", extra={"model": model})
    logger.info("Starting server container via docker run", extra={"image": SERVER_IMAGE})

    server_env = {}
    for key in (
        "DATABASE_URL",
        "PGHOST",
        "PGPORT",
        "PGUSER",
        "PGPASSWORD",
        "PGDATABASE",
    ):
        value = os.getenv(key)
        if value:
            server_env[key] = value

    docker_args = ["run", "-i", "--rm"]
    network_name = os.getenv("MCP_SERVER_DOCKER_NETWORK")
    if network_name:
        docker_args += ["--network", network_name]

    for key, value in server_env.items():
        docker_args += ["-e", f"{key}={value}"]

    docker_args.append(SERVER_IMAGE)

    server_params = StdioServerParameters(
        command="docker",
        args=docker_args,
        env=None,
    )

    # Properly manage context managers
    _stdio_client_cm = stdio_client(server_params)
    read, write = await _stdio_client_cm.__aenter__()
    
    _session = ClientSession(read, write)
    await _session.__aenter__()
    
    await _session.initialize()
    tools_response = await _session.list_tools()
    mcp_tools = tools_response.tools
    logger.info("Tools listed", extra={"tool_count": len(mcp_tools)})

    for t in mcp_tools:
        logger.info(
            "Tool available",
            extra={"tool_name": t.name, "tool_description": t.description},
        )

    # Convert MCP tools → OpenAI tools format
    _llm_tools = []
    for tool in mcp_tools:
        input_schema = tool.inputSchema or {}
        _llm_tools.append(
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
        extra={"tool_count": len(_llm_tools)},
    )
    
    # Initialize conversation with system prompt
    _conversation_history.clear()
    _conversation_history.append({
        "role": "system",
        "content": """You are a travel booking assistant and customer executive. Your goal is to help customers book travel tours.
You have access to tools to:
1. Look up customer information by phone number
2. Search for available tours based on destination and budget
3. Book a tour for a customer

Be proactive, professional, and ask for information if needed. Use the tools strategically to complete the booking process.
Always be polite and provide clear summaries of actions taken. Remember all details provided by the customer in this conversation."""
    })



async def process_query(user_query: str) -> str:
    """Process a user query through the agent"""
    global _session, _client, _llm_tools, _conversation_history
    
    if not _session or not _client or not _llm_tools:
        raise RuntimeError("Agent not initialized")
    
    model = os.getenv("LLM_MODEL", "gpt-4o")
    
    logger.info(
        "Processing user query",
        extra={"user_request": user_query, "conversation_turn": len(_conversation_history)},
    )

    # Append user message to persistent conversation history
    _conversation_history.append({"role": "user", "content": user_query})

    max_iterations = 20
    iteration = 0

    while iteration < max_iterations:
        iteration += 1
        logger.info("Agent iteration", extra={"iteration": iteration})

        response = await _client.chat.completions.create(
            model=model,
            messages=_conversation_history,
            tools=_llm_tools,
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

        # Append assistant message to history
        assistant_msg = {
            "role": "assistant",
            "content": assistant_message.content or "", 
        }
        
        # Include tool_calls in history
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

        _conversation_history.append(assistant_msg)

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

                mcp_result = await _session.call_tool(
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
            _conversation_history.extend(tool_results_messages)
            continue  # next iteration

        # No tool calls -> LLM is giving final answer
        final_response = assistant_message.content or "No response"
        logger.info(
            "Agent completed reasoning",
            extra={
                "final_message": (
                    final_response[:200]
                    if final_response
                    else "No content"
                )
            },
        )
        logger.info("Agent flow completed")
        return final_response

    logger.warning(
        "Agent reached max iterations without completing",
        extra={"max_iterations": max_iterations},
    )
    return "Agent reached maximum iterations. Please try again."


# FastAPI lifespan events
@asynccontextmanager
async def lifespan(app: FastAPI):
    global _session, _stdio_client_cm
    # Startup
    logger.info("Application startup: initializing agent")
    await initialize_session()
    yield
    # Shutdown
    logger.info("Application shutdown")
    if _session:
        await _session.__aexit__(None, None, None)
    if _stdio_client_cm:
        await _stdio_client_cm.__aexit__(None, None, None)


app = FastAPI(title="Travel Booking Agent", version="1.0.0", lifespan=lifespan)


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    model = os.getenv("LLM_MODEL", "gpt-4o")
    return HealthResponse(status="healthy", model=model)


@app.post("/query", response_model=QueryResponse)
async def query_endpoint(request: QueryRequest):
    """Process a customer query through the agent"""
    try:
        if not request.query or not request.query.strip():
            raise HTTPException(status_code=400, detail="Query cannot be empty")
        
        logger.info("Received query", extra={"query": request.query[:100]})
        response = await process_query(request.query)
        
        return QueryResponse(
            success=True,
            response=response,
        )
    except Exception as e:
        logger.error("Error processing query", extra={"error": str(e)})
        return QueryResponse(
            success=False,
            response="",
            error=str(e),
        )


@app.post("/reset")
async def reset_conversation():
    """Reset the conversation history"""
    global _conversation_history
    logger.info("Resetting conversation history")
    
    # Clear and reinitialize with system prompt
    _conversation_history.clear()
    _conversation_history.append({
        "role": "system",
        "content": """You are a travel booking assistant and customer executive. Your goal is to help customers book travel tours.
You have access to tools to:
1. Look up customer information by phone number
2. Search for available tours based on destination and budget
3. Book a tour for a customer

Be proactive, professional, and ask for information if needed. Use the tools strategically to complete the booking process.
Always be polite and provide clear summaries of actions taken. Remember all details provided by the customer in this conversation."""
    })
    
    return {"success": True, "message": "Conversation history reset"}


@app.get("/conversation-info")
async def conversation_info():
    """Get current conversation info"""
    global _conversation_history
    # Count non-system messages
    user_turns = sum(1 for msg in _conversation_history if msg.get("role") == "user")
    assistant_turns = sum(1 for msg in _conversation_history if msg.get("role") == "assistant")
    
    return {
        "total_messages": len(_conversation_history),
        "user_turns": user_turns,
        "assistant_turns": assistant_turns,
        "conversation_active": len(_conversation_history) > 1
    }

if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    logger.info("Starting FastAPI agent server", extra={"host": host, "port": port})
    uvicorn.run(app, host=host, port=port)
