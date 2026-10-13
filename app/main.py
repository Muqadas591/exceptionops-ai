
from fastapi import FastAPI

from app.api.routes.documents import router as documents_router
from app.api.routes.evaluations import router as evaluations_router
from app.api.routes.extractions import router as extractions_router
from app.api.routes.health import router as health_router


def create_app() -> FastAPI:
    """
    Create the ExceptionOps AI application.

    API version 0.4.0 includes:
    - Phase 1: core API and database foundation
    - Phase 2: document ingestion
    - Phase 3: invoice extraction
    - Phase 4: business evaluation and risk scoring
    """
    app = FastAPI(
        title="ExceptionOps AI",
        description=(
            "An invoice and supplier exception resolution platform "
            "for document ingestion, extraction, validation, and "
            "business-rule evaluation."
        ),
        version="0.4.0",
    )

    # Phase 1: Health endpoint
    app.include_router(
        health_router,
        prefix="/api/v1",
    )

    # Phase 2: Document ingestion and retrieval
    app.include_router(
        documents_router,
        prefix="/api/v1",
    )

    # Phase 3: Invoice extraction
    app.include_router(
        extractions_router,
        prefix="/api/v1",
    )

    # Phase 4: Business rules and risk evaluation
    app.include_router(
        evaluations_router,
        prefix="/api/v1",
    )

    return app


app = create_app()
