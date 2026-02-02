"""
OpenClaw Lite - Lightweight API-only LLM Router

Routes queries between OpenAI (simple/cheap) and Claude (complex/powerful).
"""

import logging
import time
from collections import defaultdict
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from .config import settings
from .providers import OpenAIProvider, ClaudeProvider
from .router import QueryRouter
from .cost_tracker import CostTracker

# Logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Global instances
query_router: QueryRouter | None = None

# Rate limiting storage
rate_limit_store: dict[str, list[float]] = defaultdict(list)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown."""
    global query_router

    logger.info(f"Starting OpenClaw Lite v{settings.version}")

    # Initialize providers
    openai_provider = OpenAIProvider(
        api_key=settings.openai_api_key,
        model=settings.openai_model,
    )
    claude_provider = ClaudeProvider(
        api_key=settings.anthropic_api_key,
        model=settings.claude_model,
    )

    # Check availability
    if not openai_provider.is_available() and not claude_provider.is_available():
        raise RuntimeError("No API keys configured. Set OPENAI_API_KEY and/or ANTHROPIC_API_KEY")

    logger.info(f"OpenAI ({settings.openai_model}): {'available' if openai_provider.is_available() else 'not configured'}")
    logger.info(f"Claude ({settings.claude_model}): {'available' if claude_provider.is_available() else 'not configured'}")

    # Initialize router
    cost_tracker = CostTracker(monthly_budget_usd=settings.monthly_budget_usd)
    query_router = QueryRouter(
        openai_provider=openai_provider,
        claude_provider=claude_provider,
        cost_tracker=cost_tracker,
        complexity_threshold=settings.complexity_threshold,
    )

    logger.info(f"Complexity threshold: {settings.complexity_threshold}")
    logger.info(f"Monthly budget: ${settings.monthly_budget_usd}")

    yield

    logger.info("Shutting down OpenClaw Lite")


# FastAPI app
app = FastAPI(
    title="OpenClaw Lite",
    description="Lightweight API router for OpenAI and Claude",
    version=settings.version,
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Rate limiting middleware
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    if request.url.path.startswith("/v1/"):
        client_ip = request.client.host if request.client else "unknown"
        now = time.time()
        window_start = now - settings.rate_limit_window

        # Clean old entries
        rate_limit_store[client_ip] = [
            t for t in rate_limit_store[client_ip] if t > window_start
        ]

        if len(rate_limit_store[client_ip]) >= settings.rate_limit_requests:
            return JSONResponse(
                status_code=429,
                content={"error": "Rate limit exceeded. Try again later."},
            )

        rate_limit_store[client_ip].append(now)

    return await call_next(request)


# Request/Response models
class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage]
    max_tokens: int = 512
    temperature: float = 0.7


class ChatResponse(BaseModel):
    id: str
    model: str
    content: str
    provider: str
    usage: dict[str, int]


# Endpoints
@app.get("/health")
async def health():
    """Health check."""
    return {
        "status": "healthy",
        "version": settings.version,
    }


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "OpenClaw Lite",
        "version": settings.version,
        "description": "Lightweight API router for OpenAI and Claude",
    }


@app.post("/v1/chat/completions", response_model=ChatResponse)
async def chat_completions(request: ChatRequest):
    """
    Chat completions endpoint.

    Routes to OpenAI (simple queries) or Claude (complex queries).
    """
    if not query_router:
        raise HTTPException(status_code=503, detail="Service not initialized")

    try:
        messages = [{"role": m.role, "content": m.content} for m in request.messages]

        response = await query_router.route(
            messages=messages,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
        )

        return ChatResponse(
            id=response.id,
            model=response.model,
            content=response.content,
            provider=response.provider,
            usage=response.usage,
        )

    except Exception as e:
        logger.error(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/v1/models")
async def list_models():
    """List available models."""
    models = []
    if settings.openai_api_key:
        models.append({"id": settings.openai_model, "provider": "openai"})
    if settings.anthropic_api_key:
        models.append({"id": settings.claude_model, "provider": "claude"})
    return {"data": models}


@app.get("/v1/stats")
async def stats():
    """Get routing and cost statistics."""
    if not query_router:
        raise HTTPException(status_code=503, detail="Service not initialized")
    return query_router.get_stats()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=settings.port)
