
from fastapi import FastAPI

from app.api.routes.documents import router as documents_router
from app.api.routes.evaluations import router as evaluations_router
from app.api.routes.extractions import router as extractions_router
from app.api.routes.health import router as health_router
from app.api.routes.workflows import router as workflows_router
from app.api.routes.reviews import router as reviews_router
from app.api.routes.actions import router as actions_router
from fastapi.middleware.cors import CORSMiddleware

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
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ],
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=[
            "Content-Type",
            "X-Reviewer-Token",
            "X-Action-Token",
        ],
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
