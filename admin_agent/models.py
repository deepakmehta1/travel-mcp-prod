from pydantic import BaseModel


class QueryRequest(BaseModel):
    query: str


class QueryResponse(BaseModel):
    response: str


class HealthResponse(BaseModel):
    status: str
    model: str
