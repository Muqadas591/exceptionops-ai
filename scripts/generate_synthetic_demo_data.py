from __future__ import annotations

import csv
from pathlib import Path


OUTPUT_DIR = Path("data/synthetic")
OUTPUT_FILE = OUTPUT_DIR / "demo_invoices.csv"

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

SYNTHETIC_INVOICES = [
    {
        "demo_record_id": "DEMO-0001",
        "invoice_number": "SYN-INV-1001",
        "supplier_reference": "SUP-DEMO-001",
        "supplier_name": "Northstar Office Supplies",
        "purchase_order_number": "SYN-PO-501",
        "purchase_order_supplier_name": "Northstar Office Supplies",
        "invoice_amount": "1250.00",
        "purchase_order_amount": "1250.00",
        "currency": "USD",
        "scenario": "matched_invoice",
        "expected_outcome": "eligible_for_standard_review",
        "is_synthetic": "true",
    },
    {
        "demo_record_id": "DEMO-0002",
        "invoice_number": "SYN-INV-1001",
        "supplier_reference": "SUP-DEMO-001",
        "supplier_name": "Northstar Office Supplies",
        "purchase_order_number": "SYN-PO-501",
        "purchase_order_supplier_name": "Northstar Office Supplies",
        "invoice_amount": "1250.00",
        "purchase_order_amount": "1250.00",
        "currency": "USD",
        "scenario": "duplicate_candidate",
        "expected_outcome": "duplicate_check_required",
        "is_synthetic": "true",
    },
    {
        "demo_record_id": "DEMO-0003",
        "invoice_number": "SYN-INV-1002",
        "supplier_reference": "SUP-DEMO-002",
        "supplier_name": "Cedar Ridge Components",
        "purchase_order_number": "SYN-PO-502",
        "purchase_order_supplier_name": "Cedar Ridge Components",
        "invoice_amount": "1840.00",
        "purchase_order_amount": "1600.00",
        "currency": "USD",
        "scenario": "amount_mismatch",
        "expected_outcome": "human_review_required",
        "is_synthetic": "true",
    },
    {
        "demo_record_id": "DEMO-0004",
        "invoice_number": "SYN-INV-1003",
        "supplier_reference": "SUP-DEMO-003",
        "supplier_name": "Bluewater Logistics",
        "purchase_order_number": "SYN-PO-503",
        "purchase_order_supplier_name": "Bluewater Logistics",
        "invoice_amount": "invalid",
        "purchase_order_amount": "780.00",
        "currency": "USD",
        "scenario": "invalid_amount",
        "expected_outcome": "validation_failure",
        "is_synthetic": "true",
    },
    {
        "demo_record_id": "DEMO-0005",
        "invoice_number": "SYN-INV-1004",
        "supplier_reference": "SUP-DEMO-004",
        "supplier_name": "Summit Industrial Goods",
        "purchase_order_number": "",
        "purchase_order_supplier_name": "Summit Industrial Goods",
        "invoice_amount": "950.00",
        "purchase_order_amount": "",
        "currency": "USD",
        "scenario": "missing_purchase_order",
        "expected_outcome": "human_review_required",
        "is_synthetic": "true",
    },
    {
        "demo_record_id": "DEMO-0006",
        "invoice_number": "SYN-INV-1005",
        "supplier_reference": "SUP-DEMO-005",
        "supplier_name": "Meadowbrook Packaging",
        "purchase_order_number": "SYN-PO-505",
        "purchase_order_supplier_name": "Meadowbrook Packaging Ltd.",
        "invoice_amount": "2340.00",
        "purchase_order_amount": "2340.00",
        "currency": "USD",
        "scenario": "supplier_mismatch",
        "expected_outcome": "human_review_required",
        "is_synthetic": "true",
    },
]


def generate_dataset(output_path: str | Path = OUTPUT_FILE) -> Path:
    target_path = Path(output_path)
    target_path.parent.mkdir(parents=True, exist_ok=True)

    with target_path.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(SYNTHETIC_INVOICES)

    return target_path


def main() -> None:
    output_path = generate_dataset()
    print(f"Created synthetic dataset: {output_path}")
    print(f"Rows: {len(SYNTHETIC_INVOICES)}")
    print("All records are fictional demo data.")


if __name__ == "__main__":
    main()
