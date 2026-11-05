
from __future__ import annotations

import hashlib
import json
import logging
from typing import Any

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.action_execution import ActionExecution
from app.models.human_review import HumanReview
from app.models.workflow_run import WorkflowRun
from app.schemas.action_execution import (
    ActionReconciliationRequest,
    ActionRequest,
)
from app.services.audit_service import record_audit_event
from app.services.action_connectors import execute_connector


logger = logging.getLogger("exceptionops.actions")


def _get_action(
    db: Session,
    action_id: int,
    *,
    lock: bool = False,
) -> ActionExecution:
    query = db.query(ActionExecution).filter(
        ActionExecution.id == action_id
    )

    if lock:
        query = query.with_for_update()

    action = query.first()

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


def _build_payload(
    request: ActionRequest,
    review: HumanReview,
) -> dict[str, Any]:
    if request.action_type == "email_draft":
        return {
            "recipient": request.recipient,
            "subject": request.subject,
            "message": request.message,
        }

    if request.action_type == "accounting_simulation":
        return {
            "invoice_reference": f"document-{review.workflow_run_id}",
        }

    if request.action_type == "webhook_simulation":
        return {
            "event_name": "invoice.review.approved",
            "event_payload": {
                "review_id": review.id,
                "workflow_run_id": review.workflow_run_id,
                "approved_by": review.decided_by,
            },
        }

    # Pydantic should reject unsupported action types before this point.
    raise HTTPException(
        status_code=422,
        detail="Unsupported action type.",
    )


def _fingerprint(
    action_type: str,
    payload: dict[str, Any],
) -> str:
    canonical_payload = json.dumps(
        {
            "action_type": action_type,
            "payload": payload,
        },
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )

    return hashlib.sha256(
        canonical_payload.encode("utf-8")
    ).hexdigest()


def _record_audit(
    db: Session,
    *,
    event_type: str,
    action: ActionExecution,
    actor: str,
    description: str,
    metadata: dict[str, Any] | None = None,
) -> None:
    review = (
        db.query(HumanReview)
        .filter(HumanReview.id == action.review_id)
        .first()
    )
    workflow = None
    if review is not None:
        workflow = (
            db.query(WorkflowRun)
            .filter(
                WorkflowRun.id == review.workflow_run_id
            )
            .first()
        )

    record_audit_event(
        db,
        event_type=event_type,
        entity_type="action_execution",
        entity_id=action.id,
        description=description,
        actor_type="operator",
        actor_id=actor,
        document_id=workflow.document_id if workflow else None,
        workflow_run_id=(
            review.workflow_run_id if review else None
        ),
        review_id=action.review_id,
        action_id=action.id,
        metadata=metadata,
    )


def _find_idempotent_action(
    db: Session,
    *,
    idempotency_key: str,
    request_fingerprint: str,
) -> ActionExecution | None:
    existing = (
        db.query(ActionExecution)
        .filter(
            ActionExecution.idempotency_key == idempotency_key
        )
        .first()
    )

    if existing is None:
        return None

    if existing.request_fingerprint != request_fingerprint:
        raise HTTPException(
            status_code=409,
            detail=(
                "This Idempotency-Key has already been used "
                "with a different action payload."
            ),
        )

    # Never execute the existing action again here. Return its recorded
    # state, including failed/uncertain states, for safe client recovery.
    return existing


def _run_saved_action(
    db: Session,
    action_id: int,
    *,
    actor: str,
) -> ActionExecution:
    # On PostgreSQL, this row lock serializes competing attempts for
    # the same action. A database uniqueness constraint independently
    # protects action creation from duplicate keys.
    action = _get_action(db, action_id, lock=True)

    if action.status == "succeeded":
        return action

    if action.status in {"in_progress", "uncertain"}:
        raise HTTPException(
            status_code=409,
            detail=(
                "This action is already running or has an uncertain "
                "outcome. Reconcile it before attempting execution."
            ),
        )

    if action.status not in {"pending", "failed"}:
        raise HTTPException(
            status_code=409,
            detail="This action is not eligible for execution.",
        )

    _require_approved_review(db, action.review_id)

    action.status = "in_progress"
    action.attempt_count += 1
    action.last_error = None

    _record_audit(
        db,
        event_type="action.execution_started",
        action=action,
        actor=actor,
        description="Action execution attempt started.",
        metadata={
            "attempt_count": action.attempt_count,
            "action_type": action.action_type,
        },
    )

    # Persist the in-progress state before the connector is called.
    # If the process dies after this commit, the recovery queue will
    # expose the action instead of silently assuming it never ran.
    db.commit()
    db.refresh(action)

    try:
        outcome = execute_connector(
            action.action_type,
            action.request_payload,
        )

    except Exception as exc:
        # An exception does not prove the operation failed. For a real
        # external connector, the remote side may have completed it
        # before the response or connection failed.
        db.rollback()

        action = _get_action(db, action_id, lock=True)
        action.status = "uncertain"
        action.last_error = (
            "Execution outcome could not be confirmed. "
            f"Exception type: {type(exc).__name__}"
        )

        _record_audit(
            db,
            event_type="action.execution_uncertain",
            action=action,
            actor=actor,
            description=(
                "Execution raised an exception; operator reconciliation "
                "is required before retry."
            ),
            metadata={
                "attempt_count": action.attempt_count,
                "exception_type": type(exc).__name__,
            },
        )

        db.commit()
        db.refresh(action)

        logger.exception(
            "Action execution outcome is uncertain",
            extra={
                "action_id": action_id,
                "attempt_count": action.attempt_count,
            },
        )

        return action

    action = _get_action(db, action_id, lock=True)
    action.result_payload = outcome.result

    if outcome.success:
        action.status = "succeeded"
        action.last_error = None

        _record_audit(
            db,
            event_type="action.execution_succeeded",
            action=action,
            actor=actor,
            description="Action execution succeeded.",
            metadata={
                "attempt_count": action.attempt_count,
            },
        )
    else:
        # The connector returned a known failure instead of raising.
        # This connector contract treats that result as a failure.
        action.status = "failed"
        action.last_error = (
            outcome.error or "Connector reported an unspecified failure."
        )[:4000]

        _record_audit(
            db,
            event_type="action.execution_failed",
            action=action,
            actor=actor,
            description="Action execution returned a known failure.",
            metadata={
                "attempt_count": action.attempt_count,
            },
        )

    db.commit()
    db.refresh(action)

    return action


