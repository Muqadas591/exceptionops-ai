from fastapi import APIRouter, Depends, Header, Query, Response
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.workflow import WorkflowRead, WorkflowResolveRequest
from app.services.workflow_service import (
    advance_workflow,
    cancel_workflow,
    create_workflow,
    get_latest_document_workflow,
    get_workflow,
    list_workflows,
    resolve_workflow,
    retry_workflow,
)
from app.core.authorization import require_reviewer

router = APIRouter(
    tags=["Workflow Orchestration"],
    dependencies=[Depends(require_reviewer)],
)


@router.post(
    "/documents/{document_id}/workflow",
    response_model=WorkflowRead,
)
def start_document_workflow(
    document_id: int,
    idempotency_key: str | None = Header(
        default=None,
        alias="Idempotency-Key",
    ),
    db: Session = Depends(get_db),
):
    return create_workflow(
        db=db,
        document_id=document_id,
        idempotency_key=idempotency_key,
    )


@router.get(
    "/documents/{document_id}/workflow",
    response_model=WorkflowRead,
)
def read_document_workflow(
    document_id: int,
    db: Session = Depends(get_db),
):
    return get_latest_document_workflow(db, document_id)


@router.get(
    "/workflows",
    response_model=list[WorkflowRead],
)
def read_workflows(
    response: Response,
    status: str | None = Query(
        default=None,
        max_length=30,
    ),
    document_id: int | None = Query(
        default=None,
        ge=1,
    ),
    limit: int = Query(
        default=20,
        ge=1,
        le=100,
    ),
    offset: int = Query(
        default=0,
        ge=0,
    ),
    db: Session = Depends(get_db),
):
    workflows, total = list_workflows(
        db,
        status=status,
        document_id=document_id,
        limit=limit,
        offset=offset,
    )
    response.headers["X-Total-Count"] = str(total)
    response.headers["X-Page-Limit"] = str(limit)
    response.headers["X-Page-Offset"] = str(offset)
    response.headers["X-Has-More"] = str(
        offset + len(workflows) < total
    ).lower()
    return workflows


@router.get(
    "/workflows/{workflow_id}",
    response_model=WorkflowRead,
)
def read_workflow(
    workflow_id: int,
    db: Session = Depends(get_db),
):
    return get_workflow(db, workflow_id)


@router.post(
    "/workflows/{workflow_id}/advance",
    response_model=WorkflowRead,
)
def advance_document_workflow(
    workflow_id: int,
    db: Session = Depends(get_db),
):
    return advance_workflow(db, workflow_id)


@router.post(
    "/workflows/{workflow_id}/retry",
    response_model=WorkflowRead,
)
def retry_document_workflow(
    workflow_id: int,
    db: Session = Depends(get_db),
):
    return retry_workflow(db, workflow_id)


@router.post(
    "/workflows/{workflow_id}/resolve",
    response_model=WorkflowRead,
)
def manually_resolve_workflow(
    workflow_id: int,
    request: WorkflowResolveRequest,
    db: Session = Depends(get_db),
):
    return resolve_workflow(
        db=db,
        workflow_id=workflow_id,
        note=request.note,
    )


@router.post(
    "/workflows/{workflow_id}/cancel",
    response_model=WorkflowRead,
)
def cancel_document_workflow(
    workflow_id: int,
    db: Session = Depends(get_db),
):
    return cancel_workflow(db, workflow_id)