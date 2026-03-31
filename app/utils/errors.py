"""Custom exceptions and error codes for machine-readable error handling."""

from __future__ import annotations
from fastapi import HTTPException


class ErrorCode:
    """Machine-readable error codes for API consumers."""

    INVALID_INPUT = "INVALID_INPUT"
    UNSUPPORTED_FORMAT = "UNSUPPORTED_FORMAT"
    INGESTION_FAILED = "INGESTION_FAILED"
    RULE_ENGINE_ERROR = "RULE_ENGINE_ERROR"
    LLM_UNAVAILABLE = "LLM_UNAVAILABLE"
    LLM_TIMEOUT = "LLM_TIMEOUT"
    LLM_INVALID_RESPONSE = "LLM_INVALID_RESPONSE"
    LLM_ALL_RETRIES_FAILED = "LLM_ALL_RETRIES_FAILED"
    PIPELINE_ERROR = "PIPELINE_ERROR"
    PARAGRAPH_NOT_FOUND = "PARAGRAPH_NOT_FOUND"


class AgentError(Exception):
    """Base exception for the course agent."""

    def __init__(self, message: str, code: str = ErrorCode.PIPELINE_ERROR, details: dict | None = None):
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details or {}


class IngestionError(AgentError):
    """Raised when input parsing fails."""

    def __init__(self, message: str, details: dict | None = None):
        super().__init__(message, code=ErrorCode.INGESTION_FAILED, details=details)


class LLMError(AgentError):
    """Raised when LLM calls fail."""

    def __init__(self, message: str, code: str = ErrorCode.LLM_UNAVAILABLE, details: dict | None = None):
        super().__init__(message, code=code, details=details)


def agent_http_exception(error: AgentError, status_code: int = 500) -> HTTPException:
    """Convert an AgentError into a FastAPI HTTPException with structured body."""
    return HTTPException(
        status_code=status_code,
        detail={
            "error": error.code,
            "message": error.message,
            "details": error.details,
        },
    )
