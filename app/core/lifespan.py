
from contextlib import asynccontextmanager
import logging
from pathlib import Path

from fastapi import FastAPI

from app.core.config import get_settings
from app.core.runtime_checks import check_storage
from app.db.session import engine


logger = logging.getLogger("exceptionops.lifecycle")


def initialize_document_storage() -> Path:
    """
    Create the configured document directory if necessary.

    The application cannot safely accept document uploads if this
    directory is unavailable, so startup fails clearly in that case.
    """
    settings = get_settings()
    storage_path = Path(settings.document_storage_dir).expanduser()

    try:
        storage_path.mkdir(parents=True, exist_ok=True)
        storage_path = storage_path.resolve()
    except OSError as exc:
        logger.critical(
            "Document storage initialization failed",
            extra={
                "exception_type": type(exc).__name__,
            },
        )
        raise RuntimeError(
            "Document storage could not be initialized."
        ) from exc

    if not check_storage(settings):
        logger.critical(
            "Document storage is not writable",
            extra={"storage_available": False},
        )
        raise RuntimeError(
            "Document storage is not writable."
        )

    logger.info(
        "Document storage initialized",
        extra={"storage_available": True},
    )

    return storage_path


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifecycle.

    Startup:
      - Initialize and verify local document storage.

    Shutdown:
      - Dispose the SQLAlchemy connection pool.
    """
    settings = get_settings()

    logger.info(
        "Application startup initiated",
        extra={
            "environment": settings.app_env,
            "application": settings.app_name,
        },
    )

    storage_path = initialize_document_storage()
    app.state.document_storage_path = str(storage_path)

    logger.info("Application startup completed")

    try:
        yield
    finally:
        logger.info("Application shutdown initiated")

        try:
            engine.dispose()
            logger.info("Database connection pool disposed")
        except Exception as exc:
            logger.error(
                "Database connection pool disposal failed",
                extra={
                    "exception_type": type(exc).__name__,
                },
            )

        logger.info("Application shutdown completed")
