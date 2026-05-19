from __future__ import annotations

import json
from datetime import datetime, timezone

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class VideoEmbedding(Base):
    __tablename__ = "video_embeddings"

    video_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("videos.id", ondelete="CASCADE"), primary_key=True
    )
    embedding: Mapped[str] = mapped_column(Text, nullable=False)
    model_ver: Mapped[str] = mapped_column(String(100), default="all-MiniLM-L6-v2")
    embedded_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc)
    )

    def get_vector(self) -> list[float]:
        return json.loads(self.embedding)

    @staticmethod
    def encode_vector(v: list[float]) -> str:
        return json.dumps(v)
