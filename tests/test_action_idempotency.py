from sqlalchemy.orm import Session, sessionmaker

from app.models.action_execution import ActionExecution
from app.models.audit_event import AuditEvent
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


def seed_action_execution(
    test_engine,
    review_id: int,
    *,
    status: str,
) -> int:
    TestingSession = sessionmaker(
        bind=test_engine,
        autoflush=False,
        expire_on_commit=False,
    )

    with TestingSession() as db:
        action = ActionExecution(
            review_id=review_id,
            action_type="accounting_simulation",
            status=status,
            attempt_count=1,
            idempotency_key=f"test-action-{status}",
            request_fingerprint="0" * 64,
            request_payload={},
            result_payload=None,
            last_error="Synthetic failure." if status == "failed" else None,
            executed_by="synthetic-operator",
        )
        db.add(action)
        db.commit()
        return action.id


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

    with Session(test_engine) as db:
        audit_events = (
            db.query(AuditEvent)
            .filter(AuditEvent.action_id == first.json()["id"])
            .all()
        )

    assert {
        event.event_type for event in audit_events
    } >= {
        "action.created",
        "action.execution_started",
        "action.execution_succeeded",
    }
    assert all(
        event.document_id is not None
        and event.workflow_run_id is not None
        and event.review_id == review_id
        for event in audit_events
    )


def test_review_action_history_is_newest_first_and_paginated(
    client,
    test_engine,
    monkeypatch,
):
    monkeypatch.setenv(
        "EXCEPTIONOPS_ACTION_TOKEN",
        ACTION_TOKEN,
    )

    review_id = seed_approved_review(test_engine)
    monkeypatch.setattr(
        action_service,
        "execute_connector",
        lambda action_type, payload: ConnectorOutcome(
            success=True,
            result={"outcome": "completed"},
        ),
    )

    created_ids = []
    for index in range(2):
        response = client.post(
            f"/api/v1/reviews/{review_id}/actions",
            headers=action_headers(f"stage84-history-{index:03d}"),
            json={"action_type": "accounting_simulation"},
        )
        assert response.status_code == 200
        created_ids.append(response.json()["id"])

    newest = client.get(
        f"/api/v1/reviews/{review_id}/actions?limit=1",
        headers={"X-Action-Token": ACTION_TOKEN},
    )
    older = client.get(
        f"/api/v1/reviews/{review_id}/actions?limit=1&offset=1",
        headers={"X-Action-Token": ACTION_TOKEN},
    )

    assert newest.status_code == 200
    assert older.status_code == 200
    assert [newest.json()[0]["id"], older.json()[0]["id"]] == list(
        reversed(created_ids)
    )


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

    with Session(test_engine) as db:
        event_types = {
            event.event_type
            for event in db.query(AuditEvent)
            .filter(AuditEvent.action_id == action_id)
            .all()
        }

    assert "action.retry_requested" in event_types


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


def test_recovery_service_includes_failed_actions(
    test_engine,
):
    review_id = seed_approved_review(test_engine)
    action_id = seed_action_execution(
        test_engine,
        review_id,
        status="failed",
    )
    TestingSession = sessionmaker(
        bind=test_engine,
        autoflush=False,
        expire_on_commit=False,
    )

    with TestingSession() as db:
        actions = action_service.list_recovery_actions(db)

    assert action_id in [action.id for action in actions]


def test_in_progress_action_cannot_be_reconciled(
    client,
    test_engine,
):
    review_id = seed_approved_review(test_engine)
    action_id = seed_action_execution(
        test_engine,
        review_id,
        status="in_progress",
    )

    response = client.post(
        f"/api/v1/actions/{action_id}/reconcile",
        json={
            "outcome": "confirmed_succeeded",
            "note": "Synthetic test reconciliation note.",
        },
    )

    assert response.status_code == 409


def test_uncertain_action_can_be_reconciled(
    client,
    test_engine,
):
    review_id = seed_approved_review(test_engine)
    action_id = seed_action_execution(
        test_engine,
        review_id,
        status="uncertain",
    )

    response = client.post(
        f"/api/v1/actions/{action_id}/reconcile",
        json={
            "outcome": "confirmed_succeeded",
            "note": "Synthetic test reconciliation note.",
        },
    )

    assert response.status_code == 200
    assert response.json()["id"] == action_id
    assert response.json()["status"] == "succeeded"

    with Session(test_engine) as db:
        event_types = {
            event.event_type
            for event in db.query(AuditEvent)
            .filter(AuditEvent.action_id == action_id)
            .all()
        }

    assert "action.reconciled" in event_types


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