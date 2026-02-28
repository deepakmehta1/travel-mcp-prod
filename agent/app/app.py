from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse

from .config import load_settings
from .logging_config import configure_logging, get_logger
from .models import QueryRequest, QueryResponse, HealthResponse
from .service import AgentService, process_query
from .cors import add_cors


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = load_settings()
    logger = get_logger("agent")
    service = AgentService(settings, logger)
    app.state.service = service

    configure_logging()
    logger.info(
        "Starting FastAPI agent server",
        extra={"host": settings.host, "port": settings.port},
    )

    await service.initialize()
    yield
    await service.shutdown()


def create_app() -> FastAPI:
    app = FastAPI(title="Travel Booking Agent", version="1.0.0", lifespan=lifespan)
    add_cors(app)

    @app.get("/health", response_model=HealthResponse)
    async def health_check():
        return app.state.service.health()

    @app.post("/query", response_model=QueryResponse)
    async def query_endpoint(request: QueryRequest):
        if not request.query or not request.query.strip():
            raise HTTPException(status_code=400, detail="Query cannot be empty")
        return await process_query(app.state.service, request.query)

    @app.post("/stream-query")
    async def stream_query_endpoint(request: QueryRequest):
        if not request.query or not request.query.strip():
            raise HTTPException(status_code=400, detail="Query cannot be empty")

        async def event_stream():
            async for chunk in app.state.service.stream_query(request.query):
                yield f"{chunk}"  # SSE format for universal client support

        return StreamingResponse(
            event_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    @app.post("/reset")
    async def reset_endpoint():
        app.state.service.reset()
        return {"success": True}

    @app.get("/hints")
    async def hints():
        try:
            return {"hints": await app.state.service.get_hints()}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/conversation-info")
    async def conversation_info():
        return app.state.service.conversation_info()

    return app
