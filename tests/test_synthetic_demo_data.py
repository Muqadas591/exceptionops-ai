import csv

from scripts.generate_synthetic_demo_data import (
    FIELDS,
    SYNTHETIC_INVOICES,
    generate_dataset,
)


def test_generated_dataset_contains_all_expected_scenarios(tmp_path):
    output_path = tmp_path / "demo_invoices.csv"

    generated_path = generate_dataset(output_path)

    assert generated_path.exists()

    with generated_path.open(
        "r",
        newline="",
        encoding="utf-8",
    ) as csv_file:
        rows = list(csv.DictReader(csv_file))

    assert len(rows) == len(SYNTHETIC_INVOICES)

    scenarios = {row["scenario"] for row in rows}

    assert scenarios == {
        "matched_invoice",
        "amount_mismatch",
        "duplicate_candidate",
        "invalid_amount",
        "missing_purchase_order",
        "supplier_mismatch",
    }


def test_generated_dataset_has_required_fields(tmp_path):
    output_path = tmp_path / "demo_invoices.csv"

    generate_dataset(output_path)

    with output_path.open(
        "r",
        newline="",
        encoding="utf-8",
    ) as csv_file:
        reader = csv.DictReader(csv_file)
        rows = list(reader)

        assert reader.fieldnames == FIELDS

    assert rows

    for row in rows:
        assert row["demo_record_id"]
        assert row["invoice_number"]
        assert row["supplier_name"]
        assert row["scenario"]
        assert row["expected_outcome"]
        assert row["is_synthetic"] == "true"


def test_duplicate_scenario_contains_a_duplicate_invoice_number(tmp_path):
    output_path = tmp_path / "demo_invoices.csv"

    generate_dataset(output_path)

    with output_path.open(
        "r",
        newline="",
        encoding="utf-8",
    ) as csv_file:
        rows = list(csv.DictReader(csv_file))

    duplicate_row = next(
        row
        for row in rows
        if row["scenario"] == "duplicate_candidate"
    )

    matching_invoices = [
        row
        for row in rows
        if row["supplier_reference"]
        == duplicate_row["supplier_reference"]
        and row["invoice_number"] == duplicate_row["invoice_number"]
    ]

    assert len(matching_invoices) >= 2


def test_dataset_is_reproducible(tmp_path):
    first_path = tmp_path / "first.csv"
    second_path = tmp_path / "second.csv"

    generate_dataset(first_path)
    generate_dataset(second_path)

    assert first_path.read_bytes() == second_path.read_bytes()