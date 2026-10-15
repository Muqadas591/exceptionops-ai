from fastapi import HTTPException
from sqlalchemy.orm import Session, selectinload

from app.models.human_review import HumanReview
from app.models.review_comment import ReviewComment
from app.models.workflow_run import WorkflowRun


def _review_query(db: Session):
    return db.query(HumanReview).options(
        selectinload(HumanReview.comments)
    )


def get_review(db: Session, review_id: int) -> HumanReview:
    review = (
        _review_query(db)
        .filter(HumanReview.id == review_id)
        .first()
    )

    if review is None:
        raise HTTPException(
            status_code=404,
            detail=f"Review {review_id} was not found.",
        )

    return review


def get_or_create_review(
    db: Session,
    workflow_run_id: int,
) -> HumanReview:
    workflow = (
        db.query(WorkflowRun)
        .filter(WorkflowRun.id == workflow_run_id)
        .first()
    )

    if workflow is None:
        raise HTTPException(
            status_code=404,
            detail="Workflow was not found.",
        )

    if workflow.status not in {"needs_review", "evaluated"}:
        raise HTTPException(
            status_code=409,
            detail=(
                "A review can only be created for a workflow "
                "that has been evaluated or needs review."
            ),
        )

    review = (
        db.query(HumanReview)
        .filter(HumanReview.workflow_run_id == workflow_run_id)
        .first()
    )

    if review is None:
        review = HumanReview(
            workflow_run_id=workflow_run_id,
            status="pending",
        )
        db.add(review)
        db.commit()
        db.refresh(review)

    return get_review(db, review.id)


def list_exception_queue(
    db: Session,
    status: str | None = None,
    assigned_to: str | None = None,
) -> list[HumanReview]:
    query = (
        db.query(HumanReview)
        .join(
            WorkflowRun,
            WorkflowRun.id == HumanReview.workflow_run_id,
        )
        .options(selectinload(HumanReview.comments))
    )

    if status:
        query = query.filter(HumanReview.status == status)

    if assigned_to:
        query = query.filter(HumanReview.assigned_to == assigned_to)

    return query.order_by(HumanReview.id.desc()).all()


def assign_reviewer(
    db: Session,
    review_id: int,
    reviewer: str,
    actor: str,
) -> HumanReview:
    review = get_review(db, review_id)

    if review.status in {"approved", "rejected"}:
        raise HTTPException(
            status_code=409,
            detail="A completed review cannot be reassigned.",
        )

    reviewer = reviewer.strip()

    if not reviewer:
        raise HTTPException(
            status_code=422,
            detail="Reviewer name cannot be empty.",
        )

    review.assigned_to = reviewer

    db.add(
        ReviewComment(
            review_id=review.id,
            author=actor,
            comment_type="assignment",
            body=f"Review assigned to {reviewer}.",
        )
    )

    db.commit()
    return get_review(db, review.id)


def add_comment(
    db: Session,
    review_id: int,
    body: str,
    actor: str,
    comment_type: str = "comment",
) -> HumanReview:
    review = get_review(db, review_id)

    if review.status in {"approved", "rejected"}:
        raise HTTPException(
            status_code=409,
            detail="Cannot add comments to a completed review.",
        )

    body = body.strip()

    if not body:
        raise HTTPException(
            status_code=422,
            detail="Comment cannot be empty.",
        )

    db.add(
        ReviewComment(
            review_id=review.id,
            author=actor,
            comment_type=comment_type,
            body=body,
        )
    )

    if comment_type == "correction_request":
        review.status = "correction_requested"

    db.commit()
    return get_review(db, review.id)


def decide_review(
    db: Session,
    review_id: int,
    decision: str,
    note: str,
    actor: str,
) -> HumanReview:
    review = get_review(db, review_id)

    if review.status in {"approved", "rejected"}:
        raise HTTPException(
            status_code=409,
            detail="This review already has a final decision.",
        )

    if decision not in {"approved", "rejected"}:
        raise HTTPException(
            status_code=422,
            detail="Decision must be approved or rejected.",
        )

    if review.assigned_to is None:
        raise HTTPException(
            status_code=409,
            detail="Assign a reviewer before making a decision.",
        )

    note = note.strip()

    if len(note) < 3:
        raise HTTPException(
            status_code=422,
            detail="A decision note of at least 3 characters is required.",
        )

    review.status = decision
    review.decision_note = note
    review.decided_by = actor

    db.add(
        ReviewComment(
            review_id=review.id,
            author=actor,
            comment_type="decision",
            body=f"{decision}: {note}",
        )
    )

    db.commit()
    return get_review(db, review.id)