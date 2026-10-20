"""Consistent error handling for the Muhurta Planner API.

All domain errors should raise ``AppError``; the registered exception handlers
convert them into a uniform JSON envelope::

    {"error": {"code": "NOT_FOUND", "message": "Resource not found"}}
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


import structlog

logger = structlog.get_logger(__name__)


# ── Common error codes ───────────────────────────────────────────────────
class ErrorCode(StrEnum):
    """Well-known error codes used across the application."""

    BAD_REQUEST = "BAD_REQUEST"
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    NOT_FOUND = "NOT_FOUND"
    CONFLICT = "CONFLICT"
    VALIDATION = "VALIDATION_ERROR"
    INTERNAL = "INTERNAL_ERROR"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    LLM_ERROR = "LLM_ERROR"
    PANCHANG_ERROR = "PANCHANG_ERROR"


# ── Mapping from error code to HTTP status ───────────────────────────────
_CODE_TO_STATUS: dict[ErrorCode, int] = {
    ErrorCode.BAD_REQUEST: 400,
    ErrorCode.UNAUTHORIZED: 401,
    ErrorCode.FORBIDDEN: 403,
    ErrorCode.NOT_FOUND: 404,
    ErrorCode.CONFLICT: 409,
    ErrorCode.VALIDATION: 422,
    ErrorCode.INTERNAL: 500,
    ErrorCode.SERVICE_UNAVAILABLE: 503,
    ErrorCode.LLM_ERROR: 502,
    ErrorCode.PANCHANG_ERROR: 500,
}


# ── Application exception ───────────────────────────────────────────────
class AppError(Exception):
    """Raise this for any domain-level error.

    Parameters
    ----------
    code:
        A member of ``ErrorCode`` (or any string).
    message:
        Human-readable explanation.
    status_code:
        Optional HTTP status override; inferred from *code* when omitted.
    extra:
        Additional context merged into the JSON body.
    """

    def __init__(
        self,
        code: ErrorCode | str,
        message: str,
        *,
        status_code: int | None = None,
        extra: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code or _CODE_TO_STATUS.get(
            ErrorCode(code) if isinstance(code, str) and code in ErrorCode.__members__ else ErrorCode.INTERNAL,
            500,
        )
        self.extra = extra or {}


# ── Helpers ──────────────────────────────────────────────────────────────
def _error_body(code: str, message: str, extra: dict[str, Any] | None = None) -> dict[str, Any]:
    body: dict[str, Any] = {"code": code, "message": message}
    if extra:
        body.update(extra)
    return {"error": body}


# ── Exception handlers ──────────────────────────────────────────────────
async def _handle_app_error(request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=_error_body(str(exc.code), exc.message, exc.extra),
    )


async def _handle_unhandled(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled server exception", path=request.url.path, error=str(exc))
    return JSONResponse(
        status_code=500,
        content=_error_body(ErrorCode.INTERNAL, f"An unexpected error occurred: {exc}"),
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Register all custom exception handlers on the FastAPI app."""
    app.add_exception_handler(AppError, _handle_app_error)  # type: ignore[arg-type]
    app.add_exception_handler(Exception, _handle_unhandled)  # type: ignore[arg-type]
