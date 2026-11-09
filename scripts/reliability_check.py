
import json
import logging
import sys

from app.core.config import get_settings
from app.core.runtime_checks import (
    check_database,
    check_storage,
)
from app.db.session import SessionLocal


logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s %(message)s",
)

logger = logging.getLogger("exceptionops.reliability")


def run_checks() -> dict:
    settings = get_settings()

    db = SessionLocal()

    try:
        database_ok = check_database(db)
    finally:
        db.close()

    storage_ok = check_storage(settings)

    result = {
        "application": settings.app_name,
        "environment": settings.app_env,
        "database": (
            "connected" if database_ok else "unavailable"
        ),
        "storage": (
            "writable" if storage_ok else "unavailable"
        ),
        "status": (
            "healthy"
            if database_ok and storage_ok
            else "degraded"
        ),
    }

    return result


def main() -> int:
    try:
        result = run_checks()
    except Exception as exc:
        logger.error(
            "Reliability diagnostic could not complete",
            extra={"exception_type": type(exc).__name__},
        )
        print(
            json.dumps(
                {
                    "status": "error",
                    "message": "Reliability diagnostic failed.",
                },
                indent=2,
            )
        )
        return 1

    print(json.dumps(result, indent=2))

    if result["status"] != "healthy":
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
