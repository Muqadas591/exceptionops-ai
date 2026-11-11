
from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = PROJECT_ROOT / "data" / "synthetic"

OUTPUT_FILE = OUTPUT_DIR / "demo_invoices.csv"
INVOICE_DIR = OUTPUT_DIR / "invoices"
MANIFEST_FILE = OUTPUT_DIR / "demo_manifest.json"

FIELDS = [
    "demo_record_id",
    "invoice_number",
    "supplier_reference",
    "supplier_name",
    "purchase_order_number",
    "purchase_order_supplier_name",
    "invoice_amount",
    "purchase_order_amount",
    "currency",
    "scenario",
    "expected_outcome",
    "is_synthetic",
]

SYNTHETIC_INVOICES: list[dict[str, Any]] = [
    {
        "demo_record_id": "DEMO-0001",
        "invoice_number": "SYN-INV-1001",
        "supplier_reference": "SUP-DEMO-001",
        "supplier_name": "Northstar Demo Supplies",
        "purchase_order_number": "SYN-PO-501",
        "purchase_order_supplier_name": "Northstar Demo Supplies",
        "invoice_amount": "1250.00",
        "purchase_order_amount": "1250.00",
        "currency": "PKR",
        "invoice_date": "2026-10-15",
        "scenario": "matched_invoice",
        "expected_outcome": "needs_review",
        "expected_findings": [
            "LOW_EXTRACTION_CONFIDENCE",
        ],
        "description": (
            "All required invoice fields are present. "
            "Supplier extraction confidence is below the "
            "configured review threshold."
        ),
    },
    {
        "demo_record_id": "DEMO-0002",
        "invoice_number": "SYN-INV-1001",
        "supplier_reference": "SUP-DEMO-001",
        "supplier_name": "Northstar Demo Supplies",
        "purchase_order_number": "SYN-PO-501",
        "purchase_order_supplier_name": "Northstar Demo Supplies",
        "invoice_amount": "1250.00",
        "purchase_order_amount": "1250.00",
        "currency": "PKR",
        "invoice_date": "2026-10-15",
        "scenario": "duplicate_candidate",
        "expected_outcome": "needs_review",
        "expected_findings": [
            "LOW_EXTRACTION_CONFIDENCE",
            "POSSIBLE_DUPLICATE_INVOICE",
        ],
        "description": (
            "Repeats the supplier and invoice number from "
            "DEMO-0001 using different document content."
        ),
    },
    {
        "demo_record_id": "DEMO-0003",
        "invoice_number": "SYN-INV-1002",
        "supplier_reference": "SUP-DEMO-002",
        "supplier_name": "Cedar Ridge Demo Components",
        "purchase_order_number": "SYN-PO-502",
        "purchase_order_supplier_name": "Cedar Ridge Demo Components",
        "invoice_amount": "0.00",
        "purchase_order_amount": "1600.00",
        "currency": "PKR",
        "invoice_date": "2026-10-16",
        "scenario": "zero_amount",
        "expected_outcome": "blocked",
        "expected_findings": [
            "LOW_EXTRACTION_CONFIDENCE",
            "TOTAL_AMOUNT_NOT_POSITIVE",
        ],
        "description": (
            "A zero invoice amount triggers a hard validation "
            "failure."
        ),
    },
    {
        "demo_record_id": "DEMO-0004",
        "invoice_number": "SYN-INV-1003",
        "supplier_reference": "SUP-DEMO-003",
        "supplier_name": "Bluewater Demo Logistics",
        "purchase_order_number": "SYN-PO-503",
        "purchase_order_supplier_name": "Bluewater Demo Logistics",
        "invoice_amount": "780.00",
        "purchase_order_amount": "780.00",
        "currency": "PKR",
        "invoice_date": None,
        "scenario": "missing_invoice_date",
        "expected_outcome": "needs_review",
        "expected_findings": [
            "REQUIRED_FIELD_MISSING",
            "LOW_EXTRACTION_CONFIDENCE",
        ],
        "description": (
            "The invoice date is intentionally omitted."
        ),
    },
    {
        "demo_record_id": "DEMO-0005",
        "invoice_number": "SYN-INV-1004",
        "supplier_reference": "SUP-DEMO-004",
        "supplier_name": "",
        "purchase_order_number": "SYN-PO-504",
        "purchase_order_supplier_name": "",
        "invoice_amount": "950.00",
        "purchase_order_amount": "950.00",
        "currency": "PKR",
        "invoice_date": "2026-10-17",
        "scenario": "missing_supplier_name",
        "expected_outcome": "needs_review",
        "expected_findings": [
            "REQUIRED_FIELD_MISSING",
        ],
        "description": (
            "The supplier name is intentionally omitted."
        ),
    },
    {
        "demo_record_id": "DEMO-0006",
        "invoice_number": "SYN-INV-1005",
        "supplier_reference": "SUP-DEMO-005",
        "supplier_name": "Meadowbrook Demo Packaging",
        "purchase_order_number": "SYN-PO-505",
        "purchase_order_supplier_name": "Meadowbrook Demo Packaging",
        "invoice_amount": "2340.00",
        "purchase_order_amount": "2340.00",
        "currency": "",
        "invoice_date": "2026-10-18",
        "scenario": "missing_currency",
        "expected_outcome": "needs_review",
        "expected_findings": [
            "REQUIRED_FIELD_MISSING",
            "LOW_EXTRACTION_CONFIDENCE",
        ],
        "description": (
            "The currency field and all other currency markers "
            "are intentionally omitted."
        ),
    },
]


