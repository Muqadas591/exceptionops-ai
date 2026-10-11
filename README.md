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
