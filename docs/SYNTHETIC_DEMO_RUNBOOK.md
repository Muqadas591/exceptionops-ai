
# ExceptionOps AI — Synthetic Demonstration Runbook

## 1. Objective

This runbook demonstrates the actual application using fictional
invoice documents.

The demonstration covers:

1. Synthetic document generation.
2. Authenticated document upload.
3. Rule-based invoice extraction.
4. Deterministic business evaluation.
5. Workflow creation and advancement.
6. Human-review record creation.
7. Human approval or rejection through the application.
8. Simulated action execution where explicitly approved.
9. Audit-history inspection.

The demonstration does not make real payments or send real emails.

## 2. Prerequisites

- Python virtual environment.
- Project dependencies installed.
- PostgreSQL available.
- Database migrations applied.
- ExceptionOps API running.
- An active admin or reviewer account.
- Frontend dependencies installed if using the web interface.

Check the application identity before starting.

The API must identify itself as:

    ExceptionOps AI

Do not run the demonstration against an unrelated service or a
different project listening on the same port.

## 3. Generate the synthetic dataset

From the repository root:

    python -m scripts.generate_synthetic_demo_data

Expected files:

    data/synthetic/demo_invoices.csv
    data/synthetic/demo_manifest.json
    data/synthetic/invoices/

There should be six invoice TXT documents.

All records are fictional.

## 4. Validate the generated dataset

Run:

    pytest tests/test_synthetic_demo_data.py -q

The tests verify:

- All six scenarios are generated.
- Every invoice is marked synthetic.
- The duplicate candidate repeats the intended invoice identity.
- The manifest includes expected decisions.
- The current extraction provider and business rules produce
  the documented expected outcomes.
- The generated data is reproducible.

## 5. Start the backend

Start PostgreSQL and the API using the project's configured setup.

For Docker:

    docker compose up -d db api

Inspect:

    docker compose ps

    docker compose logs --tail=100 api

Determine the actual host port mapped to container port 8000:

    docker compose port api 8000

Use that host port in the demonstration command.

For example, if Docker reports port 8001:

    http://127.0.0.1:8001

Check:

    http://127.0.0.1:8001/api/v1/health

The response must identify ExceptionOps AI.

## 6. Create a demonstration account if needed

The repository includes a user creation script.

From the project root:

    python -m scripts.create_user --email demo.admin@example.test --role admin

Enter a strong password when prompted.

The script stores a password hash, not the plaintext password.

Use an existing account instead if one is already available.

Do not commit demonstration passwords or environment secrets.

## 7. Run the API-driven demonstration

Use an admin or reviewer account:

    python -m scripts.run_synthetic_demo --email demo.admin@example.test --base-url http://127.0.0.1:8001

The password is requested interactively.

The runner:

- Checks the API application identity.
- Authenticates the user.
- Uploads the six documents.
- Reuses documents with matching checksums.
- Runs extraction and business evaluation.
- Creates or reuses workflows using idempotency keys.
- Advances non-terminal workflows.
- Creates or retrieves human-review records.
- Compares actual results with the synthetic manifest.
- Writes a JSON report.

Default report:

    data/synthetic/run-results/latest-run.json

The report does not contain the access token or password.

A successful run reports:

    Status: passed
    Records: 6

The exact document, workflow and review IDs depend on the database.

## 8. Expected scenario behavior

### Scenario 1 — Matched invoice

All required invoice fields are present.

The supplier extraction confidence is below the configured 0.80
threshold, so the evaluation requires review.

This is not an approval or a confirmed purchase-order match.

### Scenario 2 — Duplicate candidate

The invoice number and supplier match the first document.

The business evaluation should include:

    POSSIBLE_DUPLICATE_INVOICE

The workflow should require review.

### Scenario 3 — Zero amount

The invoice total is zero.

The evaluation should include:

    TOTAL_AMOUNT_NOT_POSITIVE

The decision should be:

    blocked

### Scenario 4 — Missing invoice date

The required invoice date is absent.

The evaluation should include:

    REQUIRED_FIELD_MISSING

