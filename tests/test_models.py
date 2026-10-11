
from sqlalchemy import inspect

from app.db.base import Base
from app import models  # noqa: F401 - register model tables


def test_expected_tables_are_registered():
    expected_tables = {
        "suppliers",
        "invoices",
        "purchase_orders",
        "exceptions",
        "audit_events",
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


def test_models_can_be_created_in_test_database(test_engine):
    inspector = inspect(test_engine)
    table_names = set(inspector.get_table_names())

    assert "suppliers" in table_names
    assert "invoices" in table_names
    assert "purchase_orders" in table_names
    assert "exceptions" in table_names
    assert "audit_events" in table_names
