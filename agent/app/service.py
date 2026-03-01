import asyncio
import json
from typing import Optional

from fastapi import HTTPException
from openai import AsyncOpenAI
from mcp import ClientSession

from .config import Settings
from .mcp import start_mcp_session, register_tools
from .prompts import SYSTEM_PROMPT
from .models import QueryResponse, HealthResponse, safe_log_extra


class AgentService:
    def __init__(self, settings: Settings, logger):
        self.settings = settings
        self.logger = logger
        self._booking_session: Optional[ClientSession] = None
        self._payment_session: Optional[ClientSession] = None
        self._booking_cm = None
        self._payment_cm = None
        self._client: Optional[AsyncOpenAI] = None
        self._llm_tools: list = []
        self._tool_routing: dict[str, tuple[ClientSession, str]] = {}
        self._conversation_history: list[dict] = []
        self._last_assistant_content: str | None = None
        self._auth_context: dict | None = None
        self._auth_context_loaded: bool = False

    async def initialize(self):
        self._client = AsyncOpenAI(api_key=self.settings.openai_api_key)

        # optional startup delay
        if self.settings.startup_delay > 0:
            self.logger.info(
                "Waiting before MCP initialization",
                extra={"delay_seconds": self.settings.startup_delay},
            )
            await asyncio.sleep(self.settings.startup_delay)

        self.logger.info(
            "Connecting MCP agents",
            extra={
                "booking_agent_url": self.settings.booking_agent_url,
                "payment_agent_url": self.settings.payment_agent_url,
            },
        )

        self._booking_session, self._booking_cm = await start_mcp_session(
            self.settings.booking_agent_url,
            "booking",
            self.settings.mcp_connect_retries,
            self.settings.mcp_connect_delay,
            self.logger,
        )

        self._payment_session, self._payment_cm = await start_mcp_session(
            self.settings.payment_agent_url,
            "payment",
            self.settings.mcp_connect_retries,
            self.settings.mcp_connect_delay,
            self.logger,
        )

        self._llm_tools = []
        self._tool_routing = {}

        await register_tools(
            "booking",
            self._booking_session,
            self._llm_tools,
            self._tool_routing,
            self.logger,
        )
        await register_tools(
            "payment",
            self._payment_session,
            self._llm_tools,
            self._tool_routing,
            self.logger,
        )

        self._conversation_history = [
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            }
        ]
        self._auth_context = None
        self._auth_context_loaded = False

    async def shutdown(self):
        if self._booking_session:
            await self._booking_session.__aexit__(None, None, None)
        if self._payment_session:
            await self._payment_session.__aexit__(None, None, None)
        if self._booking_cm:
            await self._booking_cm.__aexit__(None, None, None)
        if self._payment_cm:
            await self._payment_cm.__aexit__(None, None, None)

    async def process_query(self, user_query: str) -> str:
        if not user_query.strip():
            raise HTTPException(status_code=400, detail="Query cannot be empty")
        if not self._client or not self._llm_tools:
            raise RuntimeError("Agent not initialized")

        model = self.settings.llm_model
        self.logger.info(
            "Processing user query",
            extra={
                "user_request": user_query,
                "conversation_turn": len(self._conversation_history),
            },
        )

        self._conversation_history.append({"role": "user", "content": user_query})

        max_iterations = 20
        iteration = 0

        while iteration < max_iterations:
            iteration += 1
            self.logger.info("Agent iteration", extra={"iteration": iteration})

            response = await self._client.chat.completions.create(
                model=model,
                messages=self._conversation_history,
                tools=self._llm_tools,
                tool_choice="auto",
            )

            choice = response.choices[0]
            assistant_message = choice.message

            self.logger.info(
                "LLM response received",
                extra={
                    "stop_reason": choice.finish_reason,
                    "tool_calls_count": len(assistant_message.tool_calls or []),
                },
            )

            assistant_msg = {
                "role": "assistant",
                "content": assistant_message.content or "",
            }
            if assistant_message.tool_calls:
                assistant_msg["tool_calls"] = [
                    {
                        "id": tc.id,
                        "type": tc.type,
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        },
                    }
                    for tc in assistant_message.tool_calls
                ]
            self._conversation_history.append(assistant_msg)

            if assistant_message.tool_calls:
                tool_results_messages: list[dict] = []

                for tool_call in assistant_message.tool_calls:
                    tool_name = tool_call.function.name
                    tool_args = json.loads(tool_call.function.arguments or "{}")

                    self.logger.info(
                        "Calling tool via MCP",
                        extra={
                            "tool_name": tool_name,
                            "tool_args": safe_log_extra(tool_args),
                        },
                    )

                    routing = self._tool_routing.get(tool_name)
                    if not routing:
                        self.logger.warning(
                            "Unknown tool requested", extra={"tool_name": tool_name}
                        )
                        result_data = {"error": "UNKNOWN_TOOL"}
                    else:
                        session, actual_tool_name = routing
                        mcp_result = await session.call_tool(
                            actual_tool_name, arguments=tool_args
                        )
                        result_data = json.loads(mcp_result.content[0].text)

                    self.logger.info(
                        "Tool result received",
                        extra={
                            "tool_name": tool_name,
                            "result_keys": list(result_data.keys()),
                        },
                    )

                    tool_results_messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "name": tool_name,
                            "content": json.dumps(result_data),
                        }
                    )

                self._conversation_history.extend(tool_results_messages)
                continue

            final_response = assistant_message.content or "No response"
            self.logger.info(
                "Agent completed reasoning",
                extra={
                    "final_message": (
                        final_response[:200] if final_response else "No content"
                    )
                },
            )
            self._last_assistant_content = final_response
            return final_response

        self.logger.warning(
            "Agent reached max iterations without completing",
            extra={"max_iterations": max_iterations},
        )
        return "Agent reached maximum iterations. Please try again."

    def reset(self):
        self._conversation_history = [
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            }
        ]
        self._last_assistant_content = None
        self._auth_context_loaded = False

    async def set_auth_context(self, payload: dict):
        if not payload:
            return
        if self._auth_context_loaded and self._auth_context == payload:
            return
        self._auth_context = payload
        self._auth_context_loaded = True
        phone = payload.get("phone")
        email = payload.get("email")
        if not phone or not self._booking_session:
            return
        try:
            result = await self._booking_session.call_tool(
                "getCustomerContext",
                arguments={"phone": phone},
            )
            data = json.loads(result.content[0].text)
        except Exception:
            data = {"found": False}
        # Inject a system context note for the LLM
        if data.get("found") and data.get("customer"):
            customer = data["customer"]
            context = (
                f"Authenticated user context: name={customer.get('name')}, "
                f"phone={customer.get('phone')}, email={customer.get('email')}."
            )
        else:
            context = (
                f"Authenticated user context: email={email}, phone={phone}. "
                "No customer profile found yet."
            )
        self._conversation_history.append({"role": "system", "content": context})

    def conversation_info(self):
        user_turns = len(
            [m for m in self._conversation_history if m.get("role") == "user"]
        )
        assistant_turns = len(
            [m for m in self._conversation_history if m.get("role") == "assistant"]
        )
        total_messages = len(self._conversation_history)
        return {
            "user_turns": user_turns,
            "assistant_turns": assistant_turns,
            "total_messages": total_messages,
            "conversation_active": True,
        }

    def health(self) -> HealthResponse:
        return HealthResponse(status="healthy", model=self.settings.llm_model)

    async def get_hints(self) -> list[str]:
        if not self._booking_session or not self._client:
            return []

        # fetch current tours to ground suggestions
        try:
            mcp_result = await self._booking_session.call_tool(
                "searchTours", arguments={}
            )
            data = json.loads(mcp_result.content[0].text)
            tours = data.get("tours", [])
        except Exception as e:
            self.logger.warning(
                "Hint generation failed (tour fetch)", extra={"error": str(e)}
            )
            return []

        if not tours:
            return []

        # get last user and assistant messages to tailor suggestions
        last_user = None
        for msg in reversed(self._conversation_history):
            if msg.get("role") == "user":
                last_user = msg.get("content")
                break
        last_assistant = self._last_assistant_content or ""

        # Build a grounded prompt listing only tours we actually offer
        tours_text = "\n".join(
            f"- {t.get('name','')} (code {t.get('code','')}) to {t.get('destination','')}, price {t.get('price') or t.get('base_price')}"
            for t in tours
        )

        prompt = [
            {
                "role": "system",
                "content": (
                    "You generate 2-3 short next-step suggestions for the user in a travel booking chat. "
                    "Use ONLY the tours listed below. Do not invent destinations or services. "
                    "Keep each suggestion under 80 characters, actionable, and relevant to the last exchange. "
                    "Return ONLY a JSON array of strings, no prose. "
                    "Tours available:\n"
                    f"{tours_text}"
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Previous user message:\n{last_user or ''}\n\n"
                    f"Last assistant reply:\n{last_assistant}"
                ),
            },
        ]

        try:
            resp = await self._client.chat.completions.create(
                model=self.settings.llm_model,
                messages=prompt,
                temperature=0.4,
                max_tokens=150,
            )
            content = resp.choices[0].message.content or "[]"
            hints = json.loads(content)
            if isinstance(hints, list):
                # keep unique and short
                deduped = []
                seen = set()
                for h in hints:
                    hs = str(h)[:120]
                    if hs not in seen:
                        deduped.append(hs)
                        seen.add(hs)
            return deduped[:5]
        except Exception as e:
            self.logger.warning("Hint generation failed", extra={"error": str(e)})
        return []

    async def stream_query(self, user_query: str):
        if not user_query.strip():
            raise HTTPException(status_code=400, detail="Query cannot be empty")
        if not self._client or not self._llm_tools:
            raise RuntimeError("Agent not initialized")

        # Kick off the full process in the background so we can stream early
        task = asyncio.create_task(self.process_query(user_query))

        try:
            final = await task
            delay = 0.02  # 20ms per character
            chunk_size = 1  # letter by letter
            for i in range(0, len(final), chunk_size):
                yield final[i : i + chunk_size]
                await asyncio.sleep(delay)  # non-blocking delay between chunks
        except Exception as e:
            self.logger.error("Streaming failed", extra={"error": str(e)})
            yield "Sorry, streaming failed."

    async def register_user(
        self, name: str, email: str, phone: str, password: str
    ) -> dict:
        if not self._booking_session:
            raise RuntimeError("Booking agent unavailable")
        result = await self._booking_session.call_tool(
            "registerUser",
            arguments={
                "name": name,
                "email": email,
                "phone": phone,
                "password": password,
            },
        )
        return json.loads(result.content[0].text)

    async def login_user(self, email: str, password: str) -> dict:
        if not self._booking_session:
            raise RuntimeError("Booking agent unavailable")
        result = await self._booking_session.call_tool(
            "loginUser",
            arguments={"email": email, "password": password},
        )
        return json.loads(result.content[0].text)


async def process_query(service: AgentService, question: str) -> QueryResponse:
    try:
        response_text = await service.process_query(question)
        return QueryResponse(success=True, response=response_text)
    except HTTPException as exc:
        raise exc
    except Exception as e:
        service.logger.error("Error processing query", extra={"error": str(e)})
        return QueryResponse(success=False, response="", error=str(e))
