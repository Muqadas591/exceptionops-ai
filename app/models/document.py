
from sqlalchemy import BigInteger, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class Document(TimestampMixin, Base):
    __tablename__ = "documents"
    __table_args__ = (
        UniqueConstraint(
            "checksum_sha256",
            name="uq_document_checksum_sha256",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    # Display metadata only; never use this as a filesystem path.
    original_filename: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    # Generated storage name, such as a UUID ending in .pdf.
    storage_key: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
    )

    extension: Mapped[str] = mapped_column(String(10), nullable=False)
    content_type: Mapped[str] = mapped_column(String(100), nullable=False)

    file_size_bytes: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
    )

    checksum_sha256: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        default="received",
        nullable=False,
        index=True,
    )
