def test_workflow_routes_are_registered(client):
    response = client.get("/openapi.json")

    assert response.status_code == 200

    paths = response.json()["paths"]

    assert "/api/v1/documents/{document_id}/workflow" in paths
    assert "/api/v1/workflows/{workflow_id}" in paths
    assert "/api/v1/workflows/{workflow_id}/advance" in paths
    assert "/api/v1/workflows/{workflow_id}/retry" in paths
    assert "/api/v1/workflows/{workflow_id}/resolve" in paths
    assert "/api/v1/workflows/{workflow_id}/cancel" in paths


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