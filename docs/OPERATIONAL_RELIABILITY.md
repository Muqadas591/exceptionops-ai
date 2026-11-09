
# Operational Reliability — ExceptionOps AI

## 1. Purpose

This document describes the operational checks and recovery procedures
for the ExceptionOps AI application.

The application depends on:

- FastAPI / Uvicorn
- PostgreSQL
- Local document storage
- SQLAlchemy connection pooling
- Workflow and action execution services

The application uses synthetic portfolio data. Do not use this runbook
to test destructive recovery operations against real business data.

## 2. Health endpoints

### Liveness

GET /api/v1/health

A successful response means the API process can respond.

This endpoint intentionally does not query PostgreSQL or document
storage. It should remain available when a dependency is temporarily
unavailable.

### Readiness

GET /api/v1/ready

A successful response requires:

- PostgreSQL query succeeds.
- Document storage directory exists.
- Document storage directory is writable.

Expected HTTP status:

- 200: application is ready.
- 503: one or more required dependencies are unavailable.

## 3. Reliability diagnostic

Run from the project root with the virtual environment active:

    python -m scripts.reliability_check

A healthy result reports:

- database: connected
- storage: writable
- status: healthy

The command exits with code 1 if a dependency is unavailable.

## 4. Database unavailable

Symptoms:

- /api/v1/health returns 200.
- /api/v1/ready returns 503.
- API requests requiring PostgreSQL may fail.

Procedure:

1. Check the database container:

       docker compose ps

2. Inspect database logs:

       docker compose logs --tail=100 db

3. Check PostgreSQL readiness:

       docker compose exec db pg_isready -U exceptionops -d exceptionops

4. If the database container is stopped, start it:

       docker compose up -d db

5. Wait for the database health check to pass.

6. Recheck API readiness:

       curl.exe -i http://localhost:8000/api/v1/ready

Do not delete the PostgreSQL volume to solve a connection problem.

## 5. Document storage unavailable

Symptoms:

- /api/v1/health returns 200.
- /api/v1/ready returns 503 with storage unavailable.
- Uploads or document reads may fail.

Procedure:

1. Check the LOCAL_DOCUMENT_DIR value in the local environment.
2. Confirm that the host directory exists.
3. Confirm that the Docker API container can write to
   /app/local_documents.
4. Check available disk space on the host.
5. Restore the expected directory or permissions.
6. Restart the API if required:

       docker compose restart api

7. Run the reliability diagnostic again.

Do not delete local document files as a troubleshooting shortcut.

## 6. Application restart

Inspect service state:

    docker compose ps

Inspect API logs:

    docker compose logs --tail=200 api

Restart only the API:

    docker compose restart api

Restart the complete stack:

    docker compose down
    docker compose up -d --build

The normal shutdown path disposes the SQLAlchemy connection pool.
PostgreSQL data remains in the named Docker volume.

Do not use `docker compose down -v` during normal restarts.
The `-v` option removes named volumes and can destroy database data.

## 7. Workflow recovery

Workflow recovery is an explicit business operation.

1. Inspect the workflow and its latest status.
2. Inspect its workflow events and audit events.
3. Confirm that the required extraction and evaluation data exists.
4. If the workflow is in failed state, determine the root cause.
5. Correct the underlying problem.
6. Use the existing retry operation only for a workflow that is
   eligible for retry.
7. Verify the resulting workflow status and audit history.

Do not automatically retry all failed workflows.

## 8. Action recovery and idempotency

Action execution can have external side effects.

The application distinguishes:

- pending
- in_progress
- succeeded
- failed
- uncertain

A failed action with a known failure may be eligible for retry.

An uncertain action must be reconciled by an authorized operator.
The remote system may have completed the action even if the application
did not receive a confirmation.

Never automatically retry an uncertain action.

Before retrying:

1. Inspect the action record.
2. Inspect the action audit history.
3. Check the external system or simulation result.
4. Reconcile the outcome.
5. Retry only after confirming that the action was not executed.

Continue using the existing idempotency key and request fingerprint
controls. Do not create a new key to bypass an existing action record.

## 9. Backup and restore

Use the existing procedures in:

    docs/BACKUP_AND_RESTORE.md

Verify a backup before relying on it.

Restore is a destructive operation. Test it only against a disposable
synthetic environment after confirming which database and document
directory will be replaced.

## 10. Operational monitoring checklist

After deployment or restart:

- [ ] PostgreSQL container is running.
- [ ] PostgreSQL health check is healthy.
- [ ] API container is running.
- [ ] API Docker health check is healthy.
- [ ] GET /api/v1/health returns 200.
- [ ] GET /api/v1/ready returns 200.
- [ ] Reliability diagnostic reports healthy.
- [ ] API logs contain no repeated startup or dependency failures.
- [ ] A synthetic document upload can be completed.
- [ ] A synthetic workflow can be advanced.
- [ ] An action can be reviewed without creating an unintended
      external side effect.

## 11. Important limitations

This stage provides dependency checks and controlled operational
procedures. It does not implement:

- Distributed background job scheduling.
- Automatic workflow retries.
- Automatic retry of uncertain external actions.
- Multi-instance distributed locking.
- External uptime monitoring or alert delivery.
- Automated database failover.
- Object storage replication.
- Malware scanning.
- A cryptographically tamper-proof audit log.

These require separate infrastructure and security decisions.
