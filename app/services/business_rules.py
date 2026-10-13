
from __future__ import annotations

import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any


RULES_VERSION = "phase4_v1"

REQUIRED_FIELDS = (
    "invoice_number",
    "supplier_name",
    "invoice_date",
    "currency",
    "total_amount",
)

CONFIDENCE_THRESHOLD = 0.80


def _field_value(
    fields: dict[str, Any],
    field_name: str,
) -> Any:
    """
    Phase 3 stores fields in this shape:
    {
        "invoice_number": {
            "value": "INV-100",
            "confidence": 0.95,
            "evidence": "Invoice Number: INV-100"
        }
    }
    """
    field = fields.get(field_name)

    if isinstance(field, dict):
        return field.get("value")

    # Supports simpler test data and future providers.
    return field


def _field_confidence(
    fields: dict[str, Any],
    field_name: str,
) -> float | None:
    field = fields.get(field_name)

    if not isinstance(field, dict):
        return None

    confidence = field.get("confidence")

    if confidence is None:
        return None

    try:
        value = float(confidence)
    except (TypeError, ValueError):
        return None

    return max(0.0, min(1.0, value))


def _parse_date(value: Any) -> date | None:
    if not isinstance(value, str) or not value.strip():
        return None

    value = value.strip()

    formats = (
        "%Y-%m-%d",
        "%Y/%m/%d",
        "%d-%m-%Y",
        "%d/%m/%Y",
        "%m/%d/%Y",
        "%d-%b-%Y",
        "%d %b %Y",
        "%d %B %Y",
    )

    for date_format in formats:
        try:
            return datetime.strptime(value, date_format).date()
        except ValueError:
            continue

    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def _parse_amount(value: Any) -> Decimal | None:
    if value is None or isinstance(value, bool):
        return None

    try:
        normalized = str(value).strip()
        normalized = normalized.replace(",", "")
        normalized = normalized.replace(" ", "")

        # Remove a leading currency symbol if one was captured.
        normalized = re.sub(r"^[^\d+\-.]+", "", normalized)

        amount = Decimal(normalized)

        if not amount.is_finite():
            return None

        return amount
    except (InvalidOperation, ValueError):
        return None


def _finding(
    rule_code: str,
    severity: str,
    message: str,
    field: str | None = None,
) -> dict[str, Any]:
    return {
        "rule_code": rule_code,
        "severity": severity,
        "message": message,
        "field": field,
    }


