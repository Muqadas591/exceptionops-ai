
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

from app.core.config import get_settings
from app.core.security_headers import apply_security_headers


request_id_context: contextvars.ContextVar[str] = (
    contextvars.ContextVar("request_id", default="-")
)

REQUEST_ID_HEADER = "X-Request-ID"

REQUEST_ID_PATTERN = re.compile(
    r"^[A-Za-z0-9._-]{1,128}$"
)


class RequestContextFilter(logging.Filter):
    """Attach the active request ID to each log record."""

    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, "request_id"):
            record.request_id = request_id_context.get()

        return True


class JSONFormatter(logging.Formatter):
    """Format application log records as JSON."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(
                timezone.utc
            ).isoformat(),

            "level": record.levelname,

            "logger": record.name,

            "message": record.getMessage(),

            "request_id": getattr(
                record,
                "request_id",
                request_id_context.get(),
            ),
        }

        reserved = set(
            logging.makeLogRecord({}).__dict__.keys()
        )

        for key, value in record.__dict__.items():
            if key in reserved or key in payload:
                continue

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

    Logs go to stdout/stderr so local terminals and hosting
    platforms can capture them.
    """
    root_logger = logging.getLogger()

    handler = logging.StreamHandler()

    handler.addFilter(
        RequestContextFilter()
    )

    if environment.strip().lower() == "production":
        handler.setFormatter(
            JSONFormatter()
        )
    else:
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s %(levelname)s "
                "[%(name)s] [request_id=%(request_id)s] "
                "%(message)s"
            )
        )

    root_logger.handlers.clear()

    root_logger.addHandler(handler)

    root_logger.setLevel(logging.INFO)

    logging.getLogger(
        "uvicorn.access"
    ).setLevel(logging.WARNING)


class RequestContextMiddleware(BaseHTTPMiddleware):
    """
    Assign a request ID, apply security headers,
    and record the outcome of every HTTP request.
    """

    async def dispatch(
        self,
        request: Request,
        call_next,
    ) -> Response:

        settings = get_settings()

        supplied_id = request.headers.get(
            REQUEST_ID_HEADER,
            "",
        )

        if REQUEST_ID_PATTERN.fullmatch(supplied_id):
            request_id = supplied_id
        else:
            request_id = str(uuid.uuid4())

        context_token = request_id_context.set(
            request_id
        )

        started_at = time.perf_counter()

        logger = logging.getLogger(
            "exceptionops.api"
        )

        try:
            response = await call_next(request)

            duration_ms = round(
                (time.perf_counter() - started_at) * 1000,
                2,
            )

            response.headers[REQUEST_ID_HEADER] = (
                request_id
            )

            apply_security_headers(
                response,
                request,
                is_production=settings.is_production,
                api_prefix=settings.api_v1_prefix,
            )

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

            response = JSONResponse(
                status_code=500,
                content={
                    "detail": "Internal server error.",
                    "request_id": request_id,
                },
                headers={
                    REQUEST_ID_HEADER: request_id,
                },
            )

            apply_security_headers(
                response,
                request,
                is_production=settings.is_production,
                api_prefix=settings.api_v1_prefix,
            )

            return response

        finally:
            request_id_context.reset(
                context_token
            )
