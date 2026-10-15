from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.action_execution import ActionExecution
from app.models.human_review import HumanReview
from app.schemas.action_execution import ActionRequest
from app.services.action_connectors import execute_connector


def _get_action(
    db: Session,
    action_id: int,
) -> ActionExecution:
    action = (
        db.query(ActionExecution)
        .filter(ActionExecution.id == action_id)
        .first()
    )

    if action is None:
        raise HTTPException(
            status_code=404,
            detail=f"Action {action_id} was not found.",
        )

    return action


def _require_approved_review(
    db: Session,
    review_id: int,
) -> HumanReview:
    review = (
        db.query(HumanReview)
        .filter(HumanReview.id == review_id)
        .first()
    )

    if review is None:
        raise HTTPException(
            status_code=404,
            detail=f"Review {review_id} was not found.",
        )

    if review.status != "approved":
        raise HTTPException(
            status_code=409,
            detail="Action execution requires an approved review.",
        )

    return review


def _run_saved_action(
    db: Session,
    action: ActionExecution,
) -> ActionExecution:
    _require_approved_review(db, action.review_id)

    if action.status == "succeeded":
        raise HTTPException(
            status_code=409,
            detail="This action has already succeeded.",
        )

    action.status = "pending"
    action.attempt_count += 1
    action.last_error = None

    # Persist the attempt before invoking the connector.
    db.commit()
    db.refresh(action)

    try:
        outcome = execute_connector(
            action.action_type,
            action.request_payload,
        )

        action.result_payload = outcome.result

        if outcome.success:
            action.status = "succeeded"
            action.last_error = None
        else:
            action.status = "failed"
            action.last_error = (outcome.error or "Unknown error")[:4000]

    except Exception as exc:
        db.rollback()
        action = _get_action(db, action.id)
        action.status = "failed"
        action.last_error = str(exc)[:4000]

    db.commit()
    db.refresh(action)
    return action


def execute_review_action(
    db: Session,
    review_id: int,
    request: ActionRequest,
    actor: str,
) -> ActionExecution:
    review = _require_approved_review(db, review_id)

    payload: dict = {}

    if request.action_type == "email_draft":
        payload = {
            "recipient": request.recipient,
            "subject": request.subject,
            "message": request.message,
        }

    elif request.action_type == "accounting_simulation":
        payload = {
            "invoice_reference": (
                f"document-{review.workflow_run_id}"
            ),
        }

    elif request.action_type == "webhook_simulation":
        payload = {
            "event_name": "invoice.review.approved",
            "event_payload": {
                "review_id": review.id,
                "workflow_run_id": review.workflow_run_id,
                "approved_by": review.decided_by,
            },
        }

    action = ActionExecution(
        review_id=review.id,
        action_type=request.action_type,
        status="pending",
        attempt_count=0,
        request_payload=payload,
        executed_by=actor,
    )

    db.add(action)
    db.commit()
    db.refresh(action)

    return _run_saved_action(db, action)


def get_action(
    db: Session,
    action_id: int,
) -> ActionExecution:
    return _get_action(db, action_id)


def retry_action(
    db: Session,
    action_id: int,
    actor: str,
) -> ActionExecution:
    action = _get_action(db, action_id)

    _require_approved_review(db, action.review_id)

    if action.status != "failed":
        raise HTTPException(
            status_code=409,
            detail="Only failed actions can be retried.",
        )

    # Preserve the original execution identity for audit purposes;
    # the retrying operator is recorded in the result.
    action.result_payload = {
        **(action.result_payload or {}),
        "retry_requested_by": actor,
    }

    db.commit()
    db.refresh(action)

    return _run_saved_action(db, action)