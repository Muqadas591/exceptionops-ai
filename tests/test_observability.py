import uuid

from sqlalchemy.orm import Session

from app.models.document import Document
from app.models.human_review import HumanReview
from app.models.workflow_run import WorkflowRun


def set_reviewer_auth(monkeypatch):
    """Configure the existing shared-token authentication for tests."""
    monkeypatch.setenv(
        "EXCEPTIONOPS_REVIEWER_TOKEN",
        "test-reviewer-token",
    )

    return {
        "X-Reviewer-Token": "test-reviewer-token",
    }


def test_response_contains_generated_request_id(client):
    response = client.get("/")

    assert response.status_code == 200

    request_id = response.headers.get("X-Request-ID")

    assert request_id is not None
    uuid.UUID(request_id)


def test_valid_request_id_is_preserved(client):
    request_id = "test-request-123"

    response = client.get(
        "/",
        headers={"X-Request-ID": request_id},
    )

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == request_id


def test_invalid_request_id_is_replaced(client):
    response = client.get(
        "/",
       headers={"X-Request-ID": "invalid/request?id"},
    )

    assert response.status_code == 200

    request_id = response.headers["X-Request-ID"]

    assert request_id != "invalid request id\n"
    uuid.UUID(request_id)


def test_health_endpoint_contains_request_id(client):
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.headers.get("X-Request-ID")


def test_review_queue_returns_pagination_metadata(
    client,
    monkeypatch,
):
    headers = set_reviewer_auth(monkeypatch)

    response = client.get(
        "/api/v1/reviews/queue?limit=20&offset=0",
        headers=headers,
    )

    assert response.status_code == 200
    assert isinstance(response.json(), list)

    assert response.headers["X-Total-Count"] == "0"
    assert response.headers["X-Page-Limit"] == "20"
    assert response.headers["X-Page-Offset"] == "0"
    assert response.headers["X-Has-More"] == "false"


def test_review_queue_rejects_limit_above_maximum(
    client,
    monkeypatch,
):
    headers = set_reviewer_auth(monkeypatch)

    response = client.get(
        "/api/v1/reviews/queue?limit=101",
        headers=headers,
    )

    assert response.status_code == 422
    assert "request_id" in response.json()


def test_review_queue_rejects_negative_offset(
    client,
    monkeypatch,
):
    headers = set_reviewer_auth(monkeypatch)

    response = client.get(
        "/api/v1/reviews/queue?offset=-1",
        headers=headers,
    )

    assert response.status_code == 422
    assert "request_id" in response.json()


def test_review_queue_rejects_invalid_status(
    client,
    monkeypatch,
):
    headers = set_reviewer_auth(monkeypatch)

    response = client.get(
        "/api/v1/reviews/queue?status=unknown",
        headers=headers,
    )

    assert response.status_code == 422
    assert "request_id" in response.json()


def test_review_queue_paginates_records(
    client,
    test_engine,
    monkeypatch,
):
    headers = set_reviewer_auth(monkeypatch)

    # Seed three synthetic reviews in the isolated test database.
    with Session(test_engine) as db:
        for number in range(1, 4):
            document = Document(
                original_filename=f"synthetic-{number}.txt",
                storage_key=f"synthetic-{number}.txt",
                extension=".txt",
                content_type="text/plain",
                file_size_bytes=10,
                checksum_sha256=f"{number:064x}",
                status="received",
            )

            db.add(document)
            db.flush()

            workflow = WorkflowRun(
                document_id=document.id,
                status="needs_review",
                attempt_count=0,
            )

            db.add(workflow)
            db.flush()

            review = HumanReview(
                workflow_run_id=workflow.id,
                status="pending",
            )

            db.add(review)

        db.commit()

    first_page = client.get(
        "/api/v1/reviews/queue?limit=2&offset=0",
        headers=headers,
    )

    assert first_page.status_code == 200
    assert len(first_page.json()) == 2
    assert first_page.headers["X-Total-Count"] == "3"
    assert first_page.headers["X-Has-More"] == "true"

    second_page = client.get(
        "/api/v1/reviews/queue?limit=2&offset=2",
        headers=headers,
    )

    assert second_page.status_code == 200
    assert len(second_page.json()) == 1
    assert second_page.headers["X-Total-Count"] == "3"
    assert second_page.headers["X-Has-More"] == "false"

    first_ids = {
        item["id"]
        for item in first_page.json()
    }
    second_ids = {
        item["id"]
        for item in second_page.json()
    }

    assert first_ids.isdisjoint(second_ids)