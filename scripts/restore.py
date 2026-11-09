
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

from scripts.backup_common import (
    BackupError,
    DATABASE_FILENAME,
    DOCUMENTS_DIRECTORY_NAME,
    ensure_backup_root_is_safe,
    ensure_database_is_running,
    get_document_storage_path,
    get_running_services,
    run_compose,
    verify_backup_directory,
)


RESTORE_CONFIRMATION = "RESTORE-EXCEPTIONOPS-DATA"
CONTAINER_DUMP_PATH = "/tmp/exceptionops-restore.dump"


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Restore an ExceptionOps database and local document backup."
        )
    )

    parser.add_argument(
        "--backup-dir",
        type=Path,
        required=True,
        help="Completed backup directory to restore.",
    )

    parser.add_argument(
        "--confirm-restore",
        required=True,
        choices=[RESTORE_CONFIRMATION],
        help=(
            "Explicit confirmation required because this operation "
            "replaces the current database and document storage."
        ),
    )

    parser.add_argument(
        "--safety-backup-root",
        type=Path,
        default=Path.home() / "ExceptionOpsPreRestoreBackups",
        help=(
            "Destination for a backup of the current state before "
            "restoration."
        ),
    )

    return parser.parse_args()


def create_safety_backup(
    backup_root: Path,
) -> None:
    """
    Back up the current state before replacing it.

    The backup command pauses and resumes the API as necessary.
    """
    command = [
        sys.executable,
        "-m",
        "scripts.backup",
        "--backup-root",
        str(backup_root),
    ]

    print("Creating a safety backup of the current system...")

    subprocess.run(
        command,
        cwd=Path(__file__).resolve().parents[1],
        check=True,
    )


def restore_document_directory(
    backup_documents: Path,
    target_documents: Path,
) -> Path | None:
    """
    Stage document files beside the target and then rename directories.

    The previous directory is retained as a rollback copy. It is not
    automatically deleted after a successful restore.
    """
    target_documents = target_documents.resolve()
    target_parent = target_documents.parent

    if target_documents == target_parent:
        raise BackupError(
            "The configured document storage path is unsafe."
        )

    target_parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    restore_id = uuid.uuid4().hex[:8]

    staging_directory = (
        target_parent
        / f".{target_documents.name}.restore-staging-{restore_id}"
    )

    timestamp = datetime.now(
        timezone.utc
    ).strftime("%Y%m%dT%H%M%SZ")

    previous_directory: Path | None = None

    try:
        print("Preparing document files in a staging directory...")

        shutil.copytree(
            backup_documents,
            staging_directory,
        )

        if target_documents.exists():
            if not target_documents.is_dir():
                raise BackupError(
                    "The current document storage path is not a directory."
                )

            previous_directory = (
                target_parent
                / f"{target_documents.name}.pre-restore-{timestamp}"
            )

            if previous_directory.exists():
                raise BackupError(
                    "The proposed pre-restore directory already exists."
                )

            target_documents.rename(
                previous_directory
            )

        try:
            staging_directory.rename(
                target_documents
            )
        except Exception:
            # Restore the old directory if the final rename fails.
            if (
                previous_directory is not None
                and previous_directory.exists()
                and not target_documents.exists()
            ):
                previous_directory.rename(
                    target_documents
                )

            raise

        return previous_directory

    finally:
        if staging_directory.exists():
            shutil.rmtree(
                staging_directory,
                ignore_errors=True,
            )


