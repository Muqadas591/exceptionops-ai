
from sqlalchemy import inspect

from app import models  # noqa: F401 - register model tables
from app.db.base import Base


def test_expected_tables_are_registered():
    expected_tables = {
        "suppliers",
        "invoices",
        "purchase_orders",
        "exceptions",
        "audit_events",
        "documents",
        "extraction_results",
    }

    assert expected_tables.issubset(set(Base.metadata.tables.keys()))


def test_invoice_duplicate_constraint_exists():
    invoice_table = Base.metadata.tables["invoices"]

    unique_constraints = {
        constraint.name
        for constraint in invoice_table.constraints
        if constraint.__class__.__name__ == "UniqueConstraint"
    }

    assert "uq_invoice_supplier_number" in unique_constraints


def test_document_checksum_constraint_exists():
    document_table = Base.metadata.tables["documents"]

    unique_constraints = {
        constraint.name
        for constraint in document_table.constraints
        if constraint.__class__.__name__ == "UniqueConstraint"
    }

    assert "uq_document_checksum_sha256" in unique_constraints


def test_extraction_result_unique_document_constraint_exists():
    table = Base.metadata.tables["extraction_results"]

    unique_constraints = {
        constraint.name
        for constraint in table.constraints
        if constraint.__class__.__name__ == "UniqueConstraint"
    }

    assert "uq_extraction_result_document_id" in unique_constraints


def test_models_can_be_created_in_test_database(test_engine):
    table_names = set(inspect(test_engine).get_table_names())

    expected = {
        "suppliers",
        "invoices",
        "purchase_orders",
        "exceptions",
        "audit_events",
        "documents",
        "extraction_results",
    }

    assert expected.issubset(table_names)
