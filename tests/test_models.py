
from sqlalchemy import inspect

# Import all models so SQLAlchemy registers their tables
# in Base.metadata before the tests run.
import app.models  # noqa: F401

from app.db.base import Base


EXPECTED_TABLES = {
    "suppliers",
    "invoices",
    "purchase_orders",
    "exceptions",  # Actual table name in your project
    "audit_events",
    "documents",
    "extraction_results",
    "business_evaluations",
    "workflow_runs",
    "workflow_events",
    "human_reviews",
    "review_comments",
    "action_executions",
}


def test_expected_tables_are_registered():
    """Verify that all Phase 1-4 models are registered."""
    registered_tables = set(Base.metadata.tables.keys())

    missing_tables = EXPECTED_TABLES - registered_tables

    assert not missing_tables, (
        f"These tables are missing from SQLAlchemy metadata: "
        f"{sorted(missing_tables)}. "
        f"Registered tables: {sorted(registered_tables)}"
    )


def test_models_can_be_created_in_test_database(test_engine):
    """Verify that the registered models can create database tables."""
    table_names = set(inspect(test_engine).get_table_names())

    missing_tables = EXPECTED_TABLES - table_names

    assert not missing_tables, (
        f"These tables are missing from the test database: "
        f"{sorted(missing_tables)}. "
        f"Created tables: {sorted(table_names)}"
    )


def test_document_checksum_unique_constraint():
    """Prevent identical document files from being ingested twice."""
    document_table = Base.metadata.tables["documents"]

    constraint_names = {
        constraint.name
        for constraint in document_table.constraints
    }

    assert "uq_document_checksum_sha256" in constraint_names


def test_extraction_result_unique_constraint():
    """Allow one current extraction result per document."""
    extraction_table = Base.metadata.tables["extraction_results"]

    constraint_names = {
        constraint.name
        for constraint in extraction_table.constraints
    }

    assert "uq_extraction_result_document_id" in constraint_names


def test_business_evaluation_unique_constraint():
    """Allow one current business evaluation per document."""
    evaluation_table = Base.metadata.tables["business_evaluations"]

    constraint_names = {
        constraint.name
        for constraint in evaluation_table.constraints
    }

    assert "uq_business_evaluation_document_id" in constraint_names


def test_business_evaluation_has_risk_score_constraint():
    """Ensure the risk score has a database-level range constraint."""
    evaluation_table = Base.metadata.tables["business_evaluations"]

    constraint_names = {
        constraint.name
        for constraint in evaluation_table.constraints
    }

    assert "ck_business_evaluation_risk_score" in constraint_names
