
import logging

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.api.routes.actions import router as actions_router
from app.api.routes.documents import router as documents_router
from app.api.routes.evaluations import router as evaluations_router
from app.api.routes.extractions import router as extractions_router
from app.api.routes.health import router as health_router
from app.api.routes.reviews import router as reviews_router
from app.api.routes.workflows import router as workflows_router
from app.core.config import get_settings
from app.core.observability import (
    RequestContextMiddleware,
    configure_logging,
    request_id_context,
)


def create_app() -> FastAPI:
    settings = get_settings()

    # Configure application-wide logging.
    configure_logging(environment=settings.app_env)

    docs_enabled = settings.docs_enabled

    app = FastAPI(
        title=settings.app_name,
        description=(
            "An invoice and supplier exception resolution platform "
            "for document ingestion, extraction, validation, and "
            "business-rule evaluation."
        ),
        version="0.4.0",
        debug=settings.debug,
        docs_url="/docs" if docs_enabled else None,
        redoc_url="/redoc" if docs_enabled else None,
        openapi_url="/openapi.json" if docs_enabled else None,
    )

    # Handle request validation errors without exposing submitted values.
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request,
        exc: RequestValidationError,
    ):
        request_id = request_id_context.get()

        logging.getLogger("exceptionops.validation").warning(
            "Request validation failed",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status_code": 422,
                "validation_error_count": len(exc.errors()),
            },
        )

        errors = [
            {
                "type": error.get(
                    "type",
                    "validation_error",
                ),
                "loc": list(error.get("loc", ())),
                "msg": error.get(
                    "msg",
                    "Invalid request.",
                ),
            }
            for error in exc.errors()
        ]

        return JSONResponse(
            status_code=422,
            content={
                "detail": errors,
                "request_id": request_id,
            },
            headers={
                "X-Request-ID": request_id,
            },
        )

    # Reject requests with unexpected Host headers in production.
    # Development retains the usual local hostnames.
    if settings.is_production:
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=settings.allowed_hosts_list,
        )

    # CORS configuration.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=False,
        allow_methods=[
            "GET",
            "POST",
            "PATCH",
            "DELETE",
            "OPTIONS",
        ],
        allow_headers=[
            "Authorization",
            "Content-Type",
            "X-Request-ID",
            "Idempotency-Key",

            # Temporary compatibility with the existing Stage 6 frontend.
            # Remove these after the Stage 8.1 frontend migration.
            "X-Reviewer-Token",
            "X-Action-Token",
        ],
        expose_headers=[
     "X-Request-ID",
    "X-Total-Count",
    "X-Page-Limit",
    "X-Page-Offset",
    "X-Has-More",
    ],
    )

    # Register request context middleware after CORS middleware.
    app.add_middleware(RequestContextMiddleware)

    @app.get("/", tags=["Root"])
    def root():
        return {
            "application": settings.app_name,
            "status": "running",
            "docs": "/docs" if docs_enabled else None,
        }

    # Register existing API routers using the configured API prefix.
    app.include_router(
        health_router,
        prefix=settings.api_v1_prefix,
    )

    app.include_router(
        documents_router,
        prefix=settings.api_v1_prefix,
    )

    app.include_router(
        extractions_router,
        prefix=settings.api_v1_prefix,
    )

    app.include_router(
        evaluations_router,
        prefix=settings.api_v1_prefix,
    )

    app.include_router(
        workflows_router,
        prefix=settings.api_v1_prefix,
    )

    app.include_router(
        reviews_router,
        prefix=settings.api_v1_prefix,
    )

    app.include_router(
        actions_router,
        prefix=settings.api_v1_prefix,
    )

    return app


app = create_app()
