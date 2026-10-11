# Acceptance Criteria — ExceptionOps AI

These criteria define intended behavior. Phase 0 documents them; implementation and test evidence will be added in later phases.

## Phase 0 — Repository foundation

- [ ] Repository name is `exceptionops-ai`.
- [ ] README accurately states that the project is in Phase 0 and no application is implemented yet.
- [ ] Product specification, architecture, acceptance criteria, threat model, and synthetic-data policy exist.
- [ ] `.gitignore` excludes secrets, local environments, build outputs, and generated data.
- [ ] `.env.example` contains placeholders only and no real credentials.
- [ ] Public repository contains no employer source code, private data, or credentials.
- [ ] Git history includes a clear initial commit.

## MVP functional acceptance

### Intake and extraction
- [ ] Supported files are accepted; unsupported, oversized, or malformed files fail safely.
- [ ] Extraction results validate against a typed schema.
- [ ] Missing or ambiguous fields are flagged rather than fabricated.
- [ ] Field evidence is available where supported by the parser/provider.

### Matching and risk
- [ ] Exact and likely duplicates are distinguished.
- [ ] Invoice totals are checked against arithmetic and matching records.
- [ ] Missing purchase orders or receipt records create explicit review states.
- [ ] Supplier bank-detail changes are treated as high risk and cannot be auto-approved.
- [ ] Policy outcomes are deterministic for the same inputs and configuration.

### Approval and actions
- [ ] Unauthorized users cannot approve or execute restricted actions.
- [ ] Approval records contain actor, decision, time, and comment when provided.
- [ ] An approved invoice is not represented as paid by implication.
- [ ] Simulated accounting actions return explicit outcomes.
- [ ] A failed or ambiguous action is visible and recoverable.
- [ ] Repeated requests do not create duplicate side effects where idempotency is supported.

### Audit and UI
- [ ] Important transitions, rule outcomes, approvals, and action results are recorded.
- [ ] Users can inspect an invoice, its exceptions, evidence, and event history.
- [ ] UI has loading, error, and empty states.
- [ ] Server-side authorization is enforced independently of UI visibility.

## Quality and security acceptance

- [ ] Unit tests cover deterministic business rules.
- [ ] API and integration tests cover normal and failure paths.
- [ ] AI-dependent tests can run with a mock provider and no paid API key.
- [ ] Logs do not contain API keys, passwords, or unnecessary payment data.
- [ ] Upload handling validates file size/type and does not trust filenames.
- [ ] Tenant isolation is tested before the product is described as production-ready.
- [ ] Database migrations and setup steps are reproducible.
- [ ] AI metrics are calculated against a documented labeled test set.
- [ ] Performance and accuracy claims are supported by recorded measurements.

## Portfolio release gate

- [ ] Clean installation and deployment are documented and verified.
- [ ] Synthetic end-to-end demo is repeatable.
- [ ] Screenshots or a short demo video show actual working functionality.
- [ ] Limitations and security boundaries are documented.
- [ ] No unsupported claim of fraud prevention, guaranteed accuracy, or production readiness is made.
