
# ExceptionOps AI — Backup and Restore Runbook

## 1. Purpose

This runbook describes how to back up and restore the two persistent
data components used by ExceptionOps AI:

1. PostgreSQL database.
2. Local document-storage directory.

A database backup without its corresponding document files is not a
complete application backup.

## 2. What is included

Each backup directory contains:

- `database.dump` — PostgreSQL custom-format database archive.
- `documents/` — copy of the configured local document-storage directory.
- `manifest.json` — backup timestamp, file sizes, and SHA-256 checksums.

The manifest is used to detect missing, modified, or unexpected files.

## 3. What is not included

The backup does not include:

- `.env` or `.env.docker` secrets.
- Authentication signing keys.
- Docker images.
- Application source code.
- Git history.
- Frontend dependencies.
- Operating-system configuration.

Application code should be recoverable from the private Git repository.
Secrets must be stored separately in an approved password manager or
secure configuration store.

Never store `.env` files or passwords in the backup manifest.

## 4. Backup prerequisites

Before running a backup:

- Docker Desktop must be running.
- The `db` Compose service must be healthy.
- `.env` must contain `LOCAL_DOCUMENT_DIR`.
- The configured document directory must exist.
- The backup destination must be outside the project repository and
  outside the document-storage directory.
- The backup destination must have enough free disk space.

The backup script stops the API while it creates the database dump and
copies the document directory. This pauses application writes during
the operation.

If another process writes directly to PostgreSQL or document storage,
pause that process too.

## 5. Create a backup

From the project root:

```powershell
python -m scripts.backup
```

The default destination is:

```text
%USERPROFILE%\ExceptionOpsBackups
```

To choose another destination:

```powershell
python -m scripts.backup `
    --backup-root "D:\ExceptionOpsBackups"
```

A completed directory looks like:

```text
ExceptionOpsBackups/
    exceptionops-YYYYMMDDTHHMMSSZ-xxxxxxxx/
        database.dump
        manifest.json
        documents/
            ...
```

The script prints the exact backup directory after completion.

## 6. Verify a backup

Use the exact directory printed by the backup command:

```powershell
python -m scripts.verify_backup `
    --backup-dir "C:\Users\YOUR_USER\ExceptionOpsBackups\YOUR_BACKUP_DIRECTORY"
```

A successful verification prints:

```text
BACKUP VERIFICATION PASSED
```

The verification checks:

- PostgreSQL custom archive signature.
- Database archive size.
- Database archive SHA-256.
- Every document file's size.
- Every document file's SHA-256.
- Missing document files.
- Unexpected document files.
- Unsafe relative paths in the manifest.

A passing checksum verification does not prove that PostgreSQL can
successfully restore the archive. A restore test is also required.

## 7. Restore prerequisites

Restore replaces the database objects and local document contents.

Before restoring:

- Confirm the selected backup directory.
- Verify the backup.
- Confirm that the current `.env` points to the intended database and
  document-storage directory.
- Ensure enough disk space exists for the safety backup and restored data.
- Stop any external process that writes to the database or document storage.

The restore script creates a safety backup of the current system first.

## 8. Restore a backup

Use the exact backup directory:

```powershell
python -m scripts.restore `
    --backup-dir "C:\Users\YOUR_USER\ExceptionOpsBackups\YOUR_BACKUP_DIRECTORY" `
    --confirm-restore RESTORE-EXCEPTIONOPS-DATA
```

The script:

1. Verifies the selected backup.
2. Creates a safety backup of the current system.
3. Stops the API if it was running.
4. Restores the PostgreSQL archive in a single transaction.
5. Stages the document files.
6. Replaces the document directory.
7. Retains the previous document directory as a rollback copy.
8. Restarts the API only after successful restoration.

The default safety-backup destination is:

```text
%USERPROFILE%\ExceptionOpsPreRestoreBackups
```

## 9. After restoration

Check service status:

```powershell
docker compose ps
```

Check API health:

```powershell
Invoke-RestMethod http://localhost:8001/api/v1/health
```

Check database readiness:

```powershell
Invoke-RestMethod http://localhost:8001/api/v1/ready
```

Check application logs:

```powershell
docker compose logs --tail=100 api
docker compose logs --tail=100 db
```

Verify that:

- Expected users can log in.
- Document metadata is available.
- A known restored document can be downloaded.
- Workflow and review records are present.
- Audit events are present.
- The application can process a synthetic test document.

Do not delete the safety backup or previous document directory until
the restored system has been checked.

## 10. Backup frequency and recovery objectives

For a portfolio/demo deployment, a practical starting policy is:

- Create a backup before a deployment or database migration.
- Create a backup after a significant batch of synthetic demo data.
- Create a backup before any destructive maintenance.
- Keep at least one recent backup on a separate physical disk.
- Periodically copy an encrypted backup to a separate approved location.
- Perform a restore test at least monthly while the application is active.

These are operational recommendations, not a guarantee of a specific
recovery-point objective or recovery-time objective.

Actual recovery time depends on database size, document volume, disk
speed, and available infrastructure.

## 11. Backup security

Database archives and document backups may contain confidential
business information.

- Use synthetic data for portfolio demonstrations.
- Restrict access to backup directories.
- Encrypt backup storage at rest, for example with BitLocker on Windows.
- Protect off-device backup copies with encryption.
- Do not upload backups to GitHub.
- Do not email database dumps or document archives.
- Do not put credentials in `manifest.json`.
- Rotate credentials if a backup or environment file is exposed.

The manifest uses SHA-256 to detect accidental corruption. It is not
digitally signed and does not prove who created the backup.

## 12. Recovery limitations

The backup scripts protect the PostgreSQL database and local document
storage. They do not automatically restore application source code,
environment secrets, Docker images, or host configuration.

Those components must be recovered separately.

A successful backup command and checksum verification are not a
substitute for a tested restoration.
