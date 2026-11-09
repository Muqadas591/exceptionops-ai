
from __future__ import annotations

import argparse
import shutil
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

from scripts.backup_common import (
    BackupError,
    DATABASE_FILENAME,
    PROJECT_ROOT,
    build_manifest,
    ensure_backup_root_is_safe,
    ensure_database_is_running,
    get_document_storage_path,
    get_running_services,
    reject_symlinks,
    run_compose,
    write_manifest,
)


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Create a consistent ExceptionOps PostgreSQL and "
            "local-document backup."
        )
    )

    parser.add_argument(
        "--backup-root",
        type=Path,
        default=Path.home() / "ExceptionOpsBackups",
        help=(
            "Backup destination outside the project and document "
            "storage directories."
        ),
    )

    return parser.parse_args()


def create_backup(backup_root: Path) -> Path:
    document_source = get_document_storage_path()

    if not document_source.is_dir():
        raise BackupError(
            "The configured LOCAL_DOCUMENT_DIR does not exist: "
            f"{document_source}"
        )

    reject_symlinks(document_source)

    safe_backup_root = ensure_backup_root_is_safe(
        backup_root,
        document_source,
    )

    if (
        safe_backup_root == document_source
        or safe_backup_root.is_relative_to(document_source)
    ):
        raise BackupError(
            "Backup destination cannot be inside document storage."
        )

    safe_backup_root.mkdir(
        parents=True,
        exist_ok=True,
    )

    ensure_database_is_running()

    running_services = get_running_services()
    api_was_running = "api" in running_services
    api_was_stopped = False

    timestamp = datetime.now(
        timezone.utc
    ).strftime("%Y%m%dT%H%M%SZ")

    backup_id = (
        f"exceptionops-{timestamp}-{uuid.uuid4().hex[:8]}"
    )

    backup_directory = safe_backup_root / backup_id

    backup_directory.mkdir(
        parents=False,
        exist_ok=False,
    )

    documents_destination = (
        backup_directory / "documents"
    )

    database_destination = (
        backup_directory / DATABASE_FILENAME
    )

    try:
        if api_was_running:
            print("Stopping the API to pause application writes...")
            run_compose(["stop", "api"])
            api_was_stopped = True

        print("Creating PostgreSQL custom-format dump...")

        run_compose(
            [
                "exec",
                "-T",
                "db",
                "sh",
                "-c",
                (
                    'pg_dump -U "$POSTGRES_USER" '
                    '-d "$POSTGRES_DB" '
                    '-Fc '
                    '-f /tmp/exceptionops-backup.dump'
                ),
            ]
        )

        print("Checking the PostgreSQL archive...")

        run_compose(
            [
                "exec",
                "-T",
                "db",
                "pg_restore",
                "--list",
                "/tmp/exceptionops-backup.dump",
            ],
            capture_output=True,
        )

        print("Copying the database archive to the backup directory...")

        run_compose(
            [
                "cp",
                "db:/tmp/exceptionops-backup.dump",
                str(database_destination),
            ]
        )

        run_compose(
            [
                "exec",
                "-T",
                "db",
                "rm",
                "-f",
                "/tmp/exceptionops-backup.dump",
            ]
        )

        if not database_destination.is_file():
            raise BackupError(
                "The PostgreSQL archive was not copied to the host."
            )

        print("Copying local document storage...")

        shutil.copytree(
            document_source,
            documents_destination,
        )

        print("Generating the SHA-256 backup manifest...")

        manifest_path = write_manifest(
            backup_directory
        )

        manifest = build_manifest(
            backup_directory
        )

        print("")
        print("Backup completed successfully.")
        print(f"Backup directory: {backup_directory}")
        print(f"Database archive: {database_destination}")
        print(f"Document files: {manifest['documents']['file_count']}")
        print(
            "Document bytes: "
            f"{manifest['documents']['total_size_bytes']}"
        )
        print(f"Manifest: {manifest_path}")

        return backup_directory

    except Exception:
        print(
            "Backup failed. Removing the incomplete backup directory.",
            file=sys.stderr,
        )

        shutil.rmtree(
            backup_directory,
            ignore_errors=True,
        )

        raise

    finally:
        if api_was_stopped:
            print("Restarting the API service...")

            try:
                run_compose(["start", "api"])
            except BackupError:
                print(
                    "WARNING: The backup operation ended, but the API "
                    "could not be restarted. Run: docker compose start api",
                    file=sys.stderr,
                )


def main() -> int:
    args = parse_arguments()

    try:
        create_backup(args.backup_root)
        return 0

    except BackupError as exc:
        print(f"BACKUP ERROR: {exc}", file=sys.stderr)
        return 1

    except OSError as exc:
        print(f"FILE ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
