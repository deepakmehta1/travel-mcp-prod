from dataclasses import dataclass
import os


@dataclass
class Settings:
    openai_api_key: str
    llm_model: str
    booking_agent_url: str
    payment_agent_url: str
    mcp_connect_retries: int
    mcp_connect_delay: float
    startup_delay: float
    host: str
    port: int


def load_settings() -> Settings:
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set")

    return Settings(
        openai_api_key=openai_api_key,
        llm_model=os.getenv("LLM_MODEL", "gpt-4o"),
        booking_agent_url=os.getenv("BOOKING_AGENT_URL", "http://booking-agent:9001/mcp"),
        payment_agent_url=os.getenv("PAYMENT_AGENT_URL", "http://payment-agent:9002/mcp"),
        mcp_connect_retries=int(os.getenv("MCP_CONNECT_RETRIES", "15")),
        mcp_connect_delay=float(os.getenv("MCP_CONNECT_DELAY", "1.0")),
        startup_delay=float(os.getenv("STARTUP_DELAY", "0")),
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8000")),
    )
