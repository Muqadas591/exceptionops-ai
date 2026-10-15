import hmac
import os
from typing import Annotated

from fastapi import Depends, Header, HTTPException


def _require_token(
    supplied_token: str | None,
    environment_variable: str,
    role_name: str,
) -> str:
    expected_token = os.getenv(environment_variable)

    # Fail closed: missing server configuration must not disable auth.
    if not expected_token:
        raise HTTPException(
            status_code=503,
            detail=f"{role_name} authorization is not configured.",
        )

    if not supplied_token or not hmac.compare_digest(
        supplied_token,
        expected_token,
    ):
        raise HTTPException(
            status_code=403,
            detail=f"{role_name} authorization failed.",
        )

    return role_name


def require_reviewer(
    x_reviewer_token: Annotated[
        str | None,
        Header(alias="X-Reviewer-Token"),
    ] = None,
) -> str:
    _require_token(
        x_reviewer_token,
        "EXCEPTIONOPS_REVIEWER_TOKEN",
        "reviewer",
    )
    return "reviewer"


def require_action_operator(
    x_action_token: Annotated[
        str | None,
        Header(alias="X-Action-Token"),
    ] = None,
) -> str:
    _require_token(
        x_action_token,
        "EXCEPTIONOPS_ACTION_TOKEN",
        "action operator",
    )
    return "action_operator"