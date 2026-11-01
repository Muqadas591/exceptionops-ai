from sqlalchemy.orm import sessionmaker

from app.models.document import Document
from app.models.human_review import HumanReview
from app.models.workflow_run import WorkflowRun
from app.schemas.action_execution import ActionRequest
from app.services.action_connectors import ConnectorOutcome
from app.services import action_execution_service as action_service


ACTION_TOKEN = "test-action-token"


def seed_approved_review(test_engine) -> int:
    """Create a synthetic document, workflow, and approved review."""
    TestingSession = sessionmaker(
        bind=test_engine,
        autoflush=False,
        expire_on_commit=False,
    )

    with TestingSession() as db:
        document = Document(
            original_filename="synthetic-invoice.txt",
            storage_key="synthetic-invoice-stage-84.txt",
            extension=".txt",
            content_type="text/plain",
            file_size_bytes=10,
            checksum_sha256="a" * 64,
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
            status="approved",
            decided_by="synthetic-reviewer",
            decision_note="Synthetic approval for automated testing.",
        )
        db.add(review)
        db.commit()

        return review.id


def action_headers(key: str) -> dict[str, str]:
    return {
        "X-Action-Token": ACTION_TOKEN,
        "Idempotency-Key": key,
    }


def test_repeated_request_returns_existing_action(
    client,
    test_engine,
    monkeypatch,
):
    monkeypatch.setenv(
        "EXCEPTIONOPS_ACTION_TOKEN",
        ACTION_TOKEN,
    )

    review_id = seed_approved_review(test_engine)

    calls = {"count": 0}

    def fake_connector(action_type, payload):
        calls["count"] += 1
        return ConnectorOutcome(
            success=True,
            result={
                "connector": "test",
                "outcome": "completed",
            },
        )

    monkeypatch.setattr(
        action_service,
        "execute_connector",
        fake_connector,
    )

    headers = action_headers("stage84-idempotency-001")
    body = {"action_type": "accounting_simulation"}

    first = client.post(
        f"/api/v1/reviews/{review_id}/actions",
        headers=headers,
        json=body,
    )

    second = client.post(
        f"/api/v1/reviews/{review_id}/actions",
        headers=headers,
        json=body,
    )

    assert first.status_code == 200
    assert second.status_code == 200

    assert first.json()["id"] == second.json()["id"]
    assert first.json()["status"] == "succeeded"
    assert first.json()["attempt_count"] == 1
    assert second.json()["attempt_count"] == 1

    # The connector must not execute a second time.
    assert calls["count"] == 1


def test_same_key_with_different_payload_is_rejected(
    client,
    test_engine,
    monkeypatch,
):
    monkeypatch.setenv(
        "EXCEPTIONOPS_ACTION_TOKEN",
        ACTION_TOKEN,
    )

    review_id = seed_approved_review(test_engine)
    headers = action_headers("stage84-idempotency-002")

    first = client.post(
        f"/api/v1/reviews/{review_id}/actions",
        headers=headers,
        json={"action_type": "accounting_simulation"},
    )

    second = client.post(
        f"/api/v1/reviews/{review_id}/actions",
        headers=headers,
        json={"action_type": "webhook_simulation"},
    )

    assert first.status_code == 200
    assert second.status_code == 409
    assert "different action payload" in second.json()["detail"]


def test_failed_action_can_be_retried(
    client,
    test_engine,
    monkeypatch,
):
    monkeypatch.setenv(
        "EXCEPTIONOPS_ACTION_TOKEN",
        ACTION_TOKEN,
    )

    review_id = seed_approved_review(test_engine)
    calls = {"count": 0}

    def fake_connector(action_type, payload):
        calls["count"] += 1

        if calls["count"] == 1:
            return ConnectorOutcome(
                success=False,
                result={},
                error="Synthetic temporary failure.",
            )

        return ConnectorOutcome(
            success=True,
            result={"outcome": "recovered"},
        )

    monkeypatch.setattr(
        action_service,
        "execute_connector",
        fake_connector,
    )

    created = client.post(
        f"/api/v1/reviews/{review_id}/actions",
        headers=action_headers("stage84-retry-0001"),
        json={"action_type": "accounting_simulation"},
    )

    assert created.status_code == 200
    assert created.json()["status"] == "failed"
    action_id = created.json()["id"]

    retried = client.post(
        f"/api/v1/actions/{action_id}/retry",
        headers={"X-Action-Token": ACTION_TOKEN},
    )

    assert retried.status_code == 200
    assert retried.json()["status"] == "succeeded"
    assert retried.json()["attempt_count"] == 2
    assert calls["count"] == 2


def test_uncertain_action_is_not_blindly_retried(
    client,
    test_engine,
    monkeypatch,
):
    monkeypatch.setenv(
        "EXCEPTIONOPS_ACTION_TOKEN",
        ACTION_TOKEN,
    )

    review_id = seed_approved_review(test_engine)

    def raising_connector(action_type, payload):
        raise TimeoutError("Synthetic connector timeout.")

    monkeypatch.setattr(
        action_service,
        "execute_connector",
        raising_connector,
    )

    created = client.post(
        f"/api/v1/reviews/{review_id}/actions",
        headers=action_headers("stage84-uncertain-001"),
        json={"action_type": "accounting_simulation"},
    )

    assert created.status_code == 200
    assert created.json()["status"] == "uncertain"

    action_id = created.json()["id"]

    retry = client.post(
        f"/api/v1/actions/{action_id}/retry",
        headers={"X-Action-Token": ACTION_TOKEN},
    )

    assert retry.status_code == 409


def test_recovery_queue_contains_uncertain_action(
    client,
    test_engine,
    monkeypatch,
):
    monkeypatch.setenv(
        "EXCEPTIONOPS_ACTION_TOKEN",
        ACTION_TOKEN,
    )

    review_id = seed_approved_review(test_engine)

    def raising_connector(action_type, payload):
        raise TimeoutError("Synthetic timeout.")

    monkeypatch.setattr(
        action_service,
        "execute_connector",
        raising_connector,
    )

    created = client.post(
        f"/api/v1/reviews/{review_id}/actions",
        headers=action_headers("stage84-recovery-001"),
        json={"action_type": "accounting_simulation"},
    )

    action_id = created.json()["id"]

    response = client.get(
        "/api/v1/actions/recovery/queue",
        headers={"X-Action-Token": ACTION_TOKEN},
    )

    assert response.status_code == 200
    assert any(
        item["id"] == action_id
        and item["status"] == "uncertain"
        for item in response.json()
    )


def test_reconciliation_can_mark_action_not_executed(
    client,
    test_engine,
    monkeypatch,
):
    monkeypatch.setenv(
        "EXCEPTIONOPS_ACTION_TOKEN",
        ACTION_TOKEN,
    )

    review_id = seed_approved_review(test_engine)

    def raising_connector(action_type, payload):
        raise TimeoutError("Synthetic timeout.")

    monkeypatch.setattr(
        action_service,
        "execute_connector",
        raising_connector,
    )

    created = client.post(
        f"/api/v1/reviews/{review_id}/actions",
        headers=action_headers("stage84-reconcile-001"),
        json={"action_type": "accounting_simulation"},
    )

    action_id = created.json()["id"]

    response = client.post(
        f"/api/v1/actions/{action_id}/reconcile",
        headers={"X-Action-Token": ACTION_TOKEN},
        json={
            "outcome": "confirmed_not_executed",
            "note": (
                "Synthetic test confirms no external action occurred."
            ),
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "failed"