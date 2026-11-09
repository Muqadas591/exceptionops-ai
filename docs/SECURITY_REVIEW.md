
# ExceptionOps AI — Security Review

**Stage:** 8.8.5  
**Status:** Security hardening implementation  
**Scope:** Application-level security controls

---

## 1. Purpose

This document records the security controls implemented in
ExceptionOps AI and identifies the remaining operational risks.

This is an engineering security review, not a penetration-test
report, compliance certification, or guarantee of security.

## 2. Authentication

Implemented controls:

- Password hashing using Argon2 through pwdlib.
- Password verification without storing plaintext passwords.
- JWT-based bearer authentication.
- HS256 signature verification.
- Required token claims.
- JWT issuer validation.
- JWT audience validation.
- Access-token-purpose validation.
- Unique JWT identifiers.
- Short-lived access tokens.
- Inactive-user rejection.
- Database-backed user identity.

JWT tokens contain:

- sub
- iat
- exp
- iss
- aud
- jti
- token_use

Roles are not trusted from token claims.
The current role is loaded from the database.

### Token limitations

The application does not implement individual token revocation
or refresh-token rotation.

Disabling a user prevents future requests using that user's token.
Changing the JWT signing secret invalidates tokens signed with the
previous secret.

Users must sign in again after JWT claim changes.

## 3. Authorization

Implemented controls:

- Role-based authorization dependencies.
- Admin-only retention operations.
- Reviewer authorization for review operations.
- Action-operator authorization for action execution.
- Audit access restrictions.
- Database-backed role checks.

The frontend must never be treated as the authority for access
control. Authorization is enforced by backend dependencies.

### Multi-tenancy limitation

The current application does not implement tenant/workspace
isolation at the database level.

It must not be presented as a multi-tenant SaaS security model
until tenant ownership, tenant-scoped queries, and cross-tenant
authorization tests have been implemented.

## 4. HTTP security

Implemented controls:

- Trusted host validation in production.
- Explicit CORS origins.
- Wildcard CORS rejection in production.
- HTTPS requirement for non-local production CORS origins.
- X-Content-Type-Options: nosniff.
- X-Frame-Options: DENY.
- Referrer-Policy: no-referrer.
- Permissions-Policy restrictions.
- HSTS for production HTTPS requests.
- No-store cache policy for API responses.
- Production API documentation disabled.

### Deployment requirement

Public deployments must terminate HTTPS at a trusted reverse
proxy or hosting ingress.

If TLS terminates at a reverse proxy, configure the proxy to
send correct HTTPS information and configure trusted proxy
handling carefully.

Do not trust arbitrary forwarded headers from public clients.

## 5. Document security

Implemented controls:

- Allowed extensions: PDF, TXT, CSV.
- Configurable upload-size limit.
- Empty-file rejection.
- Basic PDF signature validation.
- UTF-8 validation for text files.
- NUL-byte rejection.
- Filename sanitization.
- Generated storage keys.
- Path traversal protection.
- SHA-256 content checksums.
- Duplicate-content detection.
- Local document storage.

### Limitations

Basic file validation is not malware scanning.

PDF signature checks do not prove that a document is harmless.
PDF parsing may still encounter malformed or resource-intensive
documents.

Before accepting documents from untrusted public users, consider:

- Malware scanning.
- Isolated document parsing.
- CPU and memory limits.
- Request rate limits.
- Additional parser resource limits.

## 6. Secrets management

Implemented controls:

- Environment-based configuration.
- Production placeholder-secret rejection.
- Production secret length and diversity checks.
- Database placeholder-password checks.
- Environment files excluded from Git.
- Secret values excluded from security-check output.

Operational requirements:

- Never commit .env or .env.docker.
- Never upload real credentials to public repositories.
- Rotate secrets if exposure is suspected.
- Use separate secrets for development and production.
- Restrict access to deployment environment variables.

Generate a secret with a cryptographically secure generator.

## 7. Logging and audit

Implemented controls:

- Request IDs.
- Structured JSON logging in production.
- Request method, path, status, and duration.
- Exception type logging without returning internal exception
  details to API clients.
- Audit events associated with business operations.

Never log:

- Passwords.
- Bearer tokens.
- Authorization headers.
- API keys.
- Database credentials.
- Complete uploaded document contents.

### Audit limitation

The audit trail is append-oriented at the application level.
It is not cryptographically tamper-proof against a database
administrator or an attacker with direct database access.

For stronger tamper evidence, consider external immutable
audit storage or signed audit checkpoints.

## 8. Database security

Implemented controls:

- SQLAlchemy ORM and parameterized query construction.
- Database sessions closed after requests.
- Production SQLite rejection.
- Database connection pool configuration.
- Database access through application dependencies.

Operational requirements:

- Use a least-privilege database account.
- Do not expose PostgreSQL publicly.
- Restrict database network access.
- Protect database backups.
- Encrypt storage volumes where required.

## 9. Frontend security

The frontend stores access tokens in sessionStorage.

This reduces persistence compared with long-lived localStorage
but does not protect tokens from malicious JavaScript executing
in the same browser origin.

Production frontend hosting should configure an appropriate
Content Security Policy and other browser security headers.

Avoid unsafe HTML rendering and untrusted script execution.

## 10. Rate limiting

The application does not implement distributed login or API
rate limiting.

A production reverse proxy or hosting ingress must enforce
appropriate limits for:

- Login attempts.
- Document uploads.
- Expensive extraction operations.
- Workflow operations.
- Other resource-intensive endpoints.

An in-memory limiter is not a sufficient replacement for
distributed rate limiting.

## 11. Dependency security

Review dependencies regularly.

Suggested checks:

- pip-audit
- GitHub dependency alerts
- Container image vulnerability scanning
- Dependency update review

Do not automatically upgrade production dependencies without
running the complete test suite.

## 12. Backup security

Backup files contain database and document data.

Protect backup directories with:

- Restricted filesystem permissions.
- Encryption at rest.
- Secure off-site storage where required.
- Separate backup credentials.
- Periodic restore tests.

SHA-256 manifests verify integrity but do not provide
cryptographic authenticity or confidentiality.

## 13. Remaining production requirements

Before processing real customer or financial data:

- Complete a deployment-specific threat assessment.
- Configure HTTPS.
- Configure reverse-proxy rate limiting.
- Implement tenant isolation if multiple organizations
  will share the same deployment.
- Evaluate malware scanning and isolated document parsing.
- Configure frontend CSP.
- Configure encrypted backup storage.
- Review database privileges.
- Configure monitoring and incident response.
- Perform an independent penetration test where appropriate.
- Review applicable privacy and regulatory requirements.

## 14. Verification commands

Run:

    python -m compileall app scripts tests

    pytest tests/test_config.py -q

    pytest tests/test_auth_security.py -q

    pytest tests/test_input_security.py -q

    pytest tests/test_security_hardening.py -q

    pytest -q

    python -m scripts.security_check

The command above checks the current environment and reports
production-only checks as warnings when `APP_ENV` is not
`production`. Run the following only in an environment configured
with valid production settings (including a strong authentication
secret, persistent database, and absolute document-storage path):

    python -m scripts.security_check --require-production

The repository's `.env` is for local development. `.env.docker` is
loaded by Docker Compose, which also injects the database URL and
authentication secret; running the command directly from the
repository does not load that Compose configuration. Do not set
`APP_ENV=production` by itself to bypass this check.

## 15. Review conclusion

Stage 8.8.5 strengthens application-level authentication,
configuration validation, browser response headers, and
document-storage security tests.

Completion of this stage does not imply that ExceptionOps AI
has passed a penetration test or is certified for processing
regulated financial data.
