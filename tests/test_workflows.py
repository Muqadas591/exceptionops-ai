from sqlalchemy.orm import Session

from app.models.document import Document
from app.models.workflow_run import WorkflowRun


def test_workflow_routes_are_registered(client):
    response = client.get("/openapi.json")

    assert response.status_code == 200

    paths = response.json()["paths"]

    assert "/api/v1/documents/{document_id}/workflow" in paths
    assert "/api/v1/workflows" in paths
    assert "get" in paths["/api/v1/workflows"]
    assert "/api/v1/workflows/{workflow_id}" in paths
    assert "/api/v1/workflows/{workflow_id}/advance" in paths
    assert "/api/v1/workflows/{workflow_id}/retry" in paths
    assert "/api/v1/workflows/{workflow_id}/resolve" in paths
    assert "/api/v1/workflows/{workflow_id}/cancel" in paths


def test_workflow_list_returns_pagination_headers(client):
    response = client.get(
        "/api/v1/workflows?limit=10&offset=0"
    )

    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert response.headers["X-Total-Count"] == "0"
    assert response.headers["X-Page-Limit"] == "10"
    assert response.headers["X-Page-Offset"] == "0"
    assert response.headers["X-Has-More"] == "false"


def test_workflow_listing_filters_and_paginates(
    client,
    test_engine,
):
    with Session(test_engine) as db:
        document_ids = []
        for number in range(1, 4):
            document = Document(
                original_filename=f"workflow-list-{number}.txt",
                storage_key=f"workflow-list-{number}.txt",
                extension=".txt",
                content_type="text/plain",
                file_size_bytes=10,
                checksum_sha256=f"{number:064x}",
                status="received",
            )
            db.add(document)
            db.flush()
            document_ids.append(document.id)

            db.add(
                WorkflowRun(
                    document_id=document.id,
                    status=(
                        "needs_review"
                        if number < 3
                        else "received"
                    ),
                    attempt_count=0,
                )
            )
        db.commit()

    first_page = client.get(
        "/api/v1/workflows?status=needs_review&limit=1&offset=0"
    )
    second_page = client.get(
        "/api/v1/workflows?status=needs_review&limit=1&offset=1"
    )

    assert first_page.status_code == 200
    assert second_page.status_code == 200
    assert len(first_page.json()) == 1
    assert len(second_page.json()) == 1
    assert first_page.headers["X-Total-Count"] == "2"
    assert second_page.headers["X-Total-Count"] == "2"
    assert first_page.json()[0]["id"] != second_page.json()[0]["id"]
    assert all(
        item["status"] == "needs_review"
        for item in first_page.json() + second_page.json()
    )

    document_page = client.get(
        f"/api/v1/workflows?document_id={document_ids[0]}"
    )
    assert document_page.status_code == 200
    assert document_page.headers["X-Total-Count"] == "1"
    assert document_page.json()[0]["document_id"] == document_ids[0]


def test_workflow_creation_requires_existing_document(client):
    response = client.post(
        "/api/v1/documents/999999/workflow"
    )

    assert response.status_code == 404


def test_reading_missing_workflow_returns_404(client):
    response = client.get("/api/v1/workflows/999999")

    assert response.status_code == 404


def test_advancing_missing_workflow_returns_404(client):
    response = client.post(
        "/api/v1/workflows/999999/advance"
    )

    assert response.status_code == 404


def test_cancelling_missing_workflow_returns_404(client):
    response = client.post(
        "/api/v1/workflows/999999/cancel"
    )

    assert response.status_code == 404