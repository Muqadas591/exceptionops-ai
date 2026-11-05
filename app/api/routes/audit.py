from datetime import datetime

from fastapi import (
    APIRouter,
    Depends,
    Query,
    Response,
)
from sqlalchemy.orm import Session

from app.core.authorization import require_audit_reader
from app.db.session import get_db
from app.schemas.audit import AuditEventRead
from app.services.audit_service import list_audit_events


router = APIRouter(tags=["Audit Trail"])


@router.get(
    "/audit/events",
    response_model=list[AuditEventRead],
)
def read_audit_events(
    response: Response,
    event_type: str | None = Query(
        default=None,
        max_length=100,
    ),
    entity_type: str | None = Query(
        default=None,
        max_length=100,
    ),
    actor_id: str | None = Query(
        default=None,
        max_length=100,
    ),
    document_id: int | None = Query(
        default=None,
        ge=1,
    ),
    workflow_run_id: int | None = Query(
        default=None,
        ge=1,
    ),
    review_id: int | None = Query(
        default=None,
        ge=1,
    ),
    action_id: int | None = Query(
        default=None,
        ge=1,
    ),
    search: str | None = Query(
        default=None,
        max_length=200,
    ),
    from_datetime: datetime | None = None,
    to_datetime: datetime | None = None,
    limit: int = Query(
        default=50,
        ge=1,
        le=100,
    ),
    offset: int = Query(
        default=0,
        ge=0,
    ),
    db: Session = Depends(get_db),
    actor: str = Depends(require_audit_reader),
):
    if (
        from_datetime is not None
        and to_datetime is not None
        and from_datetime > to_datetime
    ):
        from fastapi import HTTPException

        raise HTTPException(
            status_code=422,
            detail="from_datetime cannot be later than to_datetime.",
        )

    events, total = list_audit_events(
        db=db,
        event_type=event_type,
        entity_type=entity_type,
        actor_id=actor_id,
        document_id=document_id,
        workflow_run_id=workflow_run_id,
        review_id=review_id,
        action_id=action_id,
        search=search,
        from_datetime=from_datetime,
        to_datetime=to_datetime,
        limit=limit,
        offset=offset,
    )

    response.headers["X-Total-Count"] = str(total)
    response.headers["X-Page-Limit"] = str(limit)
    response.headers["X-Page-Offset"] = str(offset)
    response.headers["X-Has-More"] = str(
        offset + len(events) < total
    ).lower()

    return events