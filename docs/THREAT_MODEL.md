# Initial Threat Model — ExceptionOps AI

**Status:** Initial design notes for Phase 0, not a security certification.

## Assets to protect

- Supplier and invoice records
- Business financial metadata
- User identities, roles, and approval decisions
- AI-provider credentials
- Email and accounting connector credentials
- Audit history and workflow integrity

## Threats and planned controls

| Threat | Example | Planned control |
|---|---|---|
| Prompt injection in documents | Invoice text instructs the model to ignore controls | Treat document text as data; isolate instructions; never let model output authorize actions |
| Malicious upload | Crafted or oversized PDF | File size/type validation, parser limits, safe errors, and later malware-scanning consideration |
| Fabricated extraction | Model invents invoice number or bank detail | Strict schemas, source evidence, confidence/review gates, deterministic validation |
| Duplicate processing | Same invoice submitted repeatedly | Content hashes, normalized duplicate checks, idempotency keys |
| Unauthorized approval | User calls an approval endpoint directly | Server-side authentication and role authorization on every operation |
| Unsafe payment implication | UI labels an approved invoice as paid | Separate approval and action states; no real payment execution in MVP |
| Connector retry duplicates an action | Timeout occurs after an email or update succeeds | Persist action attempts, use idempotency where supported, reconcile ambiguous outcomes |
| Cross-tenant data access | User changes an invoice ID to access another company | Tenant-scoped queries, authorization checks, integration tests |
| Secret leakage | API key committed to Git or printed in logs | `.env` ignored, secret scanning where available, redaction, key rotation procedures |
| Audit tampering | User alters or deletes an event | Restrict write access, append-oriented events, monitor access; stronger tamper evidence can be considered later |
| Supply-chain risk | Vulnerable dependency | Pin/review dependencies, automated checks, updates, and minimal dependency set |

## Trust boundaries

1. Uploaded documents and extracted text are untrusted.
2. AI responses are untrusted.
3. Client-side role or tenant identifiers are not authoritative.
4. Connector results can be delayed, incomplete, or ambiguous.
5. Secrets are accessible only to authorized runtime components.

## Required before production use

- Threat review against the actual deployment
- Authentication and authorization tests
- Tenant-isolation tests
- Secure upload and retention policy
- Dependency and container scanning
- Secret management and rotation
- Backup and recovery test
- Privacy review and data-processing agreements as applicable
- Monitoring and incident-response procedures

This document does not imply that the system is secure merely because the controls are listed.
