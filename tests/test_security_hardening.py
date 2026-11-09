
from starlette.requests import Request
from starlette.responses import Response

from app.core.security_headers import apply_security_headers


def make_request(
    path="/api/v1/health",
    scheme="http",
):
    return Request(
        {
            "type": "http",
            "http_version": "1.1",
            "method": "GET",
            "scheme": scheme,
            "path": path,
            "raw_path": path.encode(),
            "query_string": b"",
            "headers": [],
            "server": ("testserver", 443 if scheme == "https" else 80),
            "client": ("testclient", 12345),
        }
    )


def test_api_response_contains_security_headers(
    client,
):
    response = client.get(
        "/api/v1/health"
    )

    assert response.status_code == 200

    assert response.headers[
        "X-Content-Type-Options"
    ] == "nosniff"

    assert response.headers[
        "X-Frame-Options"
    ] == "DENY"

    assert response.headers[
        "Referrer-Policy"
    ] == "no-referrer"

    assert response.headers[
        "Permissions-Policy"
    ] == (
        "camera=(), microphone=(), geolocation=()"
    )

    assert response.headers[
        "Cache-Control"
    ] == "no-store"

    assert response.headers[
        "Pragma"
    ] == "no-cache"

    assert response.headers.get(
        "X-Request-ID"
    )


def test_non_api_response_contains_baseline_headers(
    client,
):
    response = client.get("/")

    assert response.status_code == 200

    assert response.headers[
        "X-Content-Type-Options"
    ] == "nosniff"

    assert response.headers[
        "X-Frame-Options"
    ] == "DENY"

    assert response.headers[
        "Referrer-Policy"
    ] == "no-referrer"


def test_hsts_is_only_added_for_production_https():
    secure_request = make_request(
        scheme="https",
    )

    secure_response = Response()

    apply_security_headers(
        secure_response,
        secure_request,
        is_production=True,
        api_prefix="/api/v1",
    )

    assert secure_response.headers[
        "Strict-Transport-Security"
    ] == "max-age=31536000"

    insecure_request = make_request(
        scheme="http",
    )

    insecure_response = Response()

    apply_security_headers(
        insecure_response,
        insecure_request,
        is_production=True,
        api_prefix="/api/v1",
    )

    assert (
        "Strict-Transport-Security"
        not in insecure_response.headers
    )


def test_hsts_is_not_added_in_development():
    request = make_request(
        scheme="https",
    )

    response = Response()

    apply_security_headers(
        response,
        request,
        is_production=False,
        api_prefix="/api/v1",
    )

    assert (
        "Strict-Transport-Security"
        not in response.headers
    )