def restore_database(
    database_archive: Path,
) -> None:
    """Restore PostgreSQL objects from a verified custom-format archive."""
    print("Copying the verified database archive into PostgreSQL...")

    run_compose(
        [
            "exec",
            "-T",
            "db",
            "rm",
            "-f",
            CONTAINER_DUMP_PATH,
        ]
    )

    run_compose(
        [
            "cp",
            str(database_archive),
            f"db:{CONTAINER_DUMP_PATH}",
        ]
    )

    print("Checking the archive with PostgreSQL pg_restore...")

    run_compose(
        [
            "exec",
            "-T",
            "db",
            "pg_restore",
            "--list",
            CONTAINER_DUMP_PATH,
        ],
        capture_output=True,
    )

    print("Restoring database objects...")

    run_compose(
        [
            "exec",
            "-T",
            "db",
            "sh",
            "-c",
            (
                'pg_restore '
                '--clean '
                '--if-exists '
                '--no-owner '
                '--no-privileges '
                '--single-transaction '
                '--exit-on-error '
                '-U "$POSTGRES_USER" '
                '-d "$POSTGRES_DB" '
                f'"{CONTAINER_DUMP_PATH}"'
            ),
        ]
    )


def perform_restore(
    backup_directory: Path,
    safety_backup_root: Path,
) -> None:
    backup_directory = backup_directory.expanduser().resolve()

    # Validate all backup files before changing the running system.
    print("Verifying the selected backup...")

    manifest = verify_backup_directory(
        backup_directory
    )

    document_storage = get_document_storage_path()

    if (
        backup_directory == document_storage
        or backup_directory.is_relative_to(document_storage)
        or document_storage.is_relative_to(backup_directory)
    ):
        raise BackupError(
            "The backup directory and live document storage must "
            "be separate directories."
        )

    ensure_backup_root_is_safe(
        safety_backup_root,
        document_storage,
    )

    ensure_database_is_running()

    # Preserve the current state before replacing anything.
    create_safety_backup(
        safety_backup_root
    )

    # The safety backup may have restarted the API.
    running_services = get_running_services()
    api_was_running = "api" in running_services

    if api_was_running:
        print("Stopping the API before restoration...")
        run_compose(["stop", "api"])

    restore_completed = False

    try:
        database_archive = (
            backup_directory / DATABASE_FILENAME
        )

        backup_documents = (
            backup_directory / DOCUMENTS_DIRECTORY_NAME
        )

        # The database restore is transactional. If pg_restore fails,
        # PostgreSQL rolls back the restore transaction.
        restore_database(
            database_archive
        )

        print("Restoring local document storage...")

        previous_directory = restore_document_directory(
            backup_documents,
            document_storage,
        )

        restore_completed = True

        print("")
        print("RESTORE COMPLETED SUCCESSFULLY")
        print(
            "Backup created at UTC: "
            f"{manifest['created_at_utc']}"
        )
        print(
            "Restored document files: "
            f"{manifest['documents']['file_count']}"
        )

        if previous_directory is not None:
            print(
                "Previous document directory retained at: "
                f"{previous_directory}"
            )

        print(
            "Safety backup root: "
            f"{safety_backup_root.resolve()}"
        )

    finally:
        try:
            run_compose(
                [
                    "exec",
                    "-T",
                    "db",
                    "rm",
                    "-f",
                    CONTAINER_DUMP_PATH,
                ]
            )
        except BackupError:
            print(
                "WARNING: Could not remove the temporary restore "
                "archive from the database container.",
                file=sys.stderr,
            )

        if restore_completed and api_was_running:
            print("Restarting the API after successful restoration...")
            run_compose(["start", "api"])

        elif not restore_completed and api_was_running:
            print(
                "RESTORE DID NOT COMPLETE. The API has been left stopped "
                "to avoid serving inconsistent data. Inspect the error, "
                "then recover using the safety backup if necessary.",
                file=sys.stderr,
            )


def main() -> int:
    args = parse_arguments()

    try:
        perform_restore(
            args.backup_dir,
            args.safety_backup_root,
        )
        return 0

    except BackupError as exc:
        print(f"RESTORE ERROR: {exc}", file=sys.stderr)
        return 1

    except subprocess.CalledProcessError:
        print(
            "RESTORE ERROR: A Docker or PostgreSQL command failed. "
            "The API may have been left stopped. Inspect the command "
            "output and use the safety backup if recovery is needed.",
            file=sys.stderr,
        )
        return 1

    except OSError as exc:
        print(f"RESTORE FILE ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
