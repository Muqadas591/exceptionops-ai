from sqlalchemy.orm import Session

from app.core.observability import request_id_context
from app.models.audit_event import AuditEvent
from app.models.document import Document
from app.models.workflow_run import WorkflowRun
from app.services.audit_service import record_audit_event


def test_audit_events_route_requires_authentication(
    unauthenticated_client,
):
    response = unauthenticated_client.get(
        "/api/v1/audit/events"
    )

    assert response.status_code == 401


def test_audit_events_returns_paginated_records(
    client,
    test_engine,
):
    with Session(test_engine) as db:
        for number in range(1, 4):
            db.add(
                AuditEvent(
                    event_type="document.uploaded",
                    entity_type="document",
                    entity_id=str(number),
                    actor_type="system",
                    description=f"Synthetic upload {number}.",
                    event_metadata={"number": number},
                )
            )
        db.commit()

    response = client.get(
        "/api/v1/audit/events?limit=2&offset=1"
    )

    assert response.status_code == 200
    assert len(response.json()) == 2
    assert response.headers["X-Total-Count"] == "3"
    assert response.headers["X-Page-Limit"] == "2"
    assert response.headers["X-Page-Offset"] == "1"
    assert response.headers["X-Has-More"] == "false"


def test_audit_event_records_correlation_actor_and_request_id(
    test_engine,
):
    with Session(test_engine) as db:
        document = Document(
            original_filename="synthetic-audit.txt",
            storage_key="synthetic-audit.txt",
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
            status="received",
            attempt_count=0,
        )
        db.add(workflow)
        db.flush()

        context_token = request_id_context.set("audit-test-request")
        try:
            event = record_audit_event(
                db,
                event_type="workflow.test",
                entity_type="workflow",
                entity_id=workflow.id,
                description="Synthetic workflow audit event.",
                actor_type="user",
                actor_id="audit-user@example.com",
                document_id=document.id,
                workflow_run_id=workflow.id,
                metadata={"source": "test"},
            )
        finally:
            request_id_context.reset(context_token)

        db.commit()
        db.refresh(event)

        assert event.document_id == document.id
        assert event.workflow_run_id == workflow.id
        assert event.actor_type == "user"
        assert event.actor_id == "audit-user@example.com"
        assert event.event_metadata == {
            "source": "test",
            "request_id": "audit-test-request",
        }


def test_document_upload_extraction_and_evaluation_events_persist(
    client,
    test_engine,
):
    upload = client.post(
        "/api/v1/documents",
        files={
            "file": (
                "audit-events-invoice.txt",
                (
                    "Supplier: North Star Supplies\n"
                    "Invoice Number: AUDIT-EVENT-001\n"
                    "Invoice Date: 2026-10-10\n"
                    "Due Date: 2026-10-30\n"
                    "Currency: PKR\n"
                    "Total: 2500.00\n"
                ).encode("utf-8"),
                "text/plain",
            )
        },
    )
    assert upload.status_code == 201
    document_id = upload.json()["id"]
    request_id = upload.headers["X-Request-ID"]

    extraction = client.post(
        f"/api/v1/documents/{document_id}/extract",
        headers={"X-Request-ID": "audit-extraction-request"},
    )
    evaluation = client.post(
        f"/api/v1/documents/{document_id}/evaluate",
        headers={"X-Request-ID": "audit-evaluation-request"},
    )

    assert extraction.status_code == 200
    assert evaluation.status_code == 200

    with Session(test_engine) as db:
        events = (
            db.query(AuditEvent)
            .filter(AuditEvent.document_id == document_id)
            .all()
        )

    events_by_type = {event.event_type: event for event in events}
    assert {
        "document.uploaded",
        "document.extraction_completed",
        "document.evaluation_completed",
    }.issubset(events_by_type)
    assert events_by_type["document.uploaded"].event_metadata[
        "request_id"
    ] == request_id
    assert events_by_type[
        "document.extraction_completed"
    ].event_metadata["request_id"] == "audit-extraction-request"
    assert events_by_type[
        "document.evaluation_completed"
    ].event_metadata["request_id"] == "audit-evaluation-request"