def execute_review_action(
    db: Session,
    review_id: int,
    request: ActionRequest,
    actor: str,
    idempotency_key: str,
) -> ActionExecution:
    review = _require_approved_review(db, review_id)
    payload = _build_payload(request, review)

    fingerprint = _fingerprint(
        request.action_type,
        payload,
    )

    existing = _find_idempotent_action(
        db,
        idempotency_key=idempotency_key,
        request_fingerprint=fingerprint,
    )

    if existing is not None:
        logger.info(
            "Returning existing action for idempotent request",
            extra={
                "action_id": existing.id,
                "status": existing.status,
            },
        )
        return existing

    action = ActionExecution(
        review_id=review.id,
        action_type=request.action_type,
        status="pending",
        attempt_count=0,
        idempotency_key=idempotency_key,
        request_fingerprint=fingerprint,
        request_payload=payload,
        executed_by=actor,
    )

    db.add(action)

    try:
        # The unique constraint is the final defense against two
        # concurrent requests attempting to insert the same key.
        db.commit()
        db.refresh(action)

    except IntegrityError:
        db.rollback()

        # Another request may have inserted the same key after our
        # initial lookup. Return that record if the payload matches.
        existing = _find_idempotent_action(
            db,
            idempotency_key=idempotency_key,
            request_fingerprint=fingerprint,
        )

        if existing is not None:
            return existing

        raise HTTPException(
            status_code=409,
            detail=(
                "The action could not be created because of a "
                "database integrity conflict."
            ),
        )

    _record_audit(
        db,
        event_type="action.created",
        action=action,
        actor=actor,
        description="Action created with an idempotency key.",
        metadata={
            "action_type": action.action_type,
        },
    )
    db.commit()

    return _run_saved_action(
        db,
        action.id,
        actor=actor,
    )


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
    action = _get_action(db, action_id, lock=True)

    _require_approved_review(db, action.review_id)

    if action.status not in {"pending", "failed"}:
        raise HTTPException(
            status_code=409,
            detail=(
                "Only pending actions or actions with a known failed "
                "outcome can be retried. Reconcile uncertain outcomes first."
            ),
        )

    _record_audit(
        db,
        event_type="action.retry_requested",
        action=action,
        actor=actor,
        description="Operator requested a retry of a pending or known failed action.",
        metadata={
            "previous_attempt_count": action.attempt_count,
        },
    )
    db.commit()

    return _run_saved_action(
        db,
        action.id,
        actor=actor,
    )


def list_recovery_actions(
    db: Session,
    *,
    limit: int = 20,
    offset: int = 0,
) -> list[ActionExecution]:
    return (
        db.query(ActionExecution)
        .filter(
            ActionExecution.status.in_(
                [
                    "pending",
                    "in_progress",
                    "uncertain",
                    "failed",
                ]
            )
        )
        .order_by(
            ActionExecution.updated_at.asc(),
            ActionExecution.id.asc(),
        )
        .limit(limit)
        .offset(offset)
        .all()
    )

def reconcile_action(
    db: Session,
    action_id: int,
    request: ActionReconciliationRequest,
    actor: str,
) -> ActionExecution:
    action = _get_action(db, action_id, lock=True)

    if action.status != "uncertain":
        raise HTTPException(
            status_code=409,
            detail=(
                "Only in-progress or uncertain actions can be reconciled."
            ),
        )

    if request.outcome == "confirmed_succeeded":
        action.status = "succeeded"
        action.last_error = None

        action.result_payload = {
            **(action.result_payload or {}),
            "reconciled": True,
            "reconciliation_note": request.note,
        }

    elif request.outcome == "confirmed_not_executed":
        # This marks the action as eligible for an explicit retry.
        # It does not execute the action automatically.
        action.status = "failed"
        action.last_error = (
            "Operator confirmed that the action was not executed. "
            "A retry may now be requested."
        )

        action.result_payload = {
            **(action.result_payload or {}),
            "reconciled": True,
            "reconciliation_note": request.note,
        }

    _record_audit(
        db,
        event_type="action.reconciled",
        action=action,
        actor=actor,
        description="Operator reconciled an uncertain action outcome.",
        metadata={
            "outcome": request.outcome,
            "note": request.note,
            "status_after_reconciliation": action.status,
        },
    )

    db.commit()
    db.refresh(action)

    return action


def list_review_actions(
    db: Session,
    review_id: int,
    *,
    limit: int = 20,
    offset: int = 0,
) -> list[ActionExecution]:
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
    return (
        db.query(ActionExecution)
        .filter(ActionExecution.review_id == review_id)
        .order_by(
            ActionExecution.created_at.desc(),
            ActionExecution.id.desc(),
        )
        .limit(limit)
        .offset(offset)
        .all()
    )
