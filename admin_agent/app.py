from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware

from config import load_settings
from logging_config import configure_logging, get_logger
from models import QueryRequest, QueryResponse, HealthResponse
from service import AdminAgentService


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = load_settings()
    logger = get_logger("admin-agent")
    service = AdminAgentService(settings, logger)
    app.state.service = service

    configure_logging()
    logger.info(
        "Starting Admin Agent FastAPI server",
        extra={"host": settings.host, "port": settings.port},
    )

    await service.initialize()
    yield
    await service.shutdown()


def create_app() -> FastAPI:
    app = FastAPI(title="Travel Booking Admin Agent", version="1.0.0", lifespan=lifespan)
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health", response_model=HealthResponse)
    async def health_check():
        return app.state.service.health()

    @app.post("/query", response_model=QueryResponse)
    async def query_endpoint(request: QueryRequest):
        if not request.query or not request.query.strip():
            raise HTTPException(status_code=400, detail="Query cannot be empty")
        return await app.state.service.process_query(request.query)

    @app.post("/stream-query")
    async def stream_query_endpoint(request: QueryRequest):
        if not request.query or not request.query.strip():
            raise HTTPException(status_code=400, detail="Query cannot be empty")

        async def event_stream():
            async for chunk in app.state.service.stream_query(request.query):
                yield f"{chunk}"

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

    return app


def main():
    import uvicorn
    settings = load_settings()
    configure_logging()
    app = create_app()
    uvicorn.run(app, host=settings.host, port=settings.port)


if __name__ == "__main__":
    main()
