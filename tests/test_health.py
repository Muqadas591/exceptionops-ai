
def test_root_endpoint(client):
    response = client.get("/")

    assert response.status_code == 200
    body = response.json()
    assert body["application"] == "ExceptionOps AI"
    assert body["status"] == "running"
    assert body["docs"] == "/docs"


def test_health_endpoint(client):
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["app_name"] == "ExceptionOps AI"


def test_readiness_endpoint(client):
    response = client.get("/api/v1/ready")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ready",
        "database": "connected",
    }


def test_openapi_documentation_is_available(client):
    response = client.get("/openapi.json")

    assert response.status_code == 200
    assert "paths" in response.json()
