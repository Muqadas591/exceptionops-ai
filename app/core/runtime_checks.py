
import logging
import tempfile
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import Settings


logger = logging.getLogger("exceptionops.runtime")


def check_database(db: Session) -> bool:
    """
    Return True if the database can execute a simple query.

    Failed sessions are rolled back so they are not left in a
    failed transaction state.
    """
    try:
        db.execute(text("SELECT 1"))
        return True

    except SQLAlchemyError as exc:
        try:
            db.rollback()
        except SQLAlchemyError:
            logger.warning(
                "Database rollback after health-check failure failed"
            )

        logger.warning(
            "Database runtime check failed",
            extra={
                "exception_type": type(exc).__name__,
                "dependency": "database",
            },
        )
        return False


def check_storage(settings: Settings) -> bool:
    """
    Verify that the document storage directory exists and is writable.

    A temporary probe file is created and removed. No existing
    document is opened or changed.
    """
    storage_path = Path(
        settings.document_storage_dir
    ).expanduser()
    probe_path = None

    try:
        if not storage_path.exists():
            return False

        if not storage_path.is_dir():
            return False

        with tempfile.NamedTemporaryFile(
            mode="wb",
            prefix=".exceptionops-health-",
            suffix=".tmp",
            dir=storage_path,
            delete=False,
        ) as probe:
            probe.write(b"exceptionops-storage-health-check")
            probe.flush()
            probe_path = Path(probe.name)

        probe_path.unlink(missing_ok=True)
        return True

    except OSError as exc:
        logger.warning(
            "Document storage runtime check failed",
            extra={
                "exception_type": type(exc).__name__,
                "dependency": "document_storage",
            },
        )

        if probe_path is not None:
            try:
                probe_path.unlink(missing_ok=True)
            except OSError:
                logger.error(
                    "Could not remove storage health-check probe file"
                )

        return False
