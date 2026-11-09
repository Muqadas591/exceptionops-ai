
from fastapi import Request
from starlette.responses import Response


def apply_security_headers(
    response: Response,
    request: Request,
    *,
    is_production: bool,
    api_prefix: str,
) -> Response:
    """
    Apply baseline browser security headers.

    HSTS is only emitted for production HTTPS requests.
    API responses are marked as non-cacheable.
    """

    response.headers.setdefault(
        "X-Content-Type-Options",
        "nosniff",
    )

    response.headers.setdefault(
        "X-Frame-Options",
        "DENY",
    )

    response.headers.setdefault(
        "Referrer-Policy",
        "no-referrer",
    )

    response.headers.setdefault(
        "Permissions-Policy",
        "camera=(), microphone=(), geolocation=()",
    )

    path = request.url.path

    if (
        path == api_prefix
        or path.startswith(api_prefix.rstrip("/") + "/")
    ):
        response.headers["Cache-Control"] = "no-store"
        response.headers["Pragma"] = "no-cache"

    if (
        is_production
        and request.url.scheme.lower() == "https"
    ):
        response.headers.setdefault(
            "Strict-Transport-Security",
            "max-age=31536000",
        )

    return response
