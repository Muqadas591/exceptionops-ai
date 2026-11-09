
import pytest

from app.core.config import get_settings

from app.services.document_storage import (
    DocumentValidationError,
    resolve_storage_path,
    sanitize_display_filename,
)


@pytest.mark.parametrize(
    ("filename", "expected"),
    [
        ("invoice.txt", "invoice.txt"),
        ("../../etc/passwd", "passwd"),
        (r"..\..\secret.txt", "secret.txt"),
        ("folder/invoice.csv", "invoice.csv"),
        ("", "upload"),
        ("..", "upload"),
        ("invoice\x00.txt", "invoice.txt"),
    ],
)
def test_filename_sanitization(
    filename,
    expected,
):
    assert sanitize_display_filename(filename) == expected


@pytest.mark.parametrize(
    "storage_key",
    [
        "../secret.txt",
        "../../etc/passwd",
        r"..\secret.txt",
        "/etc/passwd",
        "",
        "folder/document.txt",
    ],
)

def test_storage_path_rejects_user_controlled_keys(storage_key):
    with pytest.raises(DocumentValidationError):
        resolve_storage_path(storage_key, get_settings())


def test_upload_path_is_not_user_controlled(
    client,
    document_storage,
):
    response = client.post(
        "/api/v1/documents",
        files={
            "file": (
                "../../malicious.txt",
                b"Synthetic invoice content",
                "text/plain",
            )
        },
    )

    assert response.status_code == 201

    body = response.json()

    assert body["original_filename"] == "malicious.txt"

    stored_files = list(document_storage.iterdir())

    assert len(stored_files) == 1

    assert stored_files[0].name != "malicious.txt"
    assert stored_files[0].name.endswith(".txt")
    assert "storage_key" not in body
