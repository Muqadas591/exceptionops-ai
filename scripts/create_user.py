import argparse
import getpass

from sqlalchemy import func, select

from app.core.authentication import hash_password
from app.db.session import SessionLocal
from app.models.user import User


VALID_ROLES = {
    "admin",
    "reviewer",
    "action_operator",
}


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create an ExceptionOps AI user."
    )

    parser.add_argument(
        "--email",
        required=True,
        help="Email address for the new user.",
    )

    parser.add_argument(
        "--role",
        choices=sorted(VALID_ROLES),
        default="reviewer",
    )

    args = parser.parse_args()

    email = args.email.strip().lower()

    password = getpass.getpass("New password: ")
    confirmation = getpass.getpass("Confirm password: ")

    if password != confirmation:
        raise SystemExit("Passwords do not match.")

    if len(password) < 12:
        raise SystemExit(
            "Use a password containing at least 12 characters."
        )

    with SessionLocal() as db:
        existing_user = db.scalar(
            select(User).where(
                func.lower(User.email) == email
            )
        )

        if existing_user is not None:
            raise SystemExit(
                "A user with this email already exists."
            )

        user = User(
            email=email,
            password_hash=hash_password(password),
            role=args.role,
            is_active=True,
        )

        db.add(user)
        db.commit()

        print(
            f"Created user {user.email} "
            f"with role {user.role}."
        )


if __name__ == "__main__":
    main()