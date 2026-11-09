
from __future__ import annotations

import hashlib
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MANIFEST_FILENAME = "manifest.json"
DATABASE_FILENAME = "database.dump"
DOCUMENTS_DIRECTORY_NAME = "documents"
MANIFEST_VERSION = 1


class BackupError(RuntimeError):
    """Raised when a backup or restore precondition fails."""


def read_env_file_value(
    env_file: Path,
    variable_name: str,
) -> str:
    """Read one simple KEY=value entry without printing its value."""
    if not env_file.is_file():
        raise BackupError(
            f"Environment file not found: {env_file}"
        )

    for raw_line in env_file.read_text(
        encoding="utf-8-sig"
    ).splitlines():
        line = raw_line.strip()

        if not line or line.startswith("#"):
            continue

        if line.startswith("export "):
            line = line[len("export "):].strip()

        key, separator, value = line.partition("=")

        if not separator or key.strip() != variable_name:
            continue

        value = value.strip()

        if (
            len(value) >= 2
            and value[0] == value[-1]
            and value[0] in {"'", '"'}
        ):
            value = value[1:-1]

        if not value:
            raise BackupError(
                f"{variable_name} is empty in {env_file.name}."
            )

        return value

    raise BackupError(
        f"{variable_name} was not found in {env_file.name}."
    )


def get_document_storage_path() -> Path:
    """
    Resolve LOCAL_DOCUMENT_DIR from the Compose .env file.

    The Compose file mounts this host directory into the API container.
    """
    raw_path = read_env_file_value(
        PROJECT_ROOT / ".env",
        "LOCAL_DOCUMENT_DIR",
    )

    path = Path(raw_path).expanduser()

    if not path.is_absolute():
        path = PROJECT_ROOT / path

    return path.resolve()


def run_compose(
    arguments: list[str],
    *,
    capture_output: bool = False,
) -> subprocess.CompletedProcess[str]:
    """Run a Docker Compose command from the project directory."""
    command = ["docker", "compose", *arguments]

    try:
        return subprocess.run(
            command,
            cwd=PROJECT_ROOT,
            check=True,
            text=True,
            capture_output=capture_output,
        )
    except FileNotFoundError as exc:
        raise BackupError(
            "Docker was not found. Install Docker Desktop and ensure "
            "the docker command is available in PowerShell."
        ) from exc
    except subprocess.CalledProcessError as exc:
        detail = (
            (exc.stderr or exc.stdout or "").strip()
            if capture_output
            else "See the Docker Compose output above."
        )

        raise BackupError(
            f"Docker Compose command failed: "
            f"{' '.join(command)}. {detail}"
        ) from exc


def get_running_services() -> set[str]:
    """Return the names of currently running Compose services."""
    result = run_compose(
        ["ps", "--services", "--status", "running"],
        capture_output=True,
    )

    return {
        line.strip()
        for line in result.stdout.splitlines()
        if line.strip()
    }


def ensure_database_is_running() -> None:
    if "db" not in get_running_services():
        raise BackupError(
            "The PostgreSQL 'db' service is not running. "
            "Start it with: docker compose up -d db"
        )


def ensure_backup_root_is_safe(
    backup_root: Path,
    document_storage: Path,
) -> Path:
    """
    Ensure backups are outside the repository and document storage.

    Backups must not be copied into the directory being backed up.
    """
    root = backup_root.expanduser().resolve()
    project = PROJECT_ROOT.resolve()
    documents = document_storage.resolve()

    if root == project or root.is_relative_to(project):
        raise BackupError(
            "The backup directory must be outside the project repository."
        )

    if root == documents or root.is_relative_to(documents):
        raise BackupError(
            "The backup directory must be outside document storage."
        )

    if documents.is_relative_to(root):
        raise BackupError(
            "The backup directory cannot be a parent of document storage."
        )

    return root


