"""add audit event correlation fields

Revision ID: c97adb9362a1
Revises: 2ed3a17e76d3
Create Date: 2026-11-05 21:50:16.212675

"""
from typing import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "c97adb9362a1"
down_revision: str | None = "2ed3a17e76d3"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "audit_events",
        sa.Column("document_id", sa.Integer(), nullable=True),
    )

    op.add_column(
        "audit_events",
        sa.Column("workflow_run_id", sa.Integer(), nullable=True),
    )

    op.add_column(
        "audit_events",
        sa.Column("review_id", sa.Integer(), nullable=True),
    )

    op.add_column(
        "audit_events",
        sa.Column("action_id", sa.Integer(), nullable=True),
    )

    op.create_index(
        "ix_audit_events_document_id",
        "audit_events",
        ["document_id"],
    )

    op.create_index(
        "ix_audit_events_workflow_run_id",
        "audit_events",
        ["workflow_run_id"],
    )

    op.create_index(
        "ix_audit_events_review_id",
        "audit_events",
        ["review_id"],
    )

    op.create_index(
        "ix_audit_events_action_id",
        "audit_events",
        ["action_id"],
    )

    op.create_index(
        "ix_audit_events_document_created",
        "audit_events",
        ["document_id", "created_at"],
    )

    op.create_index(
        "ix_audit_events_workflow_created",
        "audit_events",
        ["workflow_run_id", "created_at"],
    )

    op.create_index(
        "ix_audit_events_review_created",
        "audit_events",
        ["review_id", "created_at"],
    )

    op.create_index(
        "ix_audit_events_action_created",
        "audit_events",
        ["action_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_audit_events_action_created",
        table_name="audit_events",
    )
    op.drop_index(
        "ix_audit_events_review_created",
        table_name="audit_events",
    )
    op.drop_index(
        "ix_audit_events_workflow_created",
        table_name="audit_events",
    )
    op.drop_index(
        "ix_audit_events_document_created",
        table_name="audit_events",
    )

    op.drop_index(
        "ix_audit_events_action_id",
        table_name="audit_events",
    )
    op.drop_index(
        "ix_audit_events_review_id",
        table_name="audit_events",
    )
    op.drop_index(
        "ix_audit_events_workflow_run_id",
        table_name="audit_events",
    )
    op.drop_index(
        "ix_audit_events_document_id",
        table_name="audit_events",
    )

    op.drop_column("audit_events", "action_id")
    op.drop_column("audit_events", "review_id")
    op.drop_column("audit_events", "workflow_run_id")
    op.drop_column("audit_events", "document_id")