
from __future__ import annotations

import contextvars
import json
import logging
import re
import time
import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response


request_id_context: contextvars.ContextVar[str] = (
    contextvars.ContextVar("request_id", default="-")
)

REQUEST_ID_HEADER = "X-Request-ID"

# Restrict caller-supplied request IDs to safe, predictable characters.
REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9._-]{1,128}$")


class RequestContextFilter(logging.Filter):
    """Attach the active request ID to each log record."""

    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, "request_id"):
            record.request_id = request_id_context.get()

        return True


class JSONFormatter(logging.Formatter):
    """Format application log records as one JSON object per line."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": getattr(
                record,
                "request_id",
                request_id_context.get(),
            ),
        }

        # Add explicitly supplied structured fields.
        reserved = set(
            logging.makeLogRecord({}).__dict__.keys()
        )

        for key, value in record.__dict__.items():
            if key not in reserved and key not in payload:
                if key.startswith("_"):
                    continue

                if isinstance(
                    value,
                    (str, int, float, bool),
                ) or value is None:
                    payload[key] = value

        if record.exc_info:
            payload["exception_type"] = (
                record.exc_info[0].__name__
                if record.exc_info[0]
                else "Exception"
            )

        return json.dumps(
            payload,
            ensure_ascii=False,
            default=str,
        )


def configure_logging(
    environment: str = "development",
) -> None:
    """
    Configure one application-wide logging handler.

    Logs are written to stdout/stderr through StreamHandler so that
    local terminals and hosting-platform log collectors can capture them.
    """
    root_logger = logging.getLogger()

    handler = logging.StreamHandler()
    handler.addFilter(RequestContextFilter())

    if environment.strip().lower() == "production":
        handler.setFormatter(JSONFormatter())
    else:
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s %(levelname)s "
                "[%(name)s] [request_id=%(request_id)s] "
                "%(message)s"
            )
        )

    # Avoid duplicate handlers when create_app() is called repeatedly
    # in tests or development.
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.INFO)

    # Keep third-party HTTP/database logs from becoming excessively noisy.
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Assign a request ID and record the outcome of every HTTP request."""

    async def dispatch(self, request: Request, call_next) -> Response:
        supplied_id = request.headers.get(REQUEST_ID_HEADER, "")

        if REQUEST_ID_PATTERN.fullmatch(supplied_id):
            request_id = supplied_id
        else:
            request_id = str(uuid.uuid4())

        context_token = request_id_context.set(request_id)
        started_at = time.perf_counter()

        logger = logging.getLogger("exceptionops.api")

        try:
            response = await call_next(request)

            duration_ms = round(
                (time.perf_counter() - started_at) * 1000,
                2,
            )

            response.headers[REQUEST_ID_HEADER] = request_id

            logger.info(
                "Request completed",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "duration_ms": duration_ms,
                },
            )

            return response

        except Exception as exc:
            duration_ms = round(
                (time.perf_counter() - started_at) * 1000,
                2,
            )

            logger.error(
                "Unhandled request exception",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": 500,
                    "duration_ms": duration_ms,
                    "exception_type": type(exc).__name__,
                },
            )

            return JSONResponse(
                status_code=500,
                content={
                    "detail": "Internal server error.",
                    "request_id": request_id,
                },
                headers={
                    REQUEST_ID_HEADER: request_id,
                },
            )

        finally:
            request_id_context.reset(context_token)
