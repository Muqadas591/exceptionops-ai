# Product Specification — ExceptionOps AI

**Status:** Phase 0 draft for implementation  
**Initial workflow:** Invoice and supplier exception resolution  
**Product principle:** AI assists interpretation; deterministic code enforces policy and permissions.

## 1. Problem statement

Businesses receive supplier invoices in different formats and must reconcile them against purchase orders, supplier records, and (where available) goods-receipt records. Missing data, duplicate submissions, amount differences, changed supplier details, and slow approvals create manual investigation and follow-up work.

Basic field extraction does not resolve the full workflow. Users need an explainable exception, evidence, an owner, an approved next action, and a record of the outcome.

## 2. Intended users

- Accounts-payable clerks who process invoices
- Finance managers who configure controls and approve exceptions
- Procurement staff who investigate purchase-order or delivery discrepancies
- Small-business owners who need visibility into outstanding work

These user assumptions must be validated through customer discovery. The project must not claim product-market fit before that research.

## 3. Product objective

Build a demonstrable workflow that takes a synthetic invoice from intake through extraction, validation, matching, decision, human review when required, authorized action, and audit logging.

## 4. MVP functional requirements

### FR-01 — Intake
Accept supported invoice documents and associate each upload with a processing record. Reject unsupported or unsafe files with a clear error.

### FR-02 — Extraction
Extract supplier name and identifier (when present), invoice number, invoice date, due date, currency, subtotal, tax, total, purchase-order reference, line items, and relevant payment-detail indicators. Store evidence for fields when technically available.

### FR-03 — Validation
Validate required fields, types, date formats, currency, arithmetic consistency, and source evidence. Missing or inconsistent fields must be surfaced, not silently guessed.

### FR-04 — Duplicate detection
Detect likely duplicates using normalized supplier identity, invoice number, and additional signals such as date and amount. Distinguish exact matches from possible duplicates.

### FR-05 — Matching
Compare invoice fields and line items with available purchase-order records and, if supplied, goods-receipt records. Missing reference data must produce an explicit unresolved state.

### FR-06 — Rules and decisions
Evaluate configurable tolerances, required fields, supplier status, duplicate signals, and approval thresholds using deterministic business logic. The model must not set or override policy.

### FR-07 — Exception management
Create an exception with a reason, evidence, recommended next step, status, and assigned reviewer where required.

### FR-08 — Human approval
Record who approved, rejected, or requested correction, when the decision occurred, and any comment. Enforce role permissions in the application.

### FR-09 — Actions
Support an email draft and a simulated accounting update in the MVP. An action is not considered successful until the connector reports a success result. Real payment initiation is excluded.

### FR-10 — Audit history
Record important state transitions, rule outcomes, approval decisions, and action results with timestamps and actor/system identity.

### FR-11 — Dashboard
Provide invoice status, exception queue, invoice details, evidence, review actions, and audit history through a React + TypeScript interface.

### FR-12 — Provider abstraction
Keep extraction/classification behind an interface so a hosted model provider can be configured later. Include a deterministic mock implementation for repeatable tests. Colab experiments are for evaluation, not a production runtime dependency.

## 5. Non-functional requirements

- **Security:** secrets remain outside source control; uploads are validated; authorization is enforced server-side.
- **Traceability:** decisions should point to source evidence and applicable rules.
- **Reliability:** transient failures have bounded retries; non-idempotent actions require careful deduplication and outcome tracking.
- **Maintainability:** separate API, domain logic, persistence, provider adapters, and connectors.
- **Testability:** deterministic rules and workflows can be tested without a live AI provider.
- **Privacy:** public examples use synthetic data only.
- **Accessibility:** dashboard controls should have labels, keyboard support, and visible error states.
- **Portability:** document setup and deployment steps; avoid unnecessary vendor lock-in.

## 6. Safety and human oversight

- AI output is untrusted input and must be schema-validated.
- AI cannot authorize its own proposed action.
- Bank-detail changes are high-risk and require explicit review.
- Invoice approval and payment execution are different operations.
- The MVP simulates accounting updates and never moves money.
- External actions require permission checks, audit records, and outcome verification.

## 7. Out of scope

- Real payment execution
- Production ERP integrations
- Automatic changes to supplier bank details
- Unrestricted autonomous agents
- A universal no-code workflow builder
- Claims of guaranteed fraud detection
- Use of confidential employer or customer data

## 8. Success measures

The evaluation dataset and thresholds will be defined before performance claims are made. Measures include:

- Field-level extraction precision/accuracy on labeled synthetic cases
- Duplicate-detection precision and recall
- Discrepancy-detection precision and recall
- Correct routing of approval-required cases
- Workflow completion and failure rates
- Duplicate-action prevention under retry tests
- Median exception-resolution time in a controlled demo
- Human-review rate, interpreted alongside correctness and risk

## 9. Assumptions to validate

1. Target businesses spend meaningful time investigating invoice exceptions.
2. They can provide or export purchase-order and supplier records.
3. A document-upload and CSV/API workflow is useful before a deep ERP integration.
4. They value explainable decisions and audit history.
5. They would pay enough to cover hosting, AI usage, onboarding, and support.

Validate these assumptions with interviews and a small pilot before making commercial claims.
