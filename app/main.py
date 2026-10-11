
from fastapi import FastAPI

from app.api.routes.health import router as health_router
from app.core.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()

    application = FastAPI(
        title=settings.app_name,
        description=(
            "An exception-first operations platform for invoice "
            "and supplier workflows."
        ),
        version="0.1.0",
        debug=settings.debug,
    )

    @application.get("/", tags=["Root"])
    def root() -> dict[str, str]:
        return {
            "application": settings.app_name,
            "status": "running",
            "docs": "/docs",
        }

    application.include_router(
        health_router,
        prefix=settings.api_v1_prefix,
    )

    return application


app = create_app()
