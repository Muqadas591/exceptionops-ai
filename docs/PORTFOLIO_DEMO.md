# ExceptionOps AI — Portfolio Demo Guide

## 1. Overview

ExceptionOps AI explores AI-assisted invoice processing and business exception management.

The demonstration uses fictional invoice data to illustrate normal processing cases and potential business exceptions.

The focus is on the complete engineering workflow: ingestion, validation, exception handling, review, controlled actions, and traceability, where supported by the current implementation.

## 2. Business Problem

Invoice processing can involve repetitive data entry, comparisons against purchase orders, and the identification of inconsistent information.

Potential issues include:

- Invoice and purchase-order amount differences
- Duplicate invoice submissions
- Invalid amounts
- Missing purchase-order information
- Supplier identity mismatches

These conditions require careful handling. An automated system should identify relevant issues without treating every document as automatically approved.

## 3. Demonstration Dataset

Generate the synthetic data from the repository root:

```powershell
python scripts/generate_synthetic_demo_data.py
```

The generated file is:

`data/synthetic/demo_invoices.csv`

All records are fictional.

## 4. Demo Scenarios

### Scenario A — Matched Invoice

The invoice amount and purchase-order amount are both PKR 1,250.00.

Purpose: illustrate a normal comparison case.

Expected scenario: eligible for the standard review process.

### Scenario B — Amount Mismatch

The invoice amount is PKR 1,840.00, while the purchase-order amount is PKR 1,600.00.

Difference: PKR 240.00.

Purpose: illustrate the identification of a business discrepancy.

Expected scenario: requires amount-exception review.

### Scenario C — Duplicate Candidate

The record repeats the supplier reference and invoice number from the first synthetic invoice.

Purpose: illustrate a potential duplicate.

Expected scenario: requires duplicate review.

The dataset intentionally includes the repeated invoice identifier so that duplicate-handling behavior can be examined.

### Scenario D — Invalid Amount

The invoice amount is PKR 0.00.

Purpose: illustrate validation of an invalid business value.

Expected scenario: requires data validation.

### Scenario E — Missing Purchase Order

The invoice has an amount of PKR 780.00 but no purchase-order reference.

Purpose: illustrate missing business information.

Expected scenario: requires review of the missing purchase-order information.

### Scenario F — Supplier Mismatch

The invoice supplier and purchase-order supplier have similar but different names.

Purpose: illustrate supplier identity inconsistency.

Expected scenario: requires supplier identity review.

## 5. How to Demonstrate the Application

1. Start the backend and database using the documented local setup.
2. Start the frontend if the current implementation includes it.
3. Verify that the application health endpoint or startup checks succeed.
4. Upload a synthetic invoice through the application's supported upload workflow.
5. Inspect the extracted information if extraction is supported for that document.
6. Run the implemented validation or business-evaluation workflow.
7. Inspect any exception information returned by the application.
8. Demonstrate the supported human-review workflow.
9. Inspect the action result and audit information if those features are available.
10. Restart the backend and verify local document persistence.

Use the application's actual supported endpoints and interface. Do not insert rows directly into the database to create the appearance of a successful end-to-end workflow.

## 6. Reliability and Engineering

The project is intended to demonstrate engineering practices beyond a simple proof of concept, including:

- Structured application configuration
- Database schema migrations
- Input validation
- Document-storage safeguards
- Automated tests
- Failure-path handling
- Logging and request traceability where implemented
- Idempotency and recovery controls where implemented
- Explicit distinction between simulated and real external actions

Describe only the controls that exist and have been verified in the current codebase.

## 7. Safety Boundaries

This is a portfolio demonstration.

- All public demo data is synthetic.
- No confidential employer or customer documents should be used.
- No real payments are made by the synthetic demo.
- Simulated actions are not equivalent to live accounting or email integrations.
- Human approval requirements depend on the actual application configuration.
- Automated results should not be represented as guaranteed financial decisions.

## 8. Screenshots to Capture

Capture screenshots using the running application and synthetic data:

1. Main dashboard or application landing page
2. Invoice upload screen
3. Document details or extraction results
4. Validation or exception results
5. Review queue or review details
6. Action execution result, if implemented
7. Audit history, if implemented
8. Successful automated test run in the terminal

Use the real application UI. Do not create fake screenshots or manually alter results to imply that a feature works.

Save approved screenshots under `docs/screenshots/` or another documented portfolio-assets directory.

Before publishing, inspect every screenshot for passwords, tokens, local usernames, private paths, and real business data.

## 9. Known Limitations

Document limitations observed in the current implementation, including supported file types, extraction limitations, external integrations, and deployment constraints.

A successful synthetic demonstration does not establish production suitability for a real financial institution.

## 10. Reproducibility

Generate the synthetic dataset:

```powershell
python scripts/generate_synthetic_demo_data.py
```

Run the generator tests:

```powershell
pytest tests/test_synthetic_demo_data.py -q
```

Run the backend tests:

```powershell
pytest -q
```

Record the actual test result when publishing the project. Do not claim that all tests pass unless the full test suite has completed successfully.