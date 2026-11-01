import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db
from app.schemas.health import HealthResponse, ReadinessResponse


router = APIRouter(tags=["Health"])

logger = logging.getLogger("exceptionops.health")


@router.get(
    "/health",
    response_model=HealthResponse,
)
def health_check() -> HealthResponse:
    """
    Liveness check.

    This endpoint confirms that the application process can respond.
    It deliberately does not require a database query.
    """
    settings = get_settings()

    return HealthResponse(
        status="ok",
        app_name=settings.app_name,
        environment=settings.app_env,
    )


@router.get(
    "/ready",
    response_model=ReadinessResponse,
)
def readiness_check(
    db: Session = Depends(get_db),
) -> ReadinessResponse:
    """
    Readiness check.

    A successful response means the application can reach its database.
    """
    try:
        db.execute(text("SELECT 1"))

    except SQLAlchemyError as exc:
        logger.error(
            "Database readiness check failed",
            extra={
                "exception_type": type(exc).__name__,
                "status_code": 503,
            },
        )

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is unavailable.",
        ) from exc

    return ReadinessResponse(
        status="ready",
        database="connected",
    )