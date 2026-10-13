
from pathlib import Path

from pypdf import PdfReader
from pypdf.errors import PdfReadError

from app.models.document import Document
from app.services.document_storage import (
    DocumentValidationError,
    resolve_storage_path,
)


MAX_PDF_PAGES = 100
MAX_EXTRACTED_CHARACTERS = 1_000_000


class TextExtractionError(Exception):
    """The document could not be converted into usable text."""


def extract_document_text(document: Document, settings) -> str:
    """Read text from a stored document using its Phase 2 metadata."""
    path: Path = resolve_storage_path(document.storage_key, settings)

    if not path.is_file():
        raise TextExtractionError("Stored document content is missing.")

    try:
        if document.extension == ".txt":
            text = path.read_text(encoding="utf-8-sig")

        elif document.extension == ".csv":
            text = path.read_text(encoding="utf-8-sig")

        elif document.extension == ".pdf":
            reader = PdfReader(str(path), strict=True)

            if reader.is_encrypted:
                raise TextExtractionError(
                    "Encrypted PDFs are not supported in this phase."
                )

            if len(reader.pages) > MAX_PDF_PAGES:
                raise TextExtractionError(
                    f"PDF exceeds the {MAX_PDF_PAGES}-page limit."
                )

            page_texts: list[str] = []

            for page_number, page in enumerate(reader.pages, start=1):
                try:
                    page_text = page.extract_text() or ""
                except Exception as exc:
                    raise TextExtractionError(
                        f"Could not extract text from PDF page {page_number}."
                    ) from exc

                page_texts.append(page_text)

                if sum(map(len, page_texts)) > MAX_EXTRACTED_CHARACTERS:
                    raise TextExtractionError(
                        "Extracted document text exceeds the size limit."
                    )

            text = "\n".join(page_texts)

        else:
            raise TextExtractionError(
                "Unsupported document type for text extraction."
            )

    except TextExtractionError:
        raise
    except (OSError, UnicodeDecodeError, PdfReadError, ValueError) as exc:
        raise TextExtractionError(
            "The document could not be read as valid text."
        ) from exc

    if len(text) > MAX_EXTRACTED_CHARACTERS:
        raise TextExtractionError(
            "Extracted document text exceeds the size limit."
        )

    if not text.strip():
        raise TextExtractionError(
            "No extractable text was found. The PDF may be scanned "
            "or contain only images."
        )

    return text
