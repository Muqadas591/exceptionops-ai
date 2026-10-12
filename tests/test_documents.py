
from app.core.config import get_settings


def test_upload_txt_document(client, document_storage):
    response = client.post(
        "/api/v1/documents",
        files={
            "file": (
                "invoice.txt",
                b"Invoice number: INV-1001\nTotal: 2500.00",
                "text/plain",
            )
        },
    )

    assert response.status_code == 201
    body = response.json()

    assert body["original_filename"] == "invoice.txt"
    assert body["extension"] == ".txt"
    assert body["content_type"] == "text/plain"
    assert body["file_size_bytes"] > 0
    assert len(body["checksum_sha256"]) == 64
    assert body["status"] == "received"

    stored_files = list(document_storage.iterdir())
    assert len(stored_files) == 1
    assert stored_files[0].name != "invoice.txt"


def test_upload_pdf_document(client):
    # Minimal signature fixture for basic ingestion validation.
    pdf_content = b"%PDF-1.4\nSynthetic test document\n"

    response = client.post(
        "/api/v1/documents",
        files={
            "file": (
                "sample.pdf",
                pdf_content,
                "application/pdf",
            )
        },
    )

    assert response.status_code == 201
    assert response.json()["extension"] == ".pdf"


def test_reject_unsupported_extension(client):
    response = client.post(
        "/api/v1/documents",
        files={
            "file": (
                "invoice.exe",
                b"not allowed",
                "application/octet-stream",
            )
        },
    )

    assert response.status_code == 400
    assert "Unsupported file extension" in response.json()["detail"]


def test_reject_invalid_pdf_signature(client, document_storage):
    response = client.post(
        "/api/v1/documents",
        files={
            "file": (
                "fake.pdf",
                b"This is not a PDF",
                "application/pdf",
            )
        },
    )

    assert response.status_code == 400
    assert "PDF signature" in response.json()["detail"]
    assert list(document_storage.iterdir()) == []


def test_reject_empty_file(client):
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
    assert "Empty files" in response.json()["detail"]


def test_reject_oversized_file(client, monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "max_upload_size_bytes", 10)

    response = client.post(
        "/api/v1/documents",
        files={
            "file": (
                "large.txt",
                b"A" * 100,
                "text/plain",
            )
        },
    )

    assert response.status_code == 413


def test_duplicate_content_returns_conflict(client, document_storage):
    content = b"Same synthetic invoice content"

    first = client.post(
        "/api/v1/documents",
        files={"file": ("first.txt", content, "text/plain")},
    )
    assert first.status_code == 201

    second = client.post(
        "/api/v1/documents",
        files={"file": ("renamed.txt", content, "text/plain")},
    )

    assert second.status_code == 409
    assert (
        second.json()["detail"]["document_id"]
        == first.json()["id"]
    )

    # The duplicate upload must not leave another stored copy.
    assert len(list(document_storage.iterdir())) == 1


def test_list_documents(client):
    client.post(
        "/api/v1/documents",
        files={"file": ("one.txt", b"first", "text/plain")},
    )
    client.post(
        "/api/v1/documents",
        files={"file": ("two.csv", b"a,b\n1,2", "text/csv")},
    )

    response = client.get("/api/v1/documents")

    assert response.status_code == 200
    assert len(response.json()) == 2


def test_get_document_metadata(client):
    upload = client.post(
        "/api/v1/documents",
        files={"file": ("invoice.txt", b"test data", "text/plain")},
    )
    document_id = upload.json()["id"]

    response = client.get(f"/api/v1/documents/{document_id}")

    assert response.status_code == 200
    assert response.json()["id"] == document_id
    assert "storage_key" not in response.json()


def test_download_document_content(client):
    content = b"Synthetic invoice content"

    upload = client.post(
        "/api/v1/documents",
        files={"file": ("invoice.txt", content, "text/plain")},
    )
    document_id = upload.json()["id"]

    response = client.get(
        f"/api/v1/documents/{document_id}/content"
    )

    assert response.status_code == 200
    assert response.content == content


def test_missing_document_returns_404(client):
    response = client.get("/api/v1/documents/999999")

    assert response.status_code == 404
