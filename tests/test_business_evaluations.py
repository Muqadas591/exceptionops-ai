
from fastapi.testclient import TestClient

from app.services.business_rules import evaluate_invoice_fields


def make_field(value, confidence=0.99):
    return {
        "value": value,
        "confidence": confidence,
        "evidence": str(value),
    }


def valid_fields():
    return {
        "invoice_number": make_field("INV-2026-100"),
        "supplier_name": make_field("North Star Supplies"),
        "invoice_date": make_field("2026-10-10"),
        "due_date": make_field("2026-10-30"),
        "currency": make_field("PKR"),
        "total_amount": make_field("2500.00"),
    }


def test_valid_invoice_is_ready_for_matching():
    result = evaluate_invoice_fields(valid_fields())

    assert result["decision"] == "ready_for_matching"
    assert result["risk_score"] == 0
    assert result["findings"] == []


def test_missing_invoice_number_requires_review():
    fields = valid_fields()
    fields["invoice_number"] = make_field("")

    result = evaluate_invoice_fields(fields)

    assert result["decision"] == "needs_review"
    assert result["risk_score"] > 0
    assert any(
        finding["rule_code"] == "REQUIRED_FIELD_MISSING"
        for finding in result["findings"]
    )


def test_zero_total_is_blocked():
    fields = valid_fields()
    fields["total_amount"] = make_field("0")

    result = evaluate_invoice_fields(fields)

    assert result["decision"] == "blocked"
    assert result["risk_score"] >= 50
    assert any(
        finding["rule_code"] == "TOTAL_AMOUNT_NOT_POSITIVE"
        for finding in result["findings"]
    )


def test_invalid_total_is_blocked():
    fields = valid_fields()
    fields["total_amount"] = make_field("not-a-number")

    result = evaluate_invoice_fields(fields)

    assert result["decision"] == "blocked"
    assert any(
        finding["rule_code"] == "INVALID_TOTAL_AMOUNT"
        for finding in result["findings"]
    )


def test_due_date_before_invoice_date_requires_review():
    fields = valid_fields()
    fields["due_date"] = make_field("2026-10-01")

    result = evaluate_invoice_fields(fields)

    assert result["decision"] == "needs_review"
    assert any(
        finding["rule_code"] == "DUE_DATE_BEFORE_INVOICE_DATE"
        for finding in result["findings"]
    )


def test_low_confidence_requires_review():
    fields = valid_fields()
    fields["total_amount"] = make_field("2500.00", confidence=0.40)

    result = evaluate_invoice_fields(fields)

    assert result["decision"] == "needs_review"
    assert any(
        finding["rule_code"] == "LOW_EXTRACTION_CONFIDENCE"
        and finding["field"] == "total_amount"
        for finding in result["findings"]
    )


def test_duplicate_requires_review():
    result = evaluate_invoice_fields(
        valid_fields(),
        duplicate_detected=True,
    )

    assert result["decision"] == "needs_review"
    assert result["risk_score"] == 40
    assert any(
        finding["rule_code"] == "POSSIBLE_DUPLICATE_INVOICE"
        for finding in result["findings"]
    )


def test_risk_score_never_exceeds_100():
    fields = {
        "invoice_number": make_field(""),
        "supplier_name": make_field(""),
        "invoice_date": make_field("not-a-date"),
        "currency": make_field("US DOLLAR"),
        "total_amount": make_field("-500"),
    }

    result = evaluate_invoice_fields(
        fields,
        duplicate_detected=True,
    )

    assert 0 <= result["risk_score"] <= 100
    assert result["decision"] == "blocked"


def upload_text_invoice(
    client: TestClient,
    text: str,
) -> int:
    response = client.post(
        "/api/v1/documents",
        files={
            "file": (
                "invoice.txt",
                text.encode("utf-8"),
                "text/plain",
            )
        },
    )

    assert response.status_code in (200, 201), response.text

    payload = response.json()
    return payload["id"]


def extract_document(
    client: TestClient,
    document_id: int,
) -> None:
    response = client.post(
        f"/api/v1/documents/{document_id}/extract"
    )
    assert response.status_code == 200, response.text


def test_evaluation_requires_extraction(client: TestClient):
    document_id = upload_text_invoice(
        client,
        "This document has not been extracted yet.",
    )

    response = client.post(
        f"/api/v1/documents/{document_id}/evaluate"
    )

    assert response.status_code == 409


def test_evaluate_and_retrieve_result(client: TestClient):
    invoice_text = (
        "Supplier: North Star Supplies\n"
        "Invoice Number: INV-2026-100\n"
        "Invoice Date: 2026-10-10\n"
        "Due Date: 2026-10-30\n"
        "Currency: PKR\n"
        "Total: 2500.00\n"
    )

    document_id = upload_text_invoice(client, invoice_text)
    extract_document(client, document_id)

    response = client.post(
        f"/api/v1/documents/{document_id}/evaluate"
    )

    assert response.status_code == 200, response.text
    result = response.json()

    assert result["document_id"] == document_id
    assert result["decision"] in (
        "ready_for_matching",
        "needs_review",
        "blocked",
    )
    assert 0 <= result["risk_score"] <= 100
    assert isinstance(result["findings"], list)

    evaluation_id = result["id"]

    retrieve_response = client.get(
        f"/api/v1/documents/{document_id}/evaluation"
    )

    assert retrieve_response.status_code == 200
    assert retrieve_response.json()["id"] == evaluation_id


def test_rerun_updates_existing_evaluation(client: TestClient):
    invoice_text = (
        "Supplier: North Star Supplies\n"
        "Invoice Number: INV-2026-101\n"
        "Invoice Date: 2026-10-10\n"
        "Due Date: 2026-10-30\n"
        "Currency: PKR\n"
        "Total: 2500.00\n"
    )

    document_id = upload_text_invoice(client, invoice_text)
    extract_document(client, document_id)

    first = client.post(
        f"/api/v1/documents/{document_id}/evaluate"
    )
    second = client.post(
        f"/api/v1/documents/{document_id}/evaluate"
    )

    assert first.status_code == 200, first.text
    assert second.status_code == 200, second.text
    assert first.json()["id"] == second.json()["id"]


def test_duplicate_invoice_requires_review(client: TestClient):
    invoice_text = (
        "Supplier: North Star Supplies\n"
        "Invoice Number: INV-2026-200\n"
        "Invoice Date: 2026-10-10\n"
        "Due Date: 2026-10-30\n"
        "Currency: PKR\n"
        "Total: 2500.00\n"
    )

    first_id = upload_text_invoice(client, invoice_text)
    extract_document(client, first_id)

    first_eval = client.post(
        f"/api/v1/documents/{first_id}/evaluate"
    )
    assert first_eval.status_code == 200, first_eval.text

    # Different file content and therefore a different checksum,
    # but the supplier and invoice number are identical.
    second_id = upload_text_invoice(
        client,
        invoice_text + "\nInternal note: duplicate submission.\n",
    )
    extract_document(client, second_id)

    second_eval = client.post(
        f"/api/v1/documents/{second_id}/evaluate"
    )

    assert second_eval.status_code == 200, second_eval.text
    result = second_eval.json()

    assert result["decision"] == "needs_review"
    assert any(
        finding["rule_code"] == "POSSIBLE_DUPLICATE_INVOICE"
        for finding in result["findings"]
    )


def test_missing_document_returns_404(client: TestClient):
    response = client.post(
        "/api/v1/documents/999999/evaluate"
    )

    assert response.status_code == 404
