from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.responses import StreamingResponse

from .config import load_settings
from .logging_config import configure_logging, get_logger
from .models import (
    QueryRequest,
    QueryResponse,
    HealthResponse,
    LoginRequest,
    RegisterRequest,
    AuthResponse,
)
from .service import AgentService, process_query
from .cors import add_cors
from .jwt_utils import create_access_token, verify_token


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


async def get_current_user(authorization: str = Header(...)):
    """Dependency to extract and validate bearer token."""
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    token = authorization[7:]  # Remove "Bearer " prefix
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return payload


def create_app() -> FastAPI:
    app = FastAPI(title="Travel Booking Agent", version="1.0.0", lifespan=lifespan)
    add_cors(app)

    @app.get("/health", response_model=HealthResponse)
    async def health_check():
        return app.state.service.health()

    @app.post("/auth/login", response_model=AuthResponse)
    async def login_endpoint(request: LoginRequest):
        if not request.email or not request.password:
            raise HTTPException(
                status_code=400, detail="Email and password are required"
            )
        # For demo purposes, accept any email/password combination
        token = create_access_token(request.email, "")
        return AuthResponse(email=request.email, phone="", token=token)

    @app.post("/auth/register", response_model=AuthResponse)
    async def register_endpoint(request: RegisterRequest):
        if not request.email or not request.phone or not request.verification_code:
            raise HTTPException(
                status_code=400,
                detail="Email, phone, and verification code are required",
            )
        # For demo purposes, accept hardcoded verification code 1234
        if request.verification_code != "1234":
            raise HTTPException(status_code=400, detail="Invalid verification code")
        token = create_access_token(request.email, request.phone)
        return AuthResponse(email=request.email, phone=request.phone, token=token)

    @app.post("/query", response_model=QueryResponse)
    async def query_endpoint(
        request: QueryRequest, current_user: dict = Depends(get_current_user)
    ):
        if not request.query or not request.query.strip():
            raise HTTPException(status_code=400, detail="Query cannot be empty")
        return await process_query(app.state.service, request.query)

    @app.post("/stream-query")
    async def stream_query_endpoint(
        request: QueryRequest, current_user: dict = Depends(get_current_user)
    ):
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
    async def reset_endpoint(current_user: dict = Depends(get_current_user)):
        app.state.service.reset()
        return {"success": True}

    @app.get("/hints")
    async def hints(current_user: dict = Depends(get_current_user)):
        try:
            return {"hints": await app.state.service.get_hints()}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/conversation-info")
    async def conversation_info(current_user: dict = Depends(get_current_user)):
        return app.state.service.conversation_info()

    return app
