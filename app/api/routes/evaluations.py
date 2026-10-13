
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.business_evaluation import BusinessEvaluationRead
from app.services.business_evaluation import (
    evaluate_document,
    get_document_evaluation,
)

router = APIRouter(
    prefix="/documents",
    tags=["Business Evaluations"],
)


@router.post(
    "/{document_id}/evaluate",
    response_model=BusinessEvaluationRead,
)
def evaluate_invoice_document(
    document_id: int,
    db: Session = Depends(get_db),
) -> BusinessEvaluationRead:
    """
    Run Phase 4 business rules on the latest Phase 3 extraction.
    """
    return evaluate_document(db, document_id)


@router.get(
    "/{document_id}/evaluation",
    response_model=BusinessEvaluationRead,
)
def read_invoice_evaluation(
    document_id: int,
    db: Session = Depends(get_db),
) -> BusinessEvaluationRead:
    """
    Retrieve the latest stored Phase 4 evaluation.
    """
    return get_document_evaluation(db, document_id)
