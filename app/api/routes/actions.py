from typing import Annotated

from fastapi import APIRouter, Depends, Header, Query
from sqlalchemy.orm import Session

from app.core.authorization import require_action_operator
from app.db.session import get_db
from app.models.action_execution import ActionExecution
from app.schemas.action_execution import (
    ActionExecutionRead,
    ActionReconciliationRequest,
    ActionRequest,
)
from app.services.action_execution_service import (
    execute_review_action,
    get_action,
    list_recovery_actions,
    list_review_actions,
    reconcile_action,
    retry_action,
)


router = APIRouter(tags=["Action Connectors"])


@router.post(
    "/reviews/{review_id}/actions",
    response_model=ActionExecutionRead,
)
def create_review_action(
    review_id: int,
    request: ActionRequest,
    idempotency_key: Annotated[
        str,
        Header(
            alias="Idempotency-Key",
            min_length=16,
            max_length=128,
        ),
    ],
    db: Session = Depends(get_db),
    actor: str = Depends(require_action_operator),
):
    return execute_review_action(
        db=db,
        review_id=review_id,
        request=request,
        actor=actor,
        idempotency_key=idempotency_key,
    )


@router.get(
    "/actions/recovery/queue",
    response_model=list[ActionExecutionRead],
)
def read_action_recovery_queue(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    actor: str = Depends(require_action_operator),
):
    return list_recovery_actions(
        db,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/reviews/{review_id}/actions",
    response_model=list[ActionExecutionRead],
)
def read_review_actions(
    review_id: int,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    actor: str = Depends(require_action_operator),
):
    return list_review_actions(
        db=db,
        review_id=review_id,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/actions/{action_id}",
    response_model=ActionExecutionRead,
)
def read_action(
    action_id: int,
    db: Session = Depends(get_db),
    actor: str = Depends(require_action_operator),
):
    return get_action(db, action_id)


@router.post(
    "/actions/{action_id}/retry",
    response_model=ActionExecutionRead,
)
def retry_failed_action(
    action_id: int,
    db: Session = Depends(get_db),
    actor: str = Depends(require_action_operator),
):
    return retry_action(
        db=db,
        action_id=action_id,
        actor=actor,
    )


@router.post(
    "/actions/{action_id}/reconcile",
    response_model=ActionExecutionRead,
)
def reconcile_uncertain_action(
    action_id: int,
    request: ActionReconciliationRequest,
    db: Session = Depends(get_db),
    actor: str = Depends(require_action_operator),
):
    return reconcile_action(
        db=db,
        action_id=action_id,
        request=request,
        actor=actor,
    )