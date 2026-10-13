
def upload_sample_invoice(client):
    content = (
        "Supplier: North Star Supplies\n"
        "Invoice Number: INV-2026-001\n"
        "Invoice Date: 2026-10-10\n"
        "Due Date: 2026-10-30\n"
        "Currency: PKR\n"
        "Total: 2500.00\n"
    ).encode("utf-8")

    response = client.post(
        "/api/v1/documents",
        files={
            "file": (
                "synthetic-invoice.txt",
                content,
                "text/plain",
            )
        },
    )

    assert response.status_code == 201
    return response.json()["id"]


def test_extract_invoice_fields(client):
    document_id = upload_sample_invoice(client)

    response = client.post(
        f"/api/v1/documents/{document_id}/extract"
    )

    assert response.status_code == 200

    body = response.json()
    assert body["document_id"] == document_id
    assert body["provider_name"] == "rule_based_v1"

    fields = body["fields"]

    assert fields["invoice_number"]["value"] == "INV-2026-001"
    assert fields["invoice_date"]["value"] == "2026-10-10"
    assert fields["due_date"]["value"] == "2026-10-30"
    assert fields["supplier_name"]["value"] == "North Star Supplies"
    assert fields["currency"]["value"] == "PKR"
    assert fields["total_amount"]["value"] == "2500.00"

    assert fields["invoice_number"]["evidence"] is not None
    assert fields["invoice_number"]["confidence"] > 0


def test_extraction_result_can_be_retrieved(client):
    document_id = upload_sample_invoice(client)

    run_response = client.post(
        f"/api/v1/documents/{document_id}/extract"
    )
    assert run_response.status_code == 200

    response = client.get(
        f"/api/v1/documents/{document_id}/extraction"
    )

    assert response.status_code == 200
    assert response.json()["document_id"] == document_id
    assert response.json()["fields"]["invoice_number"]["value"] == (
        "INV-2026-001"
    )


def test_repeating_extraction_updates_existing_result(client):
    document_id = upload_sample_invoice(client)

    first = client.post(
        f"/api/v1/documents/{document_id}/extract"
    )
    second = client.post(
        f"/api/v1/documents/{document_id}/extract"
    )

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["id"] == second.json()["id"]


def test_extracting_unknown_document_returns_404(client):
    response = client.post("/api/v1/documents/999999/extract")

    assert response.status_code == 404


def test_get_missing_extraction_returns_404(client):
    document_id = upload_sample_invoice(client)

    response = client.get(
        f"/api/v1/documents/{document_id}/extraction"
    )

    assert response.status_code == 404


def test_scanned_or_empty_text_pdf_returns_clear_error(client):
    from io import BytesIO

    from pypdf import PdfWriter

    writer = PdfWriter()
    writer.add_blank_page(width=300, height=300)

    buffer = BytesIO()
    writer.write(buffer)

    upload = client.post(
        "/api/v1/documents",
        files={
            "file": (
                "blank.pdf",
                buffer.getvalue(),
                "application/pdf",
            )
        },
    )

    assert upload.status_code == 201

    document_id = upload.json()["id"]
    response = client.post(
        f"/api/v1/documents/{document_id}/extract"
    )

    assert response.status_code == 422
    assert "No extractable text" in response.json()["detail"]
