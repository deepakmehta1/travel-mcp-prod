import json
import logging
from typing import Any, AsyncGenerator

from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client
from openai import AsyncOpenAI

from config import Settings
from prompts import SYSTEM_PROMPT, USER_QUERY_TEMPLATE
from models import HealthResponse, QueryResponse


class AdminAgentService:
    def __init__(self, settings: Settings, logger: logging.Logger):
        self.settings = settings
        self.logger = logger
        self.openai_client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.session: ClientSession | None = None
        self.mcp_context = None
        self._mcp_context_entered = False
        self.conversation_history: list[dict[str, Any]] = []
        self.available_tools: list[dict] = []

    async def initialize(self):
        """Initialize the MCP session and discover tools from admin server"""
        self.logger.info("Initializing admin agent service")
        
        try:
            # Connect to admin server using MCP
            self.mcp_context = streamable_http_client(self.settings.admin_server_url)
            result = await self.mcp_context.__aenter__()
            self._mcp_context_entered = True
            read, write = result[0], result[1]
            self.session = ClientSession(read, write)
            await self.session.__aenter__()
            
            # Initialize session
            await self.session.initialize()
            
            # List tools from admin server
            tools_list = await self.session.list_tools()
            
            # Convert MCP tools to OpenAI function format
            self.available_tools = []
            for tool in tools_list.tools:
                self.available_tools.append({
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description or "",
                        "parameters": tool.inputSchema,
                    }
                })
            
            self.logger.info(f"Discovered {len(self.available_tools)} admin tools")
                
        except Exception as e:
            self.logger.error(f"Failed to initialize admin agent: {e}")
            if self.session:
                await self.session.__aexit__(None, None, None)
                self.session = None
            if self.mcp_context and self._mcp_context_entered:
                await self.mcp_context.__aexit__(None, None, None)
                self._mcp_context_entered = False
            self.mcp_context = None
            raise

    async def shutdown(self):
        """Cleanup resources"""
        if self.session:
            await self.session.__aexit__(None, None, None)
        if self.mcp_context and self._mcp_context_entered:
            await self.mcp_context.__aexit__(None, None, None)
        self.logger.info("Admin agent service shutdown complete")

    def health(self) -> HealthResponse:
        return HealthResponse(status="healthy", model=self.settings.model)

    def reset(self):
        """Reset conversation history"""
        self.conversation_history = []
        self.logger.info("Conversation history reset")

    async def call_tool(self, tool_name: str, arguments: dict) -> str:
        """Call a tool via MCP"""
        try:
            result = await self.session.call_tool(tool_name, arguments=arguments)
            # Extract text content from MCP response
            if result.content and len(result.content) > 0:
                return result.content[0].text
            return json.dumps({})
        except Exception as e:
            self.logger.error(f"Tool call failed: {e}")
            return json.dumps({"error": str(e)})

    async def process_query(self, query: str) -> QueryResponse:
        """Process a query using the LLM and available tools"""
        self.logger.info(f"Processing query: {query}")

        # Add user message to history
        self.conversation_history.append({
            "role": "user",
            "content": USER_QUERY_TEMPLATE.format(query=query)
        })
        
        # Run agentic loop
        max_iterations = 20
        iteration = 0
        
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            *self.conversation_history
        ]
        
        while iteration < max_iterations:
            iteration += 1
            self.logger.info(f"Agentic loop iteration {iteration}")
            
            # Call LLM
            response = await self.openai_client.chat.completions.create(
                model=self.settings.model,
                messages=messages,
                tools=self.available_tools if self.available_tools else None,
                tool_choice="auto" if self.available_tools else None,
            )
            
            assistant_message = response.choices[0].message
            
            # Check if LLM wants to call tools
            if assistant_message.tool_calls:
                # Add assistant message with tool calls to history
                messages.append({
                    "role": "assistant",
                    "content": assistant_message.content or "",
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments
                            }
                        }
                        for tc in assistant_message.tool_calls
                    ]
                })
                
                # Execute tool calls
                for tool_call in assistant_message.tool_calls:
                    tool_name = tool_call.function.name
                    tool_args = json.loads(tool_call.function.arguments)
                    
                    self.logger.info(f"Calling tool: {tool_name} with args: {tool_args}")
                    
                    tool_result = await self.call_tool(tool_name, tool_args)
                    
                    # Add tool result to messages
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": tool_result
                    })
            else:
                # No more tool calls, we have final response
                final_response = assistant_message.content or "I couldn't process that request."
                
                # Add to conversation history
                self.conversation_history.append({
                    "role": "assistant",
                    "content": final_response
                })
                
                return QueryResponse(response=final_response)
        
        # Max iterations reached
        return QueryResponse(response="I apologize, but I couldn't complete that request within the iteration limit.")

    async def stream_query(self, query: str) -> AsyncGenerator[str, None]:
        """Stream the response to a query"""
        self.logger.info(f"Streaming query: {query}")
        
        # Add user message to history
        self.conversation_history.append({
            "role": "user",
            "content": USER_QUERY_TEMPLATE.format(query=query)
        })
        
        # Run agentic loop
        max_iterations = 20
        iteration = 0
        
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            *self.conversation_history
        ]
        
        accumulated_response = ""
        
        while iteration < max_iterations:
            iteration += 1
            self.logger.info(f"Agentic loop iteration {iteration}")
            
            # Call LLM with streaming
            stream = await self.openai_client.chat.completions.create(
                model=self.settings.model,
                messages=messages,
                tools=self.available_tools if self.available_tools else None,
                tool_choice="auto" if self.available_tools else None,
                stream=True,
            )
            
            tool_calls = []
            content_chunks = []
            
            async for chunk in stream:
                delta = chunk.choices[0].delta if chunk.choices else None
                if not delta:
                    continue
                
                # Collect content
                if delta.content:
                    content_chunks.append(delta.content)
                    accumulated_response += delta.content
                    yield delta.content
                
                # Collect tool calls
                if delta.tool_calls:
                    for tc in delta.tool_calls:
                        if tc.index >= len(tool_calls):
                            tool_calls.append({
                                "id": tc.id,
                                "function": {"name": tc.function.name if tc.function.name else "", "arguments": ""}
                            })
                        if tc.function.arguments:
                            tool_calls[tc.index]["function"]["arguments"] += tc.function.arguments
            
            # Check if we have tool calls to execute
            if tool_calls:
                # Add assistant message with tool calls
                messages.append({
                    "role": "assistant",
                    "content": "".join(content_chunks) or "",
                    "tool_calls": [
                        {
                            "id": tc["id"],
                            "type": "function",
                            "function": tc["function"]
                        }
                        for tc in tool_calls
                    ]
                })
                
                # Execute tools
                for tool_call in tool_calls:
                    tool_name = tool_call["function"]["name"]
                    tool_args = json.loads(tool_call["function"]["arguments"])
                    
                    self.logger.info(f"Calling tool: {tool_name}")
                    
                    tool_result = await self.call_tool(tool_name, tool_args)
                    
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call["id"],
                        "content": tool_result
                    })
            else:
                # No tool calls, final response
                self.conversation_history.append({
                    "role": "assistant",
                    "content": accumulated_response
                })
                return
        
        # Max iterations reached
        final_msg = "\n\n[Request exceeded iteration limit]"
        yield final_msg
        self.conversation_history.append({
            "role": "assistant",
            "content": accumulated_response + final_msg
        })
