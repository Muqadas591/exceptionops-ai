from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy.orm import Session, selectinload

from app.models.business_evaluation import BusinessEvaluation
from app.models.document import Document
from app.models.extraction_result import ExtractionResult
from app.models.workflow_event import WorkflowEvent
from app.models.workflow_run import WorkflowRun
from app.services.business_evaluation import evaluate_document


TERMINAL_STATUSES = {"resolved", "cancelled"}

ALLOWED_RESOLUTION_STATUSES = {
    "needs_review",
    "evaluated",
    "failed",
}


def _get_workflow(db: Session, workflow_id: int) -> WorkflowRun:
    workflow = (
        db.query(WorkflowRun)
        .options(selectinload(WorkflowRun.events))
        .filter(WorkflowRun.id == workflow_id)
        .first()
    )

    if workflow is None:
        raise HTTPException(
            status_code=404,
            detail=f"Workflow {workflow_id} was not found.",
        )

    return workflow


def _record_event(
    db: Session,
    workflow: WorkflowRun,
    event_type: str,
    message: str,
    from_status: str | None = None,
    to_status: str | None = None,
    metadata: dict | None = None,
) -> None:
    event = WorkflowEvent(
        workflow_run_id=workflow.id,
        event_type=event_type,
        from_status=from_status,
        to_status=to_status,
        message=message,
        event_metadata=metadata or {},
    )
    db.add(event)


def _transition(
    db: Session,
    workflow: WorkflowRun,
    new_status: str,
    event_type: str,
    message: str,
    metadata: dict | None = None,
) -> None:
    old_status = workflow.status

    if old_status == new_status:
        return

    workflow.status = new_status

    _record_event(
        db=db,
        workflow=workflow,
        event_type=event_type,
        message=message,
        from_status=old_status,
        to_status=new_status,
        metadata=metadata,
    )


def create_workflow(
    db: Session,
    document_id: int,
    idempotency_key: str | None = None,
) -> WorkflowRun:
    document = (
        db.query(Document)
        .filter(Document.id == document_id)
        .first()
    )

    if document is None:
        raise HTTPException(
            status_code=404,
            detail=f"Document {document_id} was not found.",
        )

    # A generated key makes each request unique when the caller
    # does not supply an Idempotency-Key header.
    key = idempotency_key or f"workflow-{uuid4()}"

    existing = (
        db.query(WorkflowRun)
        .filter(WorkflowRun.idempotency_key == key)
        .first()
    )

    if existing is not None:
        if existing.document_id != document_id:
            raise HTTPException(
                status_code=409,
                detail=(
                    "This idempotency key has already been used "
                    "for a different document."
                ),
            )

        return _get_workflow(db, existing.id)

    workflow = WorkflowRun(
        document_id=document_id,
        status="received",
        idempotency_key=key,
        attempt_count=0,
    )

    db.add(workflow)
    db.flush()

    _record_event(
        db=db,
        workflow=workflow,
        event_type="workflow_created",
        message="Workflow created for the document.",
        to_status="received",
        metadata={"document_id": document_id},
    )

    db.commit()
    return _get_workflow(db, workflow.id)


def get_workflow(db: Session, workflow_id: int) -> WorkflowRun:
    return _get_workflow(db, workflow_id)


def get_latest_document_workflow(
    db: Session,
    document_id: int,
) -> WorkflowRun:
    document = (
        db.query(Document)
        .filter(Document.id == document_id)
        .first()
    )

    if document is None:
        raise HTTPException(
            status_code=404,
            detail=f"Document {document_id} was not found.",
        )

    workflow = (
        db.query(WorkflowRun)
        .filter(WorkflowRun.document_id == document_id)
        .order_by(WorkflowRun.id.desc())
        .first()
    )

    if workflow is None:
        raise HTTPException(
            status_code=404,
            detail="No workflow has been created for this document.",
        )

    return _get_workflow(db, workflow.id)


