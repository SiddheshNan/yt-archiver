"""
Custom exception types and FastAPI exception handlers.

All API errors return a consistent JSON structure:
{
    "error": {
        "code": "NOT_FOUND",
        "message": "Video not found",
        "details": {}           // optional
    }
}
"""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.logging_config import get_logger

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Custom exceptions
# ---------------------------------------------------------------------------


class AppError(Exception):
    """Base application error."""

    def __init__(
        self,
        message: str,
        code: str = "INTERNAL_ERROR",
        status_code: int = 500,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)


class NotFoundError(AppError):
    """Resource not found."""

    def __init__(self, resource: str, identifier: str) -> None:
        super().__init__(
            message=f"{resource} not found: {identifier}",
            code="NOT_FOUND",
            status_code=404,
            details={"resource": resource, "identifier": identifier},
        )


class DuplicateError(AppError):
    """Duplicate resource."""

    def __init__(self, resource: str, identifier: str) -> None:
        super().__init__(
            message=f"{resource} already exists: {identifier}",
            code="DUPLICATE",
            status_code=409,
            details={"resource": resource, "identifier": identifier},
        )


class DownloadError(AppError):
    """Video download failure."""

    def __init__(self, message: str, video_id: str | None = None) -> None:
        super().__init__(
            message=message,
            code="DOWNLOAD_ERROR",
            status_code=500,
            details={"video_id": video_id} if video_id else {},
        )


class ValidationError(AppError):
    """Invalid input."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            status_code=422,
            details=details or {},
        )


class ToolError(AppError):
    """External tool (yt-dlp, ffmpeg) error."""

    def __init__(self, tool: str, message: str) -> None:
        super().__init__(
            message=f"{tool} error: {message}",
            code="TOOL_ERROR",
            status_code=500,
            details={"tool": tool},
        )


# ---------------------------------------------------------------------------
# Exception handlers
# ---------------------------------------------------------------------------


def _error_response(status_code: int, code: str, message: str, details: dict) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": code,
                "message": message,
                "details": details,
            }
        },
    )


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    """Handle all AppError subclasses."""
    logger.warning(
        "app_error",
        code=exc.code,
        message=exc.message,
        details=exc.details,
        path=str(request.url),
    )
    return _error_response(exc.status_code, exc.code, exc.message, exc.details)


async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all for unhandled exceptions."""
    logger.error(
        "unhandled_error",
        error=str(exc),
        error_type=type(exc).__name__,
        path=str(request.url),
        exc_info=True,
    )
    return _error_response(500, "INTERNAL_ERROR", "An unexpected error occurred", {})


def register_exception_handlers(app: FastAPI) -> None:
    """Register all exception handlers on the FastAPI app."""
    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(Exception, unhandled_error_handler)
