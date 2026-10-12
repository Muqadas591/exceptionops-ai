
import hashlib
import os
import re
import uuid
from dataclasses import dataclass
from pathlib import Path

from fastapi import UploadFile

from app.core.config import Settings


ALLOWED_EXTENSIONS = {".pdf", ".txt", ".csv"}
CHUNK_SIZE = 64 * 1024


class DocumentValidationError(Exception):
    """The uploaded file failed a validation rule."""


class UploadTooLargeError(DocumentValidationError):
    """The upload exceeded the configured size limit."""


@dataclass(frozen=True)
class StoredFile:
    original_filename: str
    storage_key: str
    extension: str
    content_type: str
    file_size_bytes: int
    checksum_sha256: str


def sanitize_display_filename(filename: str | None) -> str:
    """Return a safe display name; never use it as a path."""
    raw_name = (filename or "upload").replace("\\", "/")
    name = raw_name.split("/")[-1]
    name = re.sub(r"[\x00-\x1f\x7f]", "", name).strip()

    if not name or name in {".", ".."}:
        name = "upload"

    return name[:255]


def _detect_content_type(extension: str) -> str:
    return {
        ".pdf": "application/pdf",
        ".txt": "text/plain",
        ".csv": "text/csv",
    }[extension]


def _validate_file_content(path: Path, extension: str) -> None:
    """Perform basic format checks; this is not malware scanning."""
    if path.stat().st_size == 0:
        raise DocumentValidationError("Empty files are not accepted.")

    with path.open("rb") as file:
        prefix = file.read(8)

    if extension == ".pdf":
        if not prefix.startswith(b"%PDF-"):
            raise DocumentValidationError(
                "The file does not have a valid basic PDF signature."
            )
        return

    # TXT and CSV are treated as UTF-8 text.
    try:
        with path.open("rb") as file:
            while chunk := file.read(CHUNK_SIZE):
                if b"\x00" in chunk:
                    raise DocumentValidationError(
                        "Text files must not contain NUL bytes."
                    )
                # Validate UTF-8 incrementally below instead of per chunk.
    except OSError as exc:
        raise DocumentValidationError(
            "Could not read the uploaded file."
        ) from exc

    import codecs

    decoder = codecs.getincrementaldecoder("utf-8-sig")()
    try:
        with path.open("rb") as file:
            while chunk := file.read(CHUNK_SIZE):
                decoder.decode(chunk)
        decoder.decode(b"", final=True)
    except UnicodeDecodeError as exc:
        raise DocumentValidationError(
            "TXT and CSV files must contain valid UTF-8 text."
        ) from exc


async def save_upload(
    upload: UploadFile,
    settings: Settings,
) -> StoredFile:
    """Validate and save an upload under a generated storage key."""
    original_filename = sanitize_display_filename(upload.filename)
    extension = Path(original_filename).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise DocumentValidationError(
            "Unsupported file extension. Allowed types: PDF, TXT, CSV."
        )

    storage_dir = Path(settings.document_storage_dir).resolve()
    storage_dir.mkdir(parents=True, exist_ok=True)

    storage_key = f"{uuid.uuid4().hex}{extension}"
    final_path = storage_dir / storage_key
    temp_path = storage_dir / f".{uuid.uuid4().hex}.upload-tmp"

    digest = hashlib.sha256()
    total_size = 0

    try:
        with temp_path.open("xb") as target:
            while True:
                chunk = await upload.read(CHUNK_SIZE)
                if not chunk:
                    break

                total_size += len(chunk)
                if total_size > settings.max_upload_size_bytes:
                    raise UploadTooLargeError(
                        "File exceeds the configured upload size limit."
                    )

                digest.update(chunk)
                target.write(chunk)

        if total_size == 0:
            raise DocumentValidationError("Empty files are not accepted.")

        _validate_file_content(temp_path, extension)

        # Generated keys contain no user-controlled path components.
        os.replace(temp_path, final_path)

        return StoredFile(
            original_filename=original_filename,
            storage_key=storage_key,
            extension=extension,
            content_type=_detect_content_type(extension),
            file_size_bytes=total_size,
            checksum_sha256=digest.hexdigest(),
        )
    except Exception:
        temp_path.unlink(missing_ok=True)
        final_path.unlink(missing_ok=True)
        raise
    finally:
        await upload.close()


def resolve_storage_path(
    storage_key: str,
    settings: Settings,
) -> Path:
    """Resolve a generated key and reject path traversal."""
    if (
        not storage_key
        or Path(storage_key).name != storage_key
        or "/" in storage_key
        or "\\" in storage_key
    ):
        raise DocumentValidationError("Invalid storage key.")

    root = Path(settings.document_storage_dir).resolve()
    path = (root / storage_key).resolve()

    if path.parent != root:
        raise DocumentValidationError("Invalid storage key.")

    return path
