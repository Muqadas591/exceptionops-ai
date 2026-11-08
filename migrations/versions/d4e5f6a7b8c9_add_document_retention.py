
"""Add document content retention lifecycle fields.

Revision ID: d4e5f6a7b8c9
Revises: c97adb9362a1
"""

from alembic import op
import sqlalchemy as sa


revision = "d4e5f6a7b8c9"
down_revision = "c97adb9362a1"

branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "documents",
        sa.Column(
            "content_status",
            sa.String(length=30),
            server_default="available",
            nullable=False,
        ),
    )

    op.add_column(
        "documents",
        sa.Column(
            "content_deleted_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )

    op.add_column(
        "documents",
        sa.Column(
            "content_deletion_reason",
            sa.Text(),
            nullable=True,
        ),
    )

    op.add_column(
        "documents",
        sa.Column(
            "content_deleted_by",
            sa.String(length=320),
            nullable=True,
        ),
    )

    op.create_check_constraint(
        "ck_documents_content_status",
        "documents",
        (
            "content_status IN "
            "('available', 'deletion_pending', 'deleted')"
        ),
    )

    op.create_index(
        "ix_documents_content_status",
        "documents",
        ["content_status"],
    )

    op.create_index(
        "ix_documents_content_status_created",
        "documents",
        ["content_status", "created_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_documents_content_status_created",
        table_name="documents",
    )

    op.drop_index(
        "ix_documents_content_status",
        table_name="documents",
    )

    op.drop_constraint(
        "ck_documents_content_status",
        "documents",
        type_="check",
    )

    op.drop_column(
        "documents",
        "content_deleted_by",
    )

    op.drop_column(
        "documents",
        "content_deletion_reason",
    )

    op.drop_column(
        "documents",
        "content_deleted_at",
    )

    op.drop_column(
        "documents",
        "content_status",
    )