def build_invoice_text(record: dict[str, Any]) -> str:
    """
    Build a parser-friendly synthetic invoice document.

    The text uses the field labels supported by the current
    RuleBasedInvoiceProvider.
    """
    lines = [
        "EXCEPTIONOPS AI - SYNTHETIC DEMONSTRATION",
        "",
        f"Demo Record ID: {record['demo_record_id']}",
        f"Demo Scenario: {record['scenario']}",
        "Synthetic Record: true",
        "",
        f"Invoice Number: {record['invoice_number']}",
    ]

    if record.get("supplier_name"):
        lines.append(
            f"Supplier: {record['supplier_name']}"
        )

    if record.get("invoice_date"):
        lines.append(
            f"Invoice Date: {record['invoice_date']}"
        )

    if record.get("currency"):
        lines.append(
            f"Currency: {record['currency']}"
        )

    lines.extend(
        [
            f"Total: {record['invoice_amount']}",
            "",
            "This document contains fictional demonstration data.",
            "It is not a real invoice and must not be used for payment.",
        ]
    )

    return "\n".join(lines) + "\n"


def generate_dataset(
    output_path: str | Path = OUTPUT_FILE,
) -> Path:
    """
    Generate the synthetic CSV, invoice documents and manifest.

    Existing unrelated files are not deleted.
    """
    target_path = Path(output_path)
    output_dir = target_path.parent

    invoice_dir = output_dir / "invoices"
    manifest_path = output_dir / "demo_manifest.json"

    output_dir.mkdir(parents=True, exist_ok=True)
    invoice_dir.mkdir(parents=True, exist_ok=True)

    csv_rows: list[dict[str, str]] = []
    manifest_records: list[dict[str, Any]] = []

    for record in SYNTHETIC_INVOICES:
        filename = (
            f"{record['demo_record_id']}-"
            f"{record['scenario']}.txt"
        )

        invoice_path = invoice_dir / filename
        invoice_content = build_invoice_text(record)

        invoice_path.write_text(
            invoice_content,
            encoding="utf-8",
        )

        csv_rows.append(
            {
                "demo_record_id": record["demo_record_id"],
                "invoice_number": record["invoice_number"],
                "supplier_reference": record["supplier_reference"],
                "supplier_name": record["supplier_name"],
                "purchase_order_number": record["purchase_order_number"],
                "purchase_order_supplier_name": (
                    record["purchase_order_supplier_name"]
                ),
                "invoice_amount": record["invoice_amount"],
                "purchase_order_amount": (
                    record["purchase_order_amount"]
                ),
                "currency": record["currency"],
                "scenario": record["scenario"],
                "expected_outcome": record["expected_outcome"],
                "is_synthetic": "true",
            }
        )

        manifest_records.append(
            {
                "demo_record_id": record["demo_record_id"],
                "scenario": record["scenario"],
                "filename": filename,
                "expected_decision": record["expected_outcome"],
                "expected_findings": record["expected_findings"],
                "description": record["description"],
                "is_synthetic": True,
            }
        )

    with target_path.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=FIELDS,
        )
        writer.writeheader()
        writer.writerows(csv_rows)

    manifest = {
        "dataset_name": "ExceptionOps AI Synthetic Demo",
        "dataset_version": "1.0",
        "is_synthetic": True,
        "record_count": len(manifest_records),
        "processing_provider": "rule_based_v1",
        "business_rules_version": "phase4_v1",
        "records": manifest_records,
    }

    manifest_path.write_text(
        json.dumps(
            manifest,
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    return target_path


def main() -> None:
    output_path = generate_dataset()

    print("Synthetic demonstration dataset generated.")
    print(f"CSV: {output_path}")
    print(f"Invoice documents: {INVOICE_DIR}")
    print(f"Manifest: {MANIFEST_FILE}")
    print(f"Records: {len(SYNTHETIC_INVOICES)}")
    print("All records are fictional.")


if __name__ == "__main__":
    main()
