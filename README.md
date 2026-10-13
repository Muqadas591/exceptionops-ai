# ExceptionOps AI

**From business requests to verified resolution.**

ExceptionOps AI is a portfolio project for AI-assisted invoice and supplier exception resolution. It is designed to help accounts-payable teams process invoices, identify discrepancies, route exceptions for human review, and track authorized actions with an audit trail.

> **Project status:** Phase 0 — product specification and repository foundation. The application code has not been implemented yet.

## Problem

Invoice processing often spans email, PDFs, purchase orders, spreadsheets, and approval chains. Extracting fields is only one part of the problem: teams also need to identify duplicates, reconcile records, investigate exceptions, obtain approvals, and verify that actions actually succeeded.

## MVP

- PDF invoice intake and document processing
- AI-assisted extraction through a configurable provider interface
- Field validation and source evidence
- Duplicate invoice detection
- Invoice-to-purchase-order matching
- Configurable discrepancy and approval rules
- Human review and approval workflow
- Email drafts and simulated accounting actions
- Persistent workflow state and audit history
- React + TypeScript operations dashboard

The initial demonstration uses synthetic data. It will not initiate real payments.

## Planned technology

- **Backend:** Python, FastAPI, Pydantic
- **Persistence:** PostgreSQL, SQLAlchemy, Alembic
- **Frontend:** React, TypeScript
- **AI experiments:** Google Colab notebooks; optional GPU usage when available
- **Inference:** configurable hosted-model adapter plus a deterministic mock provider for tests
- **Quality:** pytest, HTTPX, GitHub Actions
- **Deployment:** Docker and managed hosting, selected during the deployment phase

No local GPU model is required for normal development. A hosted API subscription and API access are separate; verify provider API access and pricing before use.

## Architecture and requirements

- [Product specification](docs/PRODUCT_SPEC.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Acceptance criteria](docs/ACCEPTANCE_CRITERIA.md)
- [Initial threat model](docs/THREAT_MODEL.md)
- [Synthetic data policy](data/synthetic/README.md)

## Roadmap

| Phase | Focus |
|---|---|
| 0 | Product definition and repository foundation |
| 1 | Backend foundation and database |
| 2 | Document ingestion and processing |
| 3 | AI extraction and classification |
| 4 | Business rules and risk engine |
| 5 | Workflow orchestration |
| 6 | Human approval and action connectors |
| 7 | React dashboard |
| 8 | Testing, security, and observability |
| 9 | Deployment and CI/CD |
| 10 | Portfolio release and product expansion |

## Phase 0 status

This repository currently contains specifications and project hygiene files only. There is no running API or UI yet.

## Local setup

Phase 0 requires only Git and a text editor. No Python packages, Node packages, GPU, database, or API key are needed yet.

1. Clone the repository.
2. Read the product specification and acceptance criteria.
3. Review `.gitignore` and `.env.example`.
4. Do not add secrets or confidential employer data.

Later phases will add exact installation and execution commands for the backend and frontend.

## Security principles

- Never commit `.env` files, credentials, API keys, or tokens.
- Use synthetic examples only in the public repository.
- Never upload confidential employer code or banking/customer records.
- Treat invoice text and attachments as untrusted input.
- AI suggestions do not grant permission to perform actions.
- Real payment execution is out of scope for the MVP.

## License

This project is licensed under the MIT License; see [LICENSE](LICENSE).
## Phase 1 — Backend Foundation and Database

**Status:** Implemented locally; validate tests and migration before release.

### Technology Stack

- Python 3.11+
- FastAPI and Uvicorn
- Pydantic Settings
- SQLAlchemy 2.x
- PostgreSQL
- Alembic database migrations
- Pytest and HTTPX

### Current Capabilities

- FastAPI application factory and interactive OpenAPI documentation
- Environment-based application configuration
- PostgreSQL connection and session management
- Version-controlled database migrations
- Initial supplier, invoice, purchase order, exception, and audit-event models
- Basic duplicate invoice protection using a supplier and invoice-number uniqueness constraint
- Health and database readiness endpoints
- Automated tests using an isolated SQLite test database

### Run Locally

1. Create and activate a Python virtual environment.
2. Install development dependencies with `python -m pip install -e ".[dev]"`.
3. Create `.env` from `.env.example`.
4. Start PostgreSQL with `docker compose up -d db`.
5. Apply migrations with `alembic upgrade head`.
6. Start the API with `uvicorn app.main:app --reload`.
7. Open `http://127.0.0.1:8000/docs`.
8. Run tests with `pytest`.

### Current Limitations

Invoice ingestion, AI extraction, business-rule evaluation, authentication, approval workflows, and accounting integrations are not implemented in this phase. The database is a local development database; production deployment and security hardening remain future work.

No real payments or accounting actions are executed.

## Phase 2 — Secure Document Ingestion

**Status:** Implemented locally; validate migrations and automated tests before release.

### Capabilities

- Upload PDF, TXT, and CSV documents through a FastAPI endpoint.
- Validate allowed extensions, file size, basic file signatures, and UTF-8 text.
- Generate unique storage keys instead of trusting supplied filenames.
- Calculate SHA-256 checksums and prevent duplicate content records.
- Persist document metadata in PostgreSQL using SQLAlchemy.
- Store document contents separately from database metadata.
- List documents, retrieve metadata, and download stored content through API routes.
- Run automated tests for successful uploads, invalid files, duplicate content, size limits, and retrieval.

### API Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/api/v1/documents` | Upload a document |
| GET | `/api/v1/documents` | List document metadata |
| GET | `/api/v1/documents/{document_id}` | Retrieve metadata |
| GET | `/api/v1/documents/{document_id}/content` | Download document content |
| GET | `/api/v1/health` | Check application health |
| GET | `/api/v1/ready` | Check database readiness |

### Run and Test

1. Activate the virtual environment.
2. Install dependencies with `python -m pip install -e ".[dev]"`.
3. Start PostgreSQL with `docker compose up -d db`.
4. Apply database migrations with `alembic upgrade head`.
5. Run the API with `uvicorn app.main:app --reload`.
6. Run automated tests with `pytest -v`.

### Current Limitations

Document ingestion does not yet extract invoice fields or classify exceptions. Basic format checks do not replace malware scanning or secure document parsing. Authentication, authorization, tenant isolation, production storage, and production security hardening remain future work.

Use synthetic documents only. Do not expose this development API publicly or upload confidential business documents.
## Phase 3 — Free Invoice Extraction Pipeline

**Status:** Initial extraction pipeline implemented; validate database migrations and automated tests before release.

### Capabilities

- Extract text from text-based PDF, TXT and CSV documents.
- Detect invoice number, invoice date, due date, supplier name, currency and total amount using deterministic rules.
- Return structured fields with supporting text evidence and heuristic confidence indicators.
- Store extraction results in PostgreSQL.
- Retrieve saved results by document ID.
- Re-run extraction and update the existing result.
- Keep the extraction provider independent from the API and database layers.

### Free Inference Strategy

The current `rule_based_v1` provider does not call a hosted AI service, download an AI model, or require an API key. It is a baseline for development and evaluation, not a general-purpose AI model.

Future providers can be evaluated behind the same extraction interface. Open-source model experiments can be run in Google Colab, subject to available free compute resources.

### API Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/api/v1/documents/{document_id}/extract` | Run extraction |
| GET | `/api/v1/documents/{document_id}/extraction` | Retrieve the saved result |

Document upload, listing, metadata retrieval and content download remain available from Phase 2.

### Run and Test

1. Activate the project virtual environment.
2. Install dependencies with `python -m pip install -e ".[dev]"`.
3. Apply database migrations with `alembic upgrade head`.
4. Start the API with `uvicorn app.main:app --reload`.
5. Run automated tests with `pytest -v`.
6. Open `http://127.0.0.1:8000/docs` to explore the API.

### Limitations

- Scanned PDFs require OCR.
- Rules may fail on unfamiliar invoice layouts.
- Confidence indicators are heuristic, not calibrated probabilities.
- Extraction does not validate supplier identity, purchase orders, tax calculations, duplicates across differently formatted invoices, or payment eligibility.
- Human review and business-rule validation are required before business actions.
- Production authentication, authorization, tenant isolation, secure deployment and document-processing hardening remain future work.

Use synthetic documents during development. Do not upload confidential customer or employer documents to a public service or repository.
## Phase 4 — Business Rules & Risk Engine

Phase 4 introduces a deterministic business-rules engine for evaluating extracted invoice data before downstream processing.

### Capabilities

- Validates required invoice fields.
- Validates invoice dates, due dates, currency format, and total amount.
- Flags low-confidence extracted fields.
- Detects potential duplicate invoices using normalized supplier names and invoice numbers.
- Calculates an explainable risk score from 0 to 100.
- Stores the latest evaluation for each document.
- Returns structured findings with rule codes, severity, messages, and field names.
- Exposes API endpoints for running and retrieving evaluations.

### Evaluation decisions

- `ready_for_matching`: basic validation passed; further matching checks are still required.
- `needs_review`: one or more business-rule findings require review.
- `blocked`: a hard validation failure prevents normal processing.

These decisions are internal workflow states, not authorization to pay an invoice.

### API endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/documents/{document_id}/evaluate` | Evaluate the latest extraction |
| GET | `/api/v1/documents/{document_id}/evaluation` | Retrieve the latest evaluation |

### Technology

- Python
- FastAPI
- SQLAlchemy
- PostgreSQL
- Alembic
- Pydantic
- pytest

### AI and cost strategy

The Phase 4 rules engine uses deterministic Python logic and does not require a paid AI API key. Phase 3's extraction confidence is treated as a review signal, not a calibrated probability.

### Current limitations

- Duplicate detection uses exact normalized supplier-name and invoice-number matching.
- Purchase-order and goods-receipt matching are not implemented yet.
- A passing evaluation does not mean an invoice is approved for payment.
- Accounting-system integration and real payment execution are outside this phase.
- Scanned PDF OCR and advanced extraction remain separate capabilities.

### Run tests

```powershell
pytest -v
```

### Database migration

```powershell
alembic upgrade head
```
