
import csv
import json

from app.services.business_rules import evaluate_invoice_fields
from app.services.extraction_providers import (
    RuleBasedInvoiceProvider,
)

from scripts.generate_synthetic_demo_data import (
    FIELDS,
    SYNTHETIC_INVOICES,
    generate_dataset,
)


EXPECTED_SCENARIOS = {
    "matched_invoice",
    "duplicate_candidate",
    "zero_amount",
    "missing_invoice_date",
    "missing_supplier_name",
    "missing_currency",
}


def read_csv(path):
    with path.open(
        "r",
        newline="",
        encoding="utf-8",
    ) as csv_file:
        return list(csv.DictReader(csv_file))


def test_generated_dataset_contains_all_expected_scenarios(
    tmp_path,
):
    output_path = tmp_path / "demo_invoices.csv"

    generate_dataset(output_path)

    rows = read_csv(output_path)

    assert len(rows) == len(SYNTHETIC_INVOICES)

    scenarios = {
        row["scenario"]
        for row in rows
    }

    assert scenarios == EXPECTED_SCENARIOS


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
        assert row["scenario"]
        assert row["expected_outcome"]
        assert row["is_synthetic"] == "true"


def test_generated_invoice_documents_are_marked_synthetic(
    tmp_path,
):
    output_path = tmp_path / "demo_invoices.csv"

    generate_dataset(output_path)

    invoice_dir = tmp_path / "invoices"
    invoice_files = list(invoice_dir.glob("*.txt"))

    assert len(invoice_files) == len(SYNTHETIC_INVOICES)

    for invoice_file in invoice_files:
        content = invoice_file.read_text(
            encoding="utf-8"
        )

        assert "SYNTHETIC DEMONSTRATION" in content
        assert "Synthetic Record: true" in content
        assert "fictional demonstration data" in content


def test_duplicate_scenario_reuses_invoice_number_and_supplier(
    tmp_path,
):
    output_path = tmp_path / "demo_invoices.csv"

    generate_dataset(output_path)

    rows = read_csv(output_path)

    duplicate_row = next(
        row
        for row in rows
        if row["scenario"] == "duplicate_candidate"
    )

    matching_invoices = [
        row
        for row in rows
        if row["supplier_name"] == duplicate_row["supplier_name"]
        and row["invoice_number"] == duplicate_row["invoice_number"]
    ]

    assert len(matching_invoices) >= 2


def test_manifest_contains_expected_decisions(tmp_path):
    output_path = tmp_path / "demo_invoices.csv"

    generate_dataset(output_path)

    manifest_path = tmp_path / "demo_manifest.json"

    manifest = json.loads(
        manifest_path.read_text(encoding="utf-8")
    )

    assert manifest["is_synthetic"] is True
    assert manifest["record_count"] == 6

    records = {
        item["scenario"]: item
        for item in manifest["records"]
    }

    assert records["matched_invoice"]["expected_decision"] == (
        "needs_review"
    )

    assert records["zero_amount"]["expected_decision"] == (
        "blocked"
    )


def test_generated_documents_match_actual_business_rules(
    tmp_path,
):
    output_path = tmp_path / "demo_invoices.csv"

    generate_dataset(output_path)

    manifest = json.loads(
        (tmp_path / "demo_manifest.json").read_text(
            encoding="utf-8"
        )
    )

    provider = RuleBasedInvoiceProvider()

    for record in manifest["records"]:
        invoice_path = (
            tmp_path
            / "invoices"
            / record["filename"]
        )

        text = invoice_path.read_text(
            encoding="utf-8"
        )

        candidates = provider.extract(text)

        fields = {
            name: {
                "value": candidate.value,
                "confidence": candidate.confidence,
                "evidence": candidate.evidence,
            }
            for name, candidate in candidates.items()
        }

        result = evaluate_invoice_fields(
            fields,
            duplicate_detected=(
                record["scenario"] == "duplicate_candidate"
            ),
        )

        actual_findings = {
            finding["rule_code"]
            for finding in result["findings"]
        }

        assert result["decision"] == record["expected_decision"]

        assert set(record["expected_findings"]).issubset(
            actual_findings
        )


def test_generated_dataset_is_reproducible(tmp_path):
    first_dir = tmp_path / "first"
    second_dir = tmp_path / "second"

    first_path = first_dir / "demo_invoices.csv"
    second_path = second_dir / "demo_invoices.csv"

    generate_dataset(first_path)
    generate_dataset(second_path)

    assert first_path.read_bytes() == second_path.read_bytes()

    first_manifest = (
        first_dir / "demo_manifest.json"
    ).read_bytes()

    second_manifest = (
        second_dir / "demo_manifest.json"
    ).read_bytes()

    assert first_manifest == second_manifest

    for record in SYNTHETIC_INVOICES:
        filename = (
            f"{record['demo_record_id']}-"
            f"{record['scenario']}.txt"
        )

        first_invoice = (
            first_dir / "invoices" / filename
        ).read_bytes()

        second_invoice = (
            second_dir / "invoices" / filename
        ).read_bytes()

        assert first_invoice == second_invoice
