import asyncio
import json
import logging
import logging.config
import os
from urllib.parse import urlparse, urlunparse
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client
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

BOOKING_AGENT_URL = os.getenv("BOOKING_AGENT_URL", "http://booking-agent:9001/mcp")
PAYMENT_AGENT_URL = os.getenv("PAYMENT_AGENT_URL", "http://payment-agent:9002/mcp")

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
_booking_session: Optional[ClientSession] = None
_payment_session: Optional[ClientSession] = None
_client: Optional[AsyncOpenAI] = None
_llm_tools: list = []
_booking_client_cm = None  # Keep the context manager alive
_payment_client_cm = None  # Keep the context manager alive
_tool_routing: dict[str, tuple[ClientSession, str]] = {}
_conversation_history: list[dict] = []  # Persistent conversation history


async def initialize_session():
    """Initialize MCP session and OpenAI client on startup"""
    global _booking_session
    global _payment_session
    global _client
    global _llm_tools
    global _booking_client_cm
    global _payment_client_cm
    global _tool_routing
    global _conversation_history
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set")

    _client = AsyncOpenAI(api_key=api_key)
    model = os.getenv("LLM_MODEL", "gpt-4o")

    def _normalize_mcp_url(url: str) -> str:
        parsed = urlparse(url)
        if not parsed.path or parsed.path == "/":
            parsed = parsed._replace(path="/mcp")
        return urlunparse(parsed)

    booking_url = _normalize_mcp_url(BOOKING_AGENT_URL)
    payment_url = _normalize_mcp_url(PAYMENT_AGENT_URL)

    logger.info("Starting LLM-based agent", extra={"model": model})
    logger.info(
        "Connecting MCP agents",
        extra={
            "booking_agent_url": booking_url,
            "payment_agent_url": payment_url,
        },
    )

    if not booking_url or not payment_url:
        raise ValueError("BOOKING_AGENT_URL and PAYMENT_AGENT_URL must be set")

    # Add startup delay to allow services to stabilize
    startup_delay = float(os.getenv("STARTUP_DELAY", "0"))
    if startup_delay > 0:
        logger.info("Waiting before MCP initialization", extra={"delay_seconds": startup_delay})
        try:
            await asyncio.sleep(startup_delay)
        except asyncio.CancelledError:
            logger.warning("Startup was cancelled during initial delay")
            raise

    async def _wait_for_tcp(url: str, retries: int, delay: float, name: str):
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
                    extra={"agent": name, "host": host, "port": port, "attempt": attempt, "error": str(exc)},
                )
                if attempt < retries:
                    await asyncio.sleep(delay)
        raise RuntimeError(f"Timed out waiting for {name} MCP agent at {host}:{port}") from last_exc

    async def _start_mcp_session(url: str, name: str):
        max_retries = int(os.getenv("MCP_CONNECT_RETRIES", "15"))
        delay_seconds = float(os.getenv("MCP_CONNECT_DELAY", "1.0"))
        await _wait_for_tcp(url, max_retries, delay_seconds, name)

        last_exc: Exception | None = None
        for attempt in range(1, max_retries + 1):
            try:
                cm = streamable_http_client(url)
                entered = False
                try:
                    logger.info("Attempting MCP session initialization", extra={"agent": name, "url": url, "attempt": attempt})
                    result = await cm.__aenter__()
                    entered = True
                    read, write = result[0], result[1]
                    session = ClientSession(read, write)
                    await session.__aenter__()
                    await session.initialize()
                    logger.info("MCP session initialized successfully", extra={"agent": name, "url": url})
                    return session, cm
                except Exception as exc:
                    last_exc = exc
                    logger.warning(
                        "MCP connect failed after port was reachable",
                        extra={"agent": name, "url": url, "attempt": attempt, "error": str(exc)},
                    )
                    if entered:
                        try:
                            await cm.__aexit__(None, None, None)
                        except Exception:
                            pass
                    if attempt < max_retries:
                        try:
                            await asyncio.sleep(delay_seconds)
                        except asyncio.CancelledError:
                            logger.warning("Startup was cancelled while waiting to retry MCP connection", extra={"agent": name})
                            raise
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                last_exc = exc
                logger.warning("Unexpected error during MCP connection", extra={"agent": name, "error": str(exc)})
                if attempt < max_retries:
                    try:
                        await asyncio.sleep(delay_seconds)
                    except asyncio.CancelledError:
                        raise

        raise RuntimeError(f"Failed to connect to {name} MCP agent at {url}") from last_exc

    try:
        _booking_session, _booking_client_cm = await _start_mcp_session(booking_url, "booking")
    except Exception as e:
        logger.error("Failed to initialize booking agent session", extra={"error": str(e)})
        logger.warning("Booking agent will not be available")
        _booking_session = None
        _booking_client_cm = None
    
    try:
        _payment_session, _payment_client_cm = await _start_mcp_session(payment_url, "payment")
    except Exception as e:
        logger.error("Failed to initialize payment agent session", extra={"error": str(e)})
        logger.warning("Payment agent will not be available")
        _payment_session = None
        _payment_client_cm = None

    _llm_tools = []
    _tool_routing = {}

    async def _register_tools(prefix: str, session: ClientSession):
        if session is None:
            logger.warning("Session not available for tools registration", extra={"prefix": prefix})
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
            _tool_routing[tool_name] = (session, tool.name)
            _llm_tools.append(
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

    if _booking_session:
        await _register_tools("booking", _booking_session)
    if _payment_session:
        await _register_tools("payment", _payment_session)

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
4. Process a payment (fake for now)

Be proactive, professional, and ask for information if needed. Use the tools strategically to complete the booking process.
Always be polite and provide clear summaries of actions taken. Remember all details provided by the customer in this conversation.
Before calling any payment tool, you must obtain explicit user consent in the conversation."""
    })



async def process_query(user_query: str) -> str:
    """Process a user query through the agent"""
    global _booking_session, _payment_session, _client, _llm_tools, _tool_routing, _conversation_history
    
    if not _client:
        raise RuntimeError("Agent not initialized - OpenAI client unavailable")
    
    if not _llm_tools:
        logger.warning("No tools available - MCP agents may not be connected")
        return "Sorry, the agent tools are not currently available. Please check that the booking and payment services are running."
    
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

                routing = _tool_routing.get(tool_name)
                if not routing:
                    logger.warning("Unknown tool requested", extra={"tool_name": tool_name})
                    result_data = {"error": "UNKNOWN_TOOL"}
                else:
                    session, actual_tool_name = routing
                    mcp_result = await session.call_tool(
                        actual_tool_name, arguments=tool_args
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
    global _booking_session, _payment_session, _booking_client_cm, _payment_client_cm
    # Startup
    logger.info("Application startup: initializing agent")
    await initialize_session()
    yield
    # Shutdown
    logger.info("Application shutdown")
    if _booking_session:
        await _booking_session.__aexit__(None, None, None)
    if _payment_session:
        await _payment_session.__aexit__(None, None, None)
    if _booking_client_cm:
        await _booking_client_cm.__aexit__(None, None, None)
    if _payment_client_cm:
        await _payment_client_cm.__aexit__(None, None, None)


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
