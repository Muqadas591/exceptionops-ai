
from fastapi import Depends

from app.core.authentication import require_roles
from app.models.user import User


def require_admin(
    user: User = Depends(
        require_roles("admin")
    ),
) -> str:
    """Allow administrators only."""
    return user.email


def require_reviewer(
    user: User = Depends(
        require_roles("admin", "reviewer")
    ),
) -> str:
    """Allow administrators and reviewers."""
    return user.email


def require_action_operator(
    user: User = Depends(
        require_roles("admin", "action_operator")
    ),
) -> str:
    """Allow administrators and action operators."""
    return user.email


def require_audit_reader(
    user: User = Depends(
        require_roles("admin", "action_operator")
    ),
) -> str:
    """Allow administrators and action operators to inspect audit data."""
    return user.email
