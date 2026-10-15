
from fastapi import FastAPI

from app.api.routes.documents import router as documents_router
from app.api.routes.evaluations import router as evaluations_router
from app.api.routes.extractions import router as extractions_router
from app.api.routes.health import router as health_router
from app.api.routes.workflows import router as workflows_router
from app.api.routes.reviews import router as reviews_router
from app.api.routes.actions import router as actions_router
def create_app() -> FastAPI:
    app = FastAPI(
        title="ExceptionOps AI",
        description=(
            "An invoice and supplier exception resolution platform "
            "for document ingestion, extraction, validation, and "
            "business-rule evaluation."
        ),
        version="0.4.0",
    )

    # Root endpoint
    @app.get("/", tags=["Root"])
    def root():
        return {
            "application": "ExceptionOps AI",
            "status": "running",
            "docs": "/docs",
        }

    # Register API routers
    app.include_router(health_router, prefix="/api/v1")
    app.include_router(documents_router, prefix="/api/v1")
    app.include_router(extractions_router, prefix="/api/v1")
    app.include_router(evaluations_router, prefix="/api/v1")
    app.include_router(workflows_router, prefix="/api/v1")
    app.include_router(reviews_router, prefix="/api/v1")
    app.include_router(actions_router, prefix="/api/v1")


    return app


app = create_app()
