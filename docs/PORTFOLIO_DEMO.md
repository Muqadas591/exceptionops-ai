
# ExceptionOps AI — Portfolio Demonstration

## Overview

ExceptionOps AI is a synthetic invoice and supplier exception
management platform.

It demonstrates an end-to-end workflow for:

- Document ingestion.
- Rule-based invoice extraction.
- Extraction confidence handling.
- Deterministic business validation.
- Duplicate invoice detection.
- Workflow orchestration.
- Human review and approval.
- Controlled simulated actions.
- Audit history and recovery controls.

All public demonstration records are fictional.

## Business Problem

Invoice processing involves repetitive document handling and
identification of incomplete or inconsistent information.

ExceptionOps AI demonstrates how an application can identify
potential exceptions, preserve processing history, and route
decisions to an authorized human reviewer.

The system is designed around an important distinction:

An extracted value is not automatically a verified business fact,
and a validation result is not an approval to pay an invoice.

## Demonstration Data

Generate the dataset:

    python -m scripts.generate_synthetic_demo_data

The generator creates:

- `data/synthetic/demo_invoices.csv`
- `data/synthetic/demo_manifest.json`
- Six fictional TXT invoice documents in `data/synthetic/invoices/`

The manifest records the expected results from the current
rule-based extraction provider and business rules.

## Demonstration Scenarios

### 1. Matched invoice example

All required fields are present.

The current extraction provider assigns supplier-name confidence
of 0.75. The business-rule threshold is 0.80, so the document is
routed for human review.

This example is not evidence of a completed purchase-order match.

### 2. Duplicate candidate

The document repeats a previously extracted supplier name and
invoice number.

The evaluation can identify:

    POSSIBLE_DUPLICATE_INVOICE

### 3. Zero amount

A zero invoice total triggers:

    TOTAL_AMOUNT_NOT_POSITIVE

The business decision is `blocked`.

### 4. Missing invoice date

The required invoice date is absent and requires review.

### 5. Missing supplier name

The required supplier name is absent and requires review.

### 6. Missing currency

The required currency is absent and requires review.

## Run the Complete Demonstration

Generate the data:

    python -m scripts.generate_synthetic_demo_data

Run the generator and business-rule tests:

    pytest tests/test_synthetic_demo_data.py -q

Start the API and database using the documented local setup.

Run the API-driven demonstration:

    python -m scripts.run_synthetic_demo --email demo.admin@example.test --base-url http://127.0.0.1:8001

The runner uploads the documents, runs extraction and evaluation,
creates workflows, creates or retrieves review records, and saves
a JSON report.

The runner does not automatically approve reviews or execute
external actions.

## Human-in-the-Loop Demonstration

Use the frontend to inspect review findings.

An authorized reviewer can:

- Inspect extracted values.
- Review business-rule findings.
- Add comments.
- Approve or reject a review with a decision note.

Only an approved review can proceed to the supported action
execution flow.

## Simulated Actions

The project includes simulated action connectors:

- Email draft.
- Accounting simulation.
- Webhook simulation.

These demonstrate controlled action execution and idempotency.
They are not live email delivery, accounting posting or payments.

## Auditability

The demonstration can show related records for:

- Document upload.
- Extraction.
- Business evaluation.
- Workflow events.
- Human-review decisions.
- Action execution.
- Audit events.

Use the real application interface and actual API responses.

## Engineering Practices

The project includes implementation work for:

- Authentication and role-based access.
- Input validation.
- Database migrations.
- Local document storage.
- Document retention.
- Backup and restore procedures.
- Security hardening.
- Idempotency and action recovery.
- Automated tests.
- Operational health checks.
- Structured logs and audit events.

Describe only features that have been implemented and verified
in the current repository.

## Screenshots

Capture genuine screenshots from the running application:

1. Dashboard.
2. Invoice list.
3. Invoice details.
4. Extraction results.
5. Business evaluation.
6. Exception queue.
7. Human-review details.
8. Workflow history.
9. Simulated action result.
10. Audit history.
11. Automated test results.

Save approved screenshots in:

    docs/screenshots/

Inspect all screenshots for secrets, tokens, private paths and
non-synthetic business data before publishing.

## Known Limitations

The current demonstration does not establish:

- Real-world invoice extraction accuracy.
- OCR performance on scanned documents.
- Purchase-order matching.
- Goods-receipt matching.
- Live accounting integration.
- Live email delivery.
- Production financial authorization.
- Production-scale throughput.
- Multi-tenant isolation.

The demonstration uses a deterministic rule-based provider and
a small synthetic dataset.

A successful synthetic demonstration is not proof of production
suitability for a financial institution.
