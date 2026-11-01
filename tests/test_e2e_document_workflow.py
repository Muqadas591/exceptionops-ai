from io import BytesIO


SYNTHETIC_INVOICE = b"""\
Invoice Number: INV-DEMO-1001
Supplier: Northstar Office Supplies
Invoice Date: 2026-10-15
Due Date: 2026-11-14
Currency: USD
Total Amount: 1250.00
Purchase Order: PO-DEMO-501
"""


def test_document_upload_metadata_download_and_workflow(client):
    # 1. Upload a synthetic invoice.
    upload = client.post(
        "/api/v1/documents",
        files={
            "file": (
                "synthetic-invoice.txt",
                BytesIO(SYNTHETIC_INVOICE),
                "text/plain",
            )
        },
    )

    assert upload.status_code == 201, upload.text

    document = upload.json()
    document_id = document["id"]

    assert document["original_filename"] == "synthetic-invoice.txt"
    assert document["file_size_bytes"] == len(SYNTHETIC_INVOICE)
    assert document["checksum_sha256"]

    # 2. Retrieve the document metadata.
    metadata = client.get(
        f"/api/v1/documents/{document_id}"
    )

    assert metadata.status_code == 200
    assert metadata.json()["id"] == document_id

    # 3. Download the original document.
    download = client.get(
        f"/api/v1/documents/{document_id}/content"
    )

    assert download.status_code == 200
    assert download.content == SYNTHETIC_INVOICE

    # 4. Start the workflow.
    workflow_response = client.post(
        f"/api/v1/documents/{document_id}/workflow",
        headers={
            "Idempotency-Key": "e2e-demo-invoice-1001"
        },
    )

    assert workflow_response.status_code == 200, workflow_response.text

    workflow = workflow_response.json()
    workflow_id = workflow["id"]

    # 5. Read the saved workflow.
    workflow_read = client.get(
        f"/api/v1/workflows/{workflow_id}"
    )

    assert workflow_read.status_code == 200
    assert workflow_read.json()["id"] == workflow_id


def test_invalid_document_is_rejected(client):
    response = client.post(
        "/api/v1/documents",
        files={
            "file": (
                "not-a-supported-image.exe",
                b"synthetic invalid content",
                "application/octet-stream",
            )
        },
    )

    assert response.status_code == 400


def test_empty_document_is_rejected(client):
    response = client.post(
        "/api/v1/documents",
        files={
            "file": (
                "empty.txt",
                b"",
                "text/plain",
            )
        },
    )

    assert response.status_code == 400


def test_missing_document_workflow_returns_404(client):
    response = client.post(
        "/api/v1/documents/999999/workflow"
    )

    assert response.status_code == 404


def test_missing_workflow_returns_404(client):
    response = client.get(
        "/api/v1/workflows/999999"
    )

    assert response.status_code == 404
def test_duplicate_document_content_is_rejected(client):
    files = {
        "file": (
            "synthetic-invoice.txt",
            SYNTHETIC_INVOICE,
            "text/plain",
        )
    }

    first = client.post(
        "/api/v1/documents",
        files=files,
    )

    second = client.post(
        "/api/v1/documents",
        files=files,
    )

    assert first.status_code == 201
    assert second.status_code == 409

    assert (
        second.json()["detail"]["document_id"]
        == first.json()["id"]
    )