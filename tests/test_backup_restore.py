
import json

import pytest

from scripts.backup_common import (
    BackupError,
    verify_backup_directory,
    write_manifest,
)


def create_sample_backup(tmp_path):
    backup_directory = tmp_path / "sample-backup"
    backup_directory.mkdir()

    documents_directory = backup_directory / "documents"
    documents_directory.mkdir()

    (backup_directory / "database.dump").write_bytes(
        b"PGDMPsynthetic-postgresql-archive"
    )

    (documents_directory / "invoice-one.txt").write_text(
        "Synthetic invoice one",
        encoding="utf-8",
    )

    nested_directory = documents_directory / "nested"
    nested_directory.mkdir()

    (nested_directory / "invoice-two.csv").write_text(
        "invoice_id,amount\nSYN-001,100",
        encoding="utf-8",
    )

    write_manifest(backup_directory)

    return backup_directory


def test_manifest_verifies_database_and_all_document_files(
    tmp_path,
):
    backup_directory = create_sample_backup(tmp_path)

    manifest = verify_backup_directory(
        backup_directory
    )

    assert manifest["application"] == "ExceptionOps AI"
    assert manifest["database"]["format"] == "postgresql_custom"
    assert manifest["documents"]["file_count"] == 2


def test_verification_rejects_modified_document(
    tmp_path,
):
    backup_directory = create_sample_backup(tmp_path)

    document_path = (
        backup_directory
        / "documents"
        / "invoice-one.txt"
    )

    document_path.write_text(
        "Modified content",
        encoding="utf-8",
    )

    with pytest.raises(
        BackupError,
        match="size mismatch|checksum mismatch",
    ):
        verify_backup_directory(backup_directory)


def test_verification_rejects_modified_database_archive(
    tmp_path,
):
    backup_directory = create_sample_backup(tmp_path)

    database_path = backup_directory / "database.dump"

    database_path.write_bytes(
        b"PGDMPmodified-archive-content"
    )

    with pytest.raises(
        BackupError,
        match="size does not match|SHA-256",
    ):
        verify_backup_directory(backup_directory)


def test_verification_rejects_unlisted_document_file(
    tmp_path,
):
    backup_directory = create_sample_backup(tmp_path)

    extra_file = (
        backup_directory
        / "documents"
        / "unexpected.txt"
    )

    extra_file.write_text(
        "Unexpected file",
        encoding="utf-8",
    )

    with pytest.raises(
        BackupError,
        match="does not match the manifest",
    ):
        verify_backup_directory(backup_directory)


def test_verification_rejects_path_traversal_in_manifest(
    tmp_path,
):
    backup_directory = create_sample_backup(tmp_path)

    manifest_path = backup_directory / "manifest.json"

    manifest = json.loads(
        manifest_path.read_text(encoding="utf-8")
    )

    manifest["documents"]["files"][0]["path"] = "../outside.txt"

    manifest_path.write_text(
        json.dumps(manifest),
        encoding="utf-8",
    )

    with pytest.raises(
        BackupError,
        match="Unsafe path",
    ):
        verify_backup_directory(backup_directory)


def test_verification_rejects_missing_manifest(
    tmp_path,
):
    backup_directory = tmp_path / "empty-backup"
    backup_directory.mkdir()

    with pytest.raises(
        BackupError,
        match="manifest.json is missing",
    ):
        verify_backup_directory(backup_directory)


def test_verification_rejects_wrong_database_signature(
    tmp_path,
):
    backup_directory = create_sample_backup(tmp_path)

    database_path = backup_directory / "database.dump"
    database_path.write_bytes(b"NOTPGDMP")

    # Rebuild the manifest to ensure the signature check is tested
    # independently of the old checksum.
    manifest_path = backup_directory / "manifest.json"
    manifest = json.loads(
        manifest_path.read_text(encoding="utf-8")
    )

    import hashlib

    manifest["database"]["size_bytes"] = database_path.stat().st_size
    manifest["database"]["sha256"] = hashlib.sha256(
        database_path.read_bytes()
    ).hexdigest()

    manifest_path.write_text(
        json.dumps(manifest),
        encoding="utf-8",
    )

    with pytest.raises(
        BackupError,
        match="signature is invalid",
    ):
        verify_backup_directory(backup_directory)