def reject_symlinks(directory: Path) -> None:
    """Reject symbolic links instead of silently following them."""
    if not directory.is_dir():
        raise BackupError(
            f"Expected a directory: {directory}"
        )

    for path in directory.rglob("*"):
        if path.is_symlink():
            raise BackupError(
                f"Symbolic links are not supported in backups: {path}"
            )


def sha256_file(path: Path) -> str:
    """Calculate SHA-256 incrementally without loading a whole file."""
    digest = hashlib.sha256()

    with path.open("rb") as file_handle:
        for chunk in iter(
            lambda: file_handle.read(1024 * 1024),
            b"",
        ):
            digest.update(chunk)

    return digest.hexdigest()


def enumerate_document_files(
    documents_directory: Path,
) -> list[dict[str, Any]]:
    """Build a sorted list of document file paths, sizes, and hashes."""
    reject_symlinks(documents_directory)

    entries: list[dict[str, Any]] = []

    for path in sorted(
        documents_directory.rglob("*"),
        key=lambda item: item.as_posix().lower(),
    ):
        if not path.is_file():
            continue

        relative_path = path.relative_to(
            documents_directory
        ).as_posix()

        entries.append(
            {
                "path": relative_path,
                "size_bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            }
        )

    return entries


def build_manifest(
    backup_directory: Path,
) -> dict[str, Any]:
    """Build a manifest for a completed database and document backup."""
    database_path = backup_directory / DATABASE_FILENAME
    documents_path = (
        backup_directory / DOCUMENTS_DIRECTORY_NAME
    )

    if not database_path.is_file():
        raise BackupError(
            f"Database archive is missing: {database_path}"
        )

    with database_path.open("rb") as file_handle:
        archive_signature = file_handle.read(5)

    if archive_signature != b"PGDMP":
        raise BackupError(
            "The database file does not have the PostgreSQL custom "
            "archive signature. The dump may be incomplete or invalid."
        )

    if not documents_path.is_dir():
        raise BackupError(
            f"Document backup directory is missing: {documents_path}"
        )

    document_files = enumerate_document_files(
        documents_path
    )

    return {
        "manifest_version": MANIFEST_VERSION,
        "application": "ExceptionOps AI",
        "created_at_utc": datetime.now(
            timezone.utc
        ).isoformat(),
        "backup_contents": [
            "postgresql_database",
            "local_document_storage",
        ],
        "database": {
            "file": DATABASE_FILENAME,
            "format": "postgresql_custom",
            "size_bytes": database_path.stat().st_size,
            "sha256": sha256_file(database_path),
        },
        "documents": {
            "directory": DOCUMENTS_DIRECTORY_NAME,
            "file_count": len(document_files),
            "total_size_bytes": sum(
                item["size_bytes"]
                for item in document_files
            ),
            "files": document_files,
        },
        "verification": {
            "algorithm": "SHA-256",
            "manifest_is_signed": False,
        },
    }


def write_manifest(
    backup_directory: Path,
) -> Path:
    """Write the backup manifest after all backup files are complete."""
    manifest = build_manifest(backup_directory)

    manifest_path = (
        backup_directory / MANIFEST_FILENAME
    )

    temporary_path = (
        backup_directory / f"{MANIFEST_FILENAME}.tmp"
    )

    temporary_path.write_text(
        json.dumps(
            manifest,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    os.replace(
        temporary_path,
        manifest_path,
    )

    return manifest_path


def _safe_manifest_relative_path(
    relative_path: str,
) -> PurePosixPath:
    """Reject absolute paths, parent traversal, and Windows drive paths."""
    posix_path = PurePosixPath(relative_path)
    windows_path = PureWindowsPath(relative_path)

    if (
        not relative_path
        or posix_path.is_absolute()
        or windows_path.is_absolute()
        or windows_path.drive
        or ".." in posix_path.parts
        or "\\" in relative_path
    ):
        raise BackupError(
            f"Unsafe path found in backup manifest: {relative_path}"
        )

    return posix_path


def verify_backup_directory(
    backup_directory: Path,
) -> dict[str, Any]:
    """
    Verify the manifest, database archive hash, and every document hash.

    This verifies file integrity. It does not replace a real restore test.
    """
    backup_directory = backup_directory.expanduser().resolve()

    manifest_path = (
        backup_directory / MANIFEST_FILENAME
    )

    if not manifest_path.is_file():
        raise BackupError(
            "manifest.json is missing from the backup directory."
        )

    try:
        manifest = json.loads(
            manifest_path.read_text(encoding="utf-8")
        )
    except (OSError, json.JSONDecodeError) as exc:
        raise BackupError(
            "manifest.json could not be read as valid JSON."
        ) from exc

    if manifest.get("manifest_version") != MANIFEST_VERSION:
        raise BackupError(
            "Unsupported or missing backup manifest version."
        )

    database = manifest.get("database", {})
    database_filename = database.get("file")

    if database_filename != DATABASE_FILENAME:
        raise BackupError(
            "Unexpected database archive filename in manifest."
        )

    database_path = backup_directory / DATABASE_FILENAME

    if not database_path.is_file():
        raise BackupError(
            "The PostgreSQL database archive is missing."
        )

    with database_path.open("rb") as file_handle:
        signature = file_handle.read(5)

    if signature != b"PGDMP":
        raise BackupError(
            "The database archive signature is invalid."
        )

    if database_path.stat().st_size != database.get("size_bytes"):
        raise BackupError(
            "The database archive size does not match the manifest."
        )

    if sha256_file(database_path) != database.get("sha256"):
        raise BackupError(
            "The database archive SHA-256 does not match the manifest."
        )

    documents = manifest.get("documents", {})
    directory_name = documents.get("directory")

    if directory_name != DOCUMENTS_DIRECTORY_NAME:
        raise BackupError(
            "Unexpected document directory name in manifest."
        )

    documents_path = (
        backup_directory / DOCUMENTS_DIRECTORY_NAME
    )

    if not documents_path.is_dir():
        raise BackupError(
            "The document backup directory is missing."
        )

    expected_files = documents.get("files")

    if not isinstance(expected_files, list):
        raise BackupError(
            "The document file list in the manifest is invalid."
        )

    expected_paths: set[str] = set()

    for entry in expected_files:
        if not isinstance(entry, dict):
            raise BackupError(
                "A document entry in the manifest is invalid."
            )

        relative_path = entry.get("path")

        if not isinstance(relative_path, str):
            raise BackupError(
                "A document path in the manifest is invalid."
            )

        safe_relative = _safe_manifest_relative_path(
            relative_path
        )

        normalized_path = safe_relative.as_posix()

        if normalized_path in expected_paths:
            raise BackupError(
                f"Duplicate document path in manifest: {normalized_path}"
            )

        expected_paths.add(normalized_path)

        file_path = documents_path.joinpath(
            *safe_relative.parts
        )

        if not file_path.is_file() or file_path.is_symlink():
            raise BackupError(
                f"Document file is missing or unsafe: {normalized_path}"
            )

        if file_path.stat().st_size != entry.get("size_bytes"):
            raise BackupError(
                f"Document size mismatch: {normalized_path}"
            )

        if sha256_file(file_path) != entry.get("sha256"):
            raise BackupError(
                f"Document checksum mismatch: {normalized_path}"
            )

    actual_files = enumerate_document_files(
        documents_path
    )

    actual_paths = {
        item["path"]
        for item in actual_files
    }

    if actual_paths != expected_paths:
        missing = sorted(expected_paths - actual_paths)
        unexpected = sorted(actual_paths - expected_paths)

        raise BackupError(
            "The document directory does not match the manifest. "
            f"Missing: {missing}; unexpected: {unexpected}"
        )

    if len(expected_files) != documents.get("file_count"):
        raise BackupError(
            "The document file count does not match the manifest."
        )

    return manifest
