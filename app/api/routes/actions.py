from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.authorization import require_action_operator
from app.db.session import get_db
from app.schemas.action_execution import (
    ActionExecutionRead,
    ActionRequest,
)
from app.services.action_execution_service import (
    execute_review_action,
    get_action,
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
    db: Session = Depends(get_db),
    actor: str = Depends(require_action_operator),
):
    return execute_review_action(
        db=db,
        review_id=review_id,
        request=request,
        actor=actor,
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