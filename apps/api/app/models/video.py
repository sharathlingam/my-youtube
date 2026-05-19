from __future__ import annotations

from datetime import datetime

from sqlalchemy import ARRAY, BigInteger, DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Video(Base):
    __tablename__ = "videos"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    channel_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    channel_name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    thumbnail_url: Mapped[str | None] = mapped_column(String(1024))
    duration_secs: Mapped[int | None] = mapped_column(Integer)
    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), index=True
    )
    category_id: Mapped[str | None] = mapped_column(String(10))
    tags: Mapped[list[str] | None] = mapped_column(ARRAY(String))
    view_count: Mapped[int | None] = mapped_column(BigInteger)
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