def evaluate_invoice_fields(
    fields: dict[str, Any],
    *,
    duplicate_detected: bool = False,
) -> dict[str, Any]:
    """
    Evaluate extracted invoice data using deterministic rules.

    Returns:
        {
            "decision": "...",
            "risk_score": 0..100,
            "rules_version": "...",
            "findings": [...],
            "summary": "..."
        }

    This function does not access a database and does not
    authorize payments.
    """
    findings: list[dict[str, Any]] = []
    risk_score = 0
    hard_block = False

    # 1. Required fields
    for field_name in REQUIRED_FIELDS:
        value = _field_value(fields, field_name)

        if value is None or not str(value).strip():
            findings.append(
                _finding(
                    "REQUIRED_FIELD_MISSING",
                    "high",
                    f"Required field '{field_name}' is missing.",
                    field_name,
                )
            )
            risk_score += 20

    # 2. Confidence checks
    for field_name in REQUIRED_FIELDS:
        value = _field_value(fields, field_name)

        if value is None or not str(value).strip():
            continue

        confidence = _field_confidence(fields, field_name)

        # If the provider omitted confidence, require review.
        if confidence is None:
            findings.append(
                _finding(
                    "CONFIDENCE_UNAVAILABLE",
                    "medium",
                    f"Confidence is unavailable for '{field_name}'.",
                    field_name,
                )
            )
            risk_score += 5
        elif confidence < CONFIDENCE_THRESHOLD:
            findings.append(
                _finding(
                    "LOW_EXTRACTION_CONFIDENCE",
                    "medium",
                    (
                        f"Extraction confidence for '{field_name}' "
                        f"is {confidence:.2f}; minimum is "
                        f"{CONFIDENCE_THRESHOLD:.2f}."
                    ),
                    field_name,
                )
            )
            risk_score += 10

    # 3. Invoice number format
    invoice_number = _field_value(fields, "invoice_number")

    if invoice_number is not None:
        invoice_number = str(invoice_number).strip()

        if len(invoice_number) > 100:
            findings.append(
                _finding(
                    "INVOICE_NUMBER_TOO_LONG",
                    "high",
                    "Invoice number exceeds 100 characters.",
                    "invoice_number",
                )
            )
            risk_score += 15

    # 4. Supplier name
    supplier_name = _field_value(fields, "supplier_name")

    if supplier_name is not None:
        supplier_name = str(supplier_name).strip()

        if len(supplier_name) > 200:
            findings.append(
                _finding(
                    "SUPPLIER_NAME_TOO_LONG",
                    "high",
                    "Supplier name exceeds 200 characters.",
                    "supplier_name",
                )
            )
            risk_score += 15

    # 5. Invoice date
    invoice_date_raw = _field_value(fields, "invoice_date")
    invoice_date = _parse_date(invoice_date_raw)

    if invoice_date_raw and invoice_date is None:
        findings.append(
            _finding(
                "INVALID_INVOICE_DATE",
                "high",
                "Invoice date could not be parsed.",
                "invoice_date",
            )
        )
        risk_score += 20

    # 6. Due date and date ordering
    due_date_raw = _field_value(fields, "due_date")
    due_date = _parse_date(due_date_raw)

    if due_date_raw and due_date is None:
        findings.append(
            _finding(
                "INVALID_DUE_DATE",
                "medium",
                "Due date could not be parsed.",
                "due_date",
            )
        )
        risk_score += 10

    if invoice_date and due_date and due_date < invoice_date:
        findings.append(
            _finding(
                "DUE_DATE_BEFORE_INVOICE_DATE",
                "high",
                "Due date is earlier than the invoice date.",
                "due_date",
            )
        )
        risk_score += 25

    # 7. Currency validation
    currency = _field_value(fields, "currency")

    if currency is not None:
        currency = str(currency).strip().upper()

        if not re.fullmatch(r"[A-Z]{3}", currency):
            findings.append(
                _finding(
                    "INVALID_CURRENCY_FORMAT",
                    "high",
                    "Currency must be a three-letter code.",
                    "currency",
                )
            )
            risk_score += 20

    # 8. Amount validation
    total_raw = _field_value(fields, "total_amount")
    total_amount = _parse_amount(total_raw)

    if total_raw is not None and total_amount is None:
        findings.append(
            _finding(
                "INVALID_TOTAL_AMOUNT",
                "critical",
                "Invoice total is not a valid finite number.",
                "total_amount",
            )
        )
        risk_score += 40
        hard_block = True

    elif total_amount is not None and total_amount <= Decimal("0"):
        findings.append(
            _finding(
                "TOTAL_AMOUNT_NOT_POSITIVE",
                "critical",
                "Invoice total must be greater than zero.",
                "total_amount",
            )
        )
        risk_score += 50
        hard_block = True

    # 9. Duplicate detection
    if duplicate_detected:
        findings.append(
            _finding(
                "POSSIBLE_DUPLICATE_INVOICE",
                "high",
                (
                    "Another document has the same normalized "
                    "supplier name and invoice number."
                ),
                "invoice_number",
            )
        )
        risk_score += 40

    risk_score = min(100, risk_score)

    # A hard failure takes priority over the risk threshold.
    if hard_block:
        decision = "blocked"
    elif findings:
        decision = "needs_review"
    else:
        decision = "ready_for_matching"

    if decision == "ready_for_matching":
        summary = (
            "Basic invoice validation passed. Continue to "
            "purchase-order and goods-receipt matching."
        )
    elif decision == "blocked":
        summary = (
            "A hard validation failure prevents normal processing. "
            "A person must investigate before the invoice proceeds."
        )
    else:
        summary = (
            f"{len(findings)} business rule finding(s) require "
            "review before the invoice proceeds."
        )

    return {
        "decision": decision,
        "risk_score": risk_score,
        "rules_version": RULES_VERSION,
        "findings": findings,
        "summary": summary,
    }
