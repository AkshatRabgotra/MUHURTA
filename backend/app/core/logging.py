"""Structlog configuration with JSON output and request-ID injection."""

from __future__ import annotations

import logging
import sys

import structlog


def _add_request_id(
    logger: structlog.types.WrappedLogger,
    method_name: str,
    event_dict: structlog.types.EventDict,
) -> structlog.types.EventDict:
    """Inject the current request ID from contextvars (if set)."""
    # Import lazily to avoid circular imports at module level.
    from app.main import request_id_ctx  # noqa: WPS433

    rid = request_id_ctx.get("")
    if rid:
        event_dict["request_id"] = rid
    return event_dict


def setup_logging(*, json: bool = True, level: str = "INFO") -> None:
    """Configure structlog for the application.

    Parameters
    ----------
    json:
        Emit JSON lines when *True* (production), coloured console output
        when *False* (development).
    level:
        Root log level.
    """
    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        _add_request_id,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]

    if json:
        renderer: structlog.types.Processor = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer()

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)