### Scenario 5 — Missing supplier name

The required supplier name is absent.

The evaluation should include:

    REQUIRED_FIELD_MISSING

### Scenario 6 — Missing currency

The required currency field is absent.

The evaluation should include:

    REQUIRED_FIELD_MISSING

## 9. Demonstrate the frontend

Set the frontend API URL to the actual backend host port.

In PowerShell:

    cd frontend

    $env:VITE_API_BASE_URL = "http://127.0.0.1:8001"

Install dependencies if necessary:

    npm ci

Start the frontend:

    npm run dev

Open the Vite URL shown in the terminal, normally:

    http://localhost:5173

Sign in using the admin or reviewer account.

Recommended walkthrough:

1. Dashboard — show the current application overview.
2. Invoices — show the six uploaded synthetic documents.
3. Invoice details — inspect a selected document.
4. Processing — inspect extraction and business evaluation.
5. Exceptions — show records requiring review.
6. Review details — inspect findings and add a review comment.
7. Workflows — show workflow states and event history.
8. Audit history — inspect traceability with an account permitted
   to access that page.

## 10. Demonstrate human approval

The API-driven runner intentionally leaves reviews pending.

Use the review interface to inspect the findings.

A reviewer should make a decision with a meaningful note.

Do not approve a record merely to make the dashboard look complete.

The review decision is a human-controlled business action.

## 11. Demonstrate simulated actions

Only after an authorized reviewer has approved a review:

1. Open the Action Center.
2. Select an approved review.
3. Choose a supported simulation action.
4. Provide the required idempotency key.
5. Execute the simulation.
6. Inspect the action result.
7. Inspect the related audit events.

Supported action types include:

- Email draft.
- Accounting simulation.
- Webhook simulation.

These are not equivalent to live email delivery, accounting posting,
or financial transactions.

Never describe a simulation as a real payment or external posting.

## 12. Demonstrate auditability

Inspect the audit history for:

- Document upload.
- Extraction completion.
- Business evaluation.
- Workflow creation.
- Workflow advancement.
- Review creation.
- Review assignment or comments.
- Review decision.
- Action creation and execution, if demonstrated.

Use the related document, workflow, review and action identifiers
to explain how events are connected.

## 13. Demonstrate reliability

Use the operational reliability procedures from:

    docs/OPERATIONAL_RELIABILITY.md

Use the backup and restore procedures from:

    docs/BACKUP_AND_RESTORE.md

Do not run destructive restore procedures against the only copy of
your demonstration database.

## 14. Screenshot checklist

Capture genuine screenshots from the running application:

- [ ] Dashboard with synthetic records.
- [ ] Invoice list.
- [ ] Invoice detail.
- [ ] Extraction fields and confidence.
- [ ] Business evaluation findings.
- [ ] Exception queue.
- [ ] Review details and human decision.
- [ ] Workflow history.
- [ ] Simulated action result, if demonstrated.
- [ ] Audit history.
- [ ] Successful synthetic demonstration report.
- [ ] Passing automated tests.

Save approved screenshots under:

    docs/screenshots/

Before publishing, inspect every screenshot for:

- Passwords.
- Access tokens.
- Email addresses that should remain private.
- Local usernames and personal paths.
- Real business data.
- Database connection strings.

Do not fabricate screenshots or manually alter results.

## 15. Repeatability and reruns

The runner uses document checksums and workflow idempotency keys.

A rerun can reuse documents and workflows already created by an
earlier run.

The runner does not reset review decisions or delete prior data.

For a completely fresh demonstration, use a separate disposable
synthetic database and storage directory.

Do not clear your normal development database just to repeat a demo.

## 16. Known limitations

This demonstration does not establish:

- Accuracy on real-world invoice datasets.
- OCR quality on scanned documents.
- Purchase-order or goods-receipt matching.
- Production financial controls.
- Live accounting-system integration.
- Live email delivery.
- Production-scale throughput.
- Multi-tenant data isolation.

The demonstration uses a deterministic rule-based extraction
provider and a small, intentionally constructed synthetic dataset.

Describe these limitations honestly in the portfolio.
