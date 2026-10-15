from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.workflow import WorkflowRead, WorkflowResolveRequest
from app.services.workflow_service import (
    advance_workflow,
    cancel_workflow,
    create_workflow,
    get_latest_document_workflow,
    get_workflow,
    resolve_workflow,
    retry_workflow,
)


router = APIRouter(tags=["Workflow Orchestration"])


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