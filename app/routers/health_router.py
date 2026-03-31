"""Health router — service health check."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.config import Settings, get_settings
from app.llm.provider import LLMProvider

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health")
async def health_check(settings: Settings = Depends(get_settings)) -> dict:
    """Returns service status, LLM provider info, and version."""
    llm = LLMProvider(settings)
    llm_status = llm.health_check()

    return {
        "status": "healthy",
        "version": "1.0.0",
        "llm": llm_status,
        "settings": {
            "provider": settings.llm_provider,
            "model": settings.llm_model,
            "review_enabled": settings.enable_llm_review,
            "review_threshold": settings.review_confidence_threshold,
        },
    }
