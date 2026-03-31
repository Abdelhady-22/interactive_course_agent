"""FastAPI application entry point."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.routers import transcript_router, health_router
from app.utils.logger import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup/shutdown lifecycle."""
    settings = get_settings()
    logger.info("Starting Interactive Course Agent v1.0.0")
    logger.info("LLM Provider: %s / %s", settings.llm_provider, settings.llm_model)
    logger.info("LLM Review: %s (threshold=%.2f)", settings.enable_llm_review, settings.review_confidence_threshold)
    yield
    logger.info("Shutting down Interactive Course Agent")


app = FastAPI(
    title="Interactive Course Agent",
    description="AI-powered layout direction for educational video courses",
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS ──
settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ──
app.include_router(transcript_router.router)
app.include_router(health_router.router)


# ── Global exception handler ──
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all handler for unhandled exceptions."""
    logger.error("Unhandled exception on %s %s: %s", request.method, request.url.path, exc)
    return JSONResponse(
        status_code=500,
        content={
            "error": "INTERNAL_ERROR",
            "message": "An unexpected error occurred. Check server logs.",
            "details": {"exception": str(exc)[:300]},
        },
    )


@app.get("/")
async def root():
    """Root endpoint — API info."""
    return {
        "service": "Interactive Course Agent",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/health",
    }
