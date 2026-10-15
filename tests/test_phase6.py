def test_phase6_routes_are_registered(client):
    response = client.get("/openapi.json")

    assert response.status_code == 200
    paths = response.json()["paths"]

    assert "/api/v1/reviews/queue" in paths
    assert "/api/v1/workflows/{workflow_id}/review" in paths
    assert "/api/v1/reviews/{review_id}/assign" in paths
    assert "/api/v1/reviews/{review_id}/comments" in paths
    assert "/api/v1/reviews/{review_id}/request-correction" in paths
    assert "/api/v1/reviews/{review_id}/approve" in paths
    assert "/api/v1/reviews/{review_id}/reject" in paths
    assert "/api/v1/reviews/{review_id}/actions" in paths
    assert "/api/v1/actions/{action_id}/retry" in paths


def test_action_execution_requires_authorization(
    client,
    monkeypatch,
):
    monkeypatch.delenv(
        "EXCEPTIONOPS_ACTION_TOKEN",
        raising=False,
    )

    response = client.post(
        "/api/v1/reviews/999/actions",
        json={"action_type": "accounting_simulation"},
    )

    assert response.status_code == 503


def test_review_queue_requires_authorization(
    client,
    monkeypatch,
):
    monkeypatch.delenv(
        "EXCEPTIONOPS_REVIEWER_TOKEN",
        raising=False,
    )

    response = client.get("/api/v1/reviews/queue")

    assert response.status_code == 503


def test_action_does_not_execute_for_missing_review(
    client,
    monkeypatch,
):
    monkeypatch.setenv(
        "EXCEPTIONOPS_ACTION_TOKEN",
        "test-action-token",
    )

    response = client.post(
        "/api/v1/reviews/999/actions",
        headers={"X-Action-Token": "test-action-token"},
        json={"action_type": "accounting_simulation"},
    )

    assert response.status_code == 404


def test_unsupported_action_type_is_rejected(
    client,
    monkeypatch,
):
    monkeypatch.setenv(
        "EXCEPTIONOPS_ACTION_TOKEN",
        "test-action-token",
    )

    response = client.post(
        "/api/v1/reviews/999/actions",
        headers={"X-Action-Token": "test-action-token"},
        json={"action_type": "execute_arbitrary_url"},
    )

    assert response.status_code == 422