from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.observability import request_id_context
from app.models.audit_event import AuditEvent


def record_audit_event(
    db: Session,
    *,
    event_type: str,
    entity_type: str,
    entity_id: int | str | None,
    description: str,
    actor_type: str = "system",
    actor_id: str | None = None,
    document_id: int | None = None,
    workflow_run_id: int | None = None,
    review_id: int | None = None,
    action_id: int | None = None,
    metadata: dict | None = None,
) -> AuditEvent:
    """
    Add an audit event to the current transaction.

    The caller is responsible for committing the transaction. This
    keeps the business change and its audit event in the same commit.
    """
    event_metadata = dict(metadata or {})
    request_id = request_id_context.get()
    if request_id != "-":
        event_metadata.setdefault("request_id", request_id)

    event = AuditEvent(
        event_type=event_type,
        entity_type=entity_type,
        entity_id=(
            str(entity_id)
            if entity_id is not None
            else None
        ),
        actor_type=actor_type,
        actor_id=actor_id,
        description=description,
        document_id=document_id,
        workflow_run_id=workflow_run_id,
        review_id=review_id,
        action_id=action_id,
        event_metadata=event_metadata,
    )

    db.add(event)
    return event


def list_audit_events(
    db: Session,
    *,
    event_type: str | None = None,
    entity_type: str | None = None,
    actor_id: str | None = None,
    document_id: int | None = None,
    workflow_run_id: int | None = None,
    review_id: int | None = None,
    action_id: int | None = None,
    search: str | None = None,
    from_datetime: datetime | None = None,
    to_datetime: datetime | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[AuditEvent], int]:
    query = db.query(AuditEvent)

    if event_type:
        query = query.filter(
            AuditEvent.event_type == event_type
        )

    if entity_type:
        query = query.filter(
            AuditEvent.entity_type == entity_type
        )

    if actor_id:
        query = query.filter(
            AuditEvent.actor_id == actor_id
        )

    if document_id is not None:
        query = query.filter(
            AuditEvent.document_id == document_id
        )

    if workflow_run_id is not None:
        query = query.filter(
            AuditEvent.workflow_run_id == workflow_run_id
        )

    if review_id is not None:
        query = query.filter(
            AuditEvent.review_id == review_id
        )

    if action_id is not None:
        query = query.filter(
            AuditEvent.action_id == action_id
        )

    if search:
        query = query.filter(
            AuditEvent.description.ilike(
                f"%{search.strip()}%"
            )
        )

    if from_datetime:
        query = query.filter(
            AuditEvent.created_at >= from_datetime
        )

    if to_datetime:
        query = query.filter(
            AuditEvent.created_at <= to_datetime
        )

    total = (
        query.with_entities(
            func.count(AuditEvent.id)
        ).scalar()
        or 0
    )

    events = (
        query
        .order_by(
            AuditEvent.created_at.desc(),
            AuditEvent.id.desc(),
        )
        .limit(limit)
        .offset(offset)
        .all()
    )

    return events, int(total)