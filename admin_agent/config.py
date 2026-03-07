import os
from dataclasses import dataclass


@dataclass
class Settings:
    host: str
    port: int
    model: str
    openai_api_key: str
    admin_server_url: str


def load_settings() -> Settings:
    return Settings(
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8001")),
        model=os.getenv("LLM_MODEL", "gpt-4o"),
        openai_api_key=os.getenv("OPENAI_API_KEY", ""),
        admin_server_url=os.getenv("ADMIN_SERVER_URL", "http://admin-server:9003/mcp"),
    )
