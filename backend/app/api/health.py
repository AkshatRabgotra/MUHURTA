"""Health-check endpoint – verifies API + database connectivity."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db

router = APIRouter(tags=["health"])


@router.get("/health", response_model=dict[str, Any])
async def healthcheck(db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    """Return service health including database connectivity.

    Returns
    -------
    dict
        ``{"status": "healthy", "database": "connected"}`` on success, or
        ``{"status": "unhealthy", "database": "<error message>"}`` on failure.
    """
    try:
        await db.execute(text("SELECT 1"))
        db_status = "connected"
        status = "healthy"
    except Exception as exc:
        db_status = str(exc)
        status = "unhealthy"

    return {"status": status, "database": db_status}
