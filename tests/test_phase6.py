
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
    review_actions_path = "/api/v1/reviews/{review_id}/actions"
    assert review_actions_path in paths
    assert "get" in paths[review_actions_path]
    assert "/api/v1/actions/{action_id}/retry" in paths


def test_review_action_history_route_is_registered(client):
    response = client.get("/openapi.json")

    assert response.status_code == 200
    paths = response.json()["paths"]
    history_path = paths["/api/v1/reviews/{review_id}/actions"]

    assert "get" in history_path
    assert "post" in history_path


def test_review_queue_rejects_unauthenticated_request(
    unauthenticated_client,
):
    response = unauthenticated_client.get(
        "/api/v1/reviews/queue"
    )

    assert response.status_code == 401


def test_action_execution_rejects_unauthenticated_request(
    unauthenticated_client,
):
    response = unauthenticated_client.post(
        "/api/v1/reviews/999/actions",
        headers={
            "Idempotency-Key": "stage84-phase6-auth",
        },
        json={"action_type": "accounting_simulation"},
    )

    assert response.status_code == 401


def test_review_action_history_rejects_unauthenticated_request(
    unauthenticated_client,
):
    response = unauthenticated_client.get(
        "/api/v1/reviews/999/actions",
    )

    assert response.status_code == 401


def test_action_does_not_execute_for_missing_review(client):
    response = client.post(
        "/api/v1/reviews/999/actions",
        headers={
            "X-Action-Token": "test-action-token",
            "Idempotency-Key": "stage84-phase6-missing",
        },
        json={"action_type": "accounting_simulation"},
    )

    assert response.status_code == 404


def test_unsupported_action_type_is_rejected(client):
    response = client.post(
        "/api/v1/reviews/999/actions",
        headers={
            "X-Action-Token": "test-action-token",
            "Idempotency-Key": "stage84-phase6-invalid",
        },
        json={"action_type": "execute_arbitrary_url"},
    )

    assert response.status_code == 422
