from typing import Optional, Any
from pydantic import BaseModel


class QueryRequest(BaseModel):
    query: str


class QueryResponse(BaseModel):
    success: bool
    response: str
    error: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    model: str


class LoginRequest(BaseModel):
    email: str
    password: str


class RegisterRequest(BaseModel):
    name: str
    email: str
    phone: str
    password: str


class AuthResponse(BaseModel):
    email: str
    phone: str
    token: str


RESERVED_LOG_ATTRS = {
    "name",
    "msg",
    "args",
    "created",
    "filename",
    "funcName",
    "levelname",
    "levelno",
    "lineno",
    "module",
    "pathname",
    "process",
    "processName",
    "relativeCreated",
    "thread",
    "threadName",
    "exc_info",
    "exc_text",
    "stack_info",
    "getMessage",
    "message",
    "asctime",
    "msecs",
}


def safe_log_extra(data: dict[str, Any]) -> dict[str, Any]:
    if not data:
        return data
    safe_data = {}
    for key, value in data.items():
        if key in RESERVED_LOG_ATTRS:
            safe_data[f"data_{key}"] = value
        else:
            safe_data[key] = value
    return safe_data
