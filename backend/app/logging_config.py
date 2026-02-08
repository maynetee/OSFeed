"""Structured logging configuration using structlog."""

import logging
import sys

import structlog

from app.config import get_settings


class Suppress401Filter(logging.Filter):
    """Filter that drops uvicorn access log entries with 401 status codes."""

    def filter(self, record: logging.LogRecord) -> bool:
        if record.args and isinstance(record.args, tuple) and len(record.args) >= 5:
            status_code = record.args[4]
            if isinstance(status_code, int) and status_code == 401:
                return False
        return True


def configure_logging() -> None:
    """Configure structlog with JSON output for production, console for development."""
    settings = get_settings()
    is_production = settings.app_env == "production"
    log_level = logging.DEBUG if settings.app_debug else logging.INFO

    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    if is_production:
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
        foreign_pre_chain=shared_processors,
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(log_level)

    # Suppress 401 responses from uvicorn access log to reduce noise
    uvicorn_access = logging.getLogger("uvicorn.access")
    uvicorn_access.addFilter(Suppress401Filter())