def advance_workflow(
    db: Session,
    workflow_id: int,
) -> WorkflowRun:
    workflow = _get_workflow(db, workflow_id)

    if workflow.status in TERMINAL_STATUSES:
        raise HTTPException(
            status_code=409,
            detail=f"A {workflow.status} workflow cannot be advanced.",
        )

    # Step 1: Verify that the source document still exists.
    document = (
        db.query(Document)
        .filter(Document.id == workflow.document_id)
        .first()
    )

    if document is None:
        raise HTTPException(
            status_code=404,
            detail="The workflow's document no longer exists.",
        )

    # Step 2: Check whether Phase 3 extraction has completed.
    extraction = (
        db.query(ExtractionResult)
        .filter(
            ExtractionResult.document_id == workflow.document_id
        )
        .first()
    )

    if extraction is None:
        _transition(
            db,
            workflow,
            "received",
            "waiting_for_extraction",
            "Waiting for the existing document extraction step.",
        )
        workflow.last_error = None
        db.commit()
        return _get_workflow(db, workflow.id)

    _transition(
        db,
        workflow,
        "extracted",
        "extraction_detected",
        "An extraction result is available.",
    )

    # Step 3: Reuse the Phase 4 business evaluation if it exists.
    evaluation = (
        db.query(BusinessEvaluation)
        .filter(
            BusinessEvaluation.document_id == workflow.document_id
        )
        .first()
    )

    if evaluation is None:
        try:
            evaluation = evaluate_document(
                db,
                workflow.document_id,
            )
        except Exception as exc:
            # The evaluation service may have changed the transaction.
            # Roll back, reload the workflow, and persist the failure.
            db.rollback()
            workflow = _get_workflow(db, workflow_id)

            if workflow.status in TERMINAL_STATUSES:
                return workflow

            workflow.attempt_count += 1
            workflow.last_error = str(exc)[:4000]

            _transition(
                db,
                workflow,
                "failed",
                "evaluation_failed",
                "Business evaluation failed. The workflow can be retried.",
                metadata={"error": str(exc)[:1000]},
            )

            db.commit()
            return _get_workflow(db, workflow_id)

    # Step 4: Map the Phase 4 decision to a workflow state.
    if evaluation.decision in {"needs_review", "blocked"}:
        next_status = "needs_review"
        message = (
            f"Business evaluation requires attention: "
            f"{evaluation.decision}."
        )
    else:
        next_status = "evaluated"
        message = "Business evaluation completed successfully."

    _transition(
        db,
        workflow,
        next_status,
        "evaluation_completed",
        message,
        metadata={
            "evaluation_id": evaluation.id,
            "decision": evaluation.decision,
            "risk_score": evaluation.risk_score,
        },
    )

    workflow.last_error = None
    db.commit()

    return _get_workflow(db, workflow.id)


def retry_workflow(
    db: Session,
    workflow_id: int,
) -> WorkflowRun:
    workflow = _get_workflow(db, workflow_id)

    if workflow.status in TERMINAL_STATUSES:
        raise HTTPException(
            status_code=409,
            detail=f"A {workflow.status} workflow cannot be retried.",
        )

    if workflow.status != "failed":
        raise HTTPException(
            status_code=409,
            detail="Only failed workflows can be retried.",
        )

    previous_error = workflow.last_error

    workflow.attempt_count += 1
    workflow.last_error = None

    _record_event(
        db=db,
        workflow=workflow,
        event_type="retry_requested",
        message="A retry was requested.",
        from_status=workflow.status,
        to_status=workflow.status,
        metadata={
            "attempt_count": workflow.attempt_count,
            "previous_error": previous_error,
        },
    )

    # Commit the retry request before attempting the next step.
    db.commit()

    return advance_workflow(db, workflow_id)


def resolve_workflow(
    db: Session,
    workflow_id: int,
    note: str,
) -> WorkflowRun:
    workflow = _get_workflow(db, workflow_id)

    if workflow.status not in ALLOWED_RESOLUTION_STATUSES:
        raise HTTPException(
            status_code=409,
            detail=(
                "Only evaluated, needs_review, or failed workflows "
                "can be manually resolved."
            ),
        )

    note = note.strip()

    if len(note) < 3:
        raise HTTPException(
            status_code=422,
            detail="Please provide a resolution note of at least 3 characters.",
        )

    workflow.resolution_note = note
    workflow.last_error = None

    _transition(
        db,
        workflow,
        "resolved",
        "manually_resolved",
        "Workflow manually resolved by an authorized API caller.",
        metadata={"resolution_note": note},
    )

    db.commit()
    return _get_workflow(db, workflow.id)


def cancel_workflow(
    db: Session,
    workflow_id: int,
) -> WorkflowRun:
    workflow = _get_workflow(db, workflow_id)

    if workflow.status in TERMINAL_STATUSES:
        raise HTTPException(
            status_code=409,
            detail=f"A {workflow.status} workflow cannot be cancelled.",
        )

    _transition(
        db,
        workflow,
        "cancelled",
        "workflow_cancelled",
        "Workflow was explicitly cancelled.",
    )

    db.commit()
    return _get_workflow(db, workflow.id)