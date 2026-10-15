from __future__ import annotations

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class ReviewComment(TimestampMixin, Base):
    __tablename__ = "review_comments"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    review_id: Mapped[int] = mapped_column(
        ForeignKey("human_reviews.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    author: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    comment_type: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
        default="comment",
    )

    body: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )