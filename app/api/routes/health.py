
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.runtime_checks import (
    check_database,
    check_storage,
)
from app.db.session import get_db
from app.schemas.health import (
    HealthResponse,
    ReadinessResponse,
)


router = APIRouter(tags=["Health"])

logger = logging.getLogger("exceptionops.health")


@router.get(
    "/health",
    response_model=HealthResponse,
)
def health_check() -> HealthResponse:
    """
    Liveness check.

    Confirms that the application process can respond.
    Does not depend on PostgreSQL or document storage.
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

    The application is ready only when both required dependencies
    are operational.
    """
    settings = get_settings()

    database_available = check_database(db)
    storage_available = check_storage(settings)

    if not database_available or not storage_available:
        logger.warning(
            "Application readiness check failed",
            extra={
                "database_available": database_available,
                "storage_available": storage_available,
                "status_code": 503,
            },
        )

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "message": "Application dependencies are unavailable.",
                "database": (
                    "connected"
                    if database_available
                    else "unavailable"
                ),
                "storage": (
                    "writable"
                    if storage_available
                    else "unavailable"
                ),
            },
        )

    return ReadinessResponse(
        status="ready",
        database="connected",
        storage="writable",
    )
