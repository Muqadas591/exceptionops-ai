from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query, Response
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
    count_exception_queue,
    decide_review,
    get_or_create_review,
    get_review,
    list_exception_queue,
)


router = APIRouter(tags=["Human Review"])


ReviewStatusFilter = Literal[
    "pending",
    "correction_requested",
    "approved",
    "rejected",
]


@router.get(
    "/reviews/queue",
    response_model=list[HumanReviewRead],
)
def exception_queue(
    response: Response,
    status: Annotated[
        ReviewStatusFilter | None,
        Query(description="Filter reviews by status."),
    ] = None,
    assigned_to: Annotated[
        str | None,
        Query(min_length=1, max_length=255),
    ] = None,
    limit: Annotated[
        int,
        Query(ge=1, le=100),
    ] = 20,
    offset: Annotated[
        int,
        Query(ge=0),
    ] = 0,
    db: Session = Depends(get_db),
    actor: str = Depends(require_reviewer),
) -> list[HumanReviewRead]:
    total = count_exception_queue(
        db=db,
        status=status,
        assigned_to=assigned_to,
    )

    reviews = list_exception_queue(
        db=db,
        status=status,
        assigned_to=assigned_to,
        limit=limit,
        offset=offset,
    )

    response.headers["X-Total-Count"] = str(total)
    response.headers["X-Page-Limit"] = str(limit)
    response.headers["X-Page-Offset"] = str(offset)
    response.headers["X-Has-More"] = str(
        offset + len(reviews) < total
    ).lower()

    return reviews


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