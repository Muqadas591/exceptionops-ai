# Synthetic Data Policy

This directory is reserved for generated, fictional records used in development, testing, and demos.

## Allowed examples

- Fictional supplier names such as `Northwind Demo Supplies`
- Clearly synthetic invoice numbers such as `SYN-INV-0001`
- Fictional purchase orders and goods-receipt records
- Artificial amounts, dates, line items, and discrepancy scenarios
- Test cases intentionally containing duplicate invoices, missing fields, arithmetic errors, mismatched quantities, or changed supplier details

## Do not add

- Real customer, employee, supplier, or bank data
- Employer documents, screenshots, source code, or database exports
- Real bank account numbers, tax IDs, addresses, or credentials
- Unredacted production logs
- AI provider keys or access tokens

## Planned scenario categories

1. Clean invoice with matching purchase order
2. Duplicate invoice submission
3. Invoice total differs from line-item arithmetic
4. Invoice exceeds purchase-order tolerance
5. Missing purchase-order reference
6. Missing or partial goods receipt
7. Supplier identity mismatch
8. Changed supplier bank details requiring manual verification
9. Unsupported currency or malformed date
10. Corrupted or unreadable document

Synthetic data is not evidence of real-world model accuracy. Evaluation results must identify the test set and its limitations.
