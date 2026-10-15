from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.authorization import require_reviewer
from app.db.session import get_db
from app.schemas.human_review import (
    AssignReviewerRequest,
    CorrectionRequest,
    HumanReviewRead,
    ReviewCommentCreate,
    ReviewDecisionRequest,
)
from app.services.human_review_service import (
    add_comment,
    assign_reviewer,
    decide_review,
    get_or_create_review,
    get_review,
    list_exception_queue,
)


router = APIRouter(tags=["Human Review"])


@router.get(
    "/reviews/queue",
    response_model=list[HumanReviewRead],
)
def exception_queue(
    status: str | None = Query(default=None),
    assigned_to: str | None = Query(default=None),
    db: Session = Depends(get_db),
    actor: str = Depends(require_reviewer),
):
    return list_exception_queue(
        db=db,
        status=status,
        assigned_to=assigned_to,
    )


@router.post(
    "/workflows/{workflow_id}/review",
    response_model=HumanReviewRead,
)
def create_workflow_review(
    workflow_id: int,
    db: Session = Depends(get_db),
    actor: str = Depends(require_reviewer),
):
    return get_or_create_review(db, workflow_id)


@router.get(
    "/reviews/{review_id}",
    response_model=HumanReviewRead,
)
def read_review(
    review_id: int,
    db: Session = Depends(get_db),
    actor: str = Depends(require_reviewer),
):
    return get_review(db, review_id)


@router.post(
    "/reviews/{review_id}/assign",
    response_model=HumanReviewRead,
)
def assign_review(
    review_id: int,
    request: AssignReviewerRequest,
    db: Session = Depends(get_db),
    actor: str = Depends(require_reviewer),
):
    return assign_reviewer(
        db=db,
        review_id=review_id,
        reviewer=request.reviewer,
        actor=actor,
    )


@router.post(
    "/reviews/{review_id}/comments",
    response_model=HumanReviewRead,
)
def create_review_comment(
    review_id: int,
    request: ReviewCommentCreate,
    db: Session = Depends(get_db),
    actor: str = Depends(require_reviewer),
):
    return add_comment(
        db=db,
        review_id=review_id,
        body=request.body,
        actor=actor,
    )


@router.post(
    "/reviews/{review_id}/request-correction",
    response_model=HumanReviewRead,
)
def request_correction(
    review_id: int,
    request: CorrectionRequest,
    db: Session = Depends(get_db),
    actor: str = Depends(require_reviewer),
):
    return add_comment(
        db=db,
        review_id=review_id,
        body=request.instructions,
        actor=actor,
        comment_type="correction_request",
    )


@router.post(
    "/reviews/{review_id}/approve",
    response_model=HumanReviewRead,
)
def approve_review(
    review_id: int,
    request: ReviewDecisionRequest,
    db: Session = Depends(get_db),
    actor: str = Depends(require_reviewer),
):
    return decide_review(
        db=db,
        review_id=review_id,
        decision="approved",
        note=request.note,
        actor=actor,
    )


@router.post(
    "/reviews/{review_id}/reject",
    response_model=HumanReviewRead,
)
def reject_review(
    review_id: int,
    request: ReviewDecisionRequest,
    db: Session = Depends(get_db),
    actor: str = Depends(require_reviewer),
):
    return decide_review(
        db=db,
        review_id=review_id,
        decision="rejected",
        note=request.note,
        actor=actor,
    )