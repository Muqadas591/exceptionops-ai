# Architecture — ExceptionOps AI

**Phase:** 0 — proposed architecture, not yet implemented.

## 1. Architectural principles

1. Use AI for unstructured interpretation, not for enforcing permissions.
2. Keep policy evaluation deterministic and independently testable.
3. Persist workflow state so work can be inspected and recovered.
4. Separate provider-specific AI code from business logic.
5. Verify action outcomes instead of assuming a request succeeded.
6. Start as a modular monolith; split services only when justified.
7. Use synthetic data in the public portfolio repository.

## 2. High-level flow

```text
PDF / supported input
        |
        v
Ingestion and file validation
        |
        v
Text extraction / OCR fallback
        |
        v
AI provider adapter
(extraction + classification)
        |
        v
Schema validation + source evidence
        |
        v
Deterministic validation and matching
        |
        v
Business rules and risk decisions
        |
        +------------------------+
        |                        |
        v                        v
Ready for approval         Exception / review
        |                        |
        +------------+-----------+
                     |
                     v
          Authorized action service
          (email draft / simulated
              accounting adapter)
                     |
                     v
          Outcome verification
                     |
                     v
       PostgreSQL state + audit events
                     |
                     v
          React + TypeScript UI
```

The UI communicates with the backend API; it does not directly connect to the database or call privileged connectors.

## 3. Planned logical modules

- `api`: versioned HTTP endpoints and request/response handling
- `core`: configuration, logging, errors, and shared types
- `domain`: invoice, supplier, purchase-order, exception, approval, and workflow rules
- `db`: SQLAlchemy models, sessions, and migrations
- `services`: orchestration of application use cases
- `ai`: provider interface, mock provider, hosted provider adapters, schema validation
- `documents`: file validation, parsing, OCR adapter, and evidence references
- `rules`: deterministic matching, duplicate detection, tolerances, and routing
- `workflows`: persisted workflow state, transitions, retry metadata, and cancellation
- `connectors`: email draft, simulated accounting, and future webhooks
- `audit`: append-oriented record of important business and system events
- `tests`: unit, API, integration, and failure-path tests
- `frontend`: React + TypeScript dashboard
- `ai-lab`: Colab notebooks and evaluation artifacts that contain no secrets

## 4. Initial data entities

### Supplier
A tenant-scoped supplier record with an internal ID, display name, normalized identity, status, and approved reference attributes. Sensitive payment details should be minimized and never exposed in logs.

### Invoice
A tenant-scoped document record and normalized invoice fields: supplier reference, invoice number, dates, currency, amounts, purchase-order reference, document hash, and processing status.

### InvoiceLine
An invoice line with description, quantity, unit price, tax information, and computed amount where available.

### PurchaseOrder
An approved or draft order containing supplier reference, currency, line items, quantities, and expected values.

### GoodsReceipt
Optional evidence of goods or services received. Absence of a receipt must not be treated as proof that goods were received.

### Exception
A detected issue with a category, severity, supporting evidence, state, owner, and resolution notes.

### Approval
A decision record containing actor, role, decision, timestamp, and comment. The application must verify the actor's authorization at decision time.

### WorkflowRun
A durable execution record with workflow version, current state, retry metadata, timestamps, and terminal outcome.

### ActionExecution
An action request and its status, idempotency key, external reference if any, and verified result.

### AuditEvent
A timestamped event describing a relevant actor/system action, affected entity, correlation ID, and safe metadata. Do not place credentials or unnecessary sensitive data in audit metadata.

## 5. State and decision principles

- Suggested invoice states: `received`, `processing`, `needs_review`, `ready_for_approval`, `approved`, `rejected`, `action_pending`, `resolved`, `failed`.
- State transitions must be explicitly allowed by server-side rules.
- A clean invoice is not automatically paid.
- Approval does not mean a downstream accounting action succeeded.
- A connector timeout may leave the external outcome unknown; reconcile before retrying a potentially non-idempotent side effect.
- Retries must be bounded and observable.
- Audit records should capture decisions and outcomes, not secrets.

Exact enums and schema constraints will be finalized when the backend domain model is implemented.

## 6. AI provider abstraction

The application will call a project-owned interface rather than vendor-specific SDK methods from business logic.

Conceptual contract:

```python
class InvoiceExtractionProvider:
    def extract_invoice(self, document_text: str) -> "InvoiceExtraction":
        ...
```

This is illustrative only; the actual asynchronous/synchronous contract and typed schemas will be selected in Phase 3. Implementations planned:

- `MockExtractionProvider`: deterministic fixtures for tests and offline development
- `HostedExtractionProvider`: provider-specific API adapter with timeout, error handling, and usage controls
- Colab notebooks: offline experiments and evaluation, not a dependency for production inference

Provider responses are untrusted. Validate them against a strict schema and run deterministic business checks after extraction.

## 7. Trust boundaries

- Uploaded files and extracted text are untrusted.
- Model output is untrusted.
- Frontend-supplied role claims are untrusted.
- External connector responses can be incomplete or ambiguous.
- Secrets and credentials are privileged configuration.
- The server is the enforcement point for authorization and business rules.

## 8. Deployment shape

Initial target: modular backend API + PostgreSQL + frontend. Use Docker for reproducible packaging when implementation begins. Background workers or a durable workflow engine may be introduced after the simple workflow requirements and failure modes are tested; do not add infrastructure without a need.
