"""FastAPI application entry-point for the Muhurta Planner API."""

from __future__ import annotations

import asyncio
import uuid
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from contextvars import ContextVar

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
import structlog

from app.api.analytics import router as analytics_router
from app.api.auth import router as auth_router
from app.api.calendar import router as calendar_router
from app.api.feedback import router as feedback_router
from app.api.health import router as health_router
from app.api.plans import router as plans_router
from app.api.reminders import router as reminders_router
from app.config import get_settings
from app.core.errors import register_exception_handlers
from app.core.logging import setup_logging
from app.db.base import Base
from app.db.session import engine
from app.services.telegram_bot import run_telegram_bot_polling

# ── Context variable for per-request ID ──────────────────────────────────
request_id_ctx: ContextVar[str] = ContextVar("request_id", default="")

settings = get_settings()
logger = structlog.get_logger(__name__)


# ── Lifespan ─────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    """Startup / shutdown lifecycle hook."""
    setup_logging()
    logger.info("Starting Muhurta Planner API", env=settings.ENV, llm_provider=settings.LLM_PROVIDER)

    # Ensure database tables exist across all environments
    try:
        import app.db.models  # noqa: F401 - ensure all ORM models are registered
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            # Ensure password_hash exists on users table
            try:
                from sqlalchemy import text
                await conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS password_hash VARCHAR(255)"))
            except Exception:
                pass  # column already exists or dialect does not support IF NOT EXISTS
        logger.info("Database tables verified/created successfully", tables=list(Base.metadata.tables.keys()))
    except Exception as exc:
        logger.error("Could not automatically create tables at startup", error=str(exc))

    # Start Telegram Bot polling worker
    bot_task: asyncio.Task | None = None
    if settings.TELEGRAM_BOT_TOKEN and settings.TELEGRAM_BOT_TOKEN != "REPLACE_ME":
        bot_task = asyncio.create_task(run_telegram_bot_polling())
        logger.info("Telegram Bot polling worker initiated")

    yield

    # Shutdown
    if bot_task:
        bot_task.cancel()
        try:
            await bot_task
        except asyncio.CancelledError:
            pass

    await engine.dispose()
    logger.info("Muhurta Planner API shutdown complete")


# ── App factory ──────────────────────────────────────────────────────────
app = FastAPI(
    title="Muhurta Planner API",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS ─────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request-ID & Structured Logging Middleware ───────────────────────────
@app.middleware("http")
async def request_id_middleware(request: Request, call_next) -> Response:  # noqa: ANN001
    """Attach a unique request ID to every request/response cycle and log request metadata."""
    rid = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    request_id_ctx.set(rid)

    response: Response = await call_next(request)
    response.headers["X-Request-ID"] = rid
    return response


# ── Exception handlers ───────────────────────────────────────────────────
register_exception_handlers(app)

# ── Routers (all under /api/v1) ───────────────────────────────────────────
app.include_router(health_router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1")
app.include_router(plans_router, prefix="/api/v1")
app.include_router(calendar_router, prefix="/api/v1")
app.include_router(reminders_router, prefix="/api/v1")
app.include_router(feedback_router, prefix="/api/v1")
app.include_router(analytics_router, prefix="/api/v1")
