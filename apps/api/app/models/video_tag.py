from __future__ import annotations

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class VideoTag(Base):
    __tablename__ = "video_tags"

    video_id: Mapped[str] = mapped_column(String(50), ForeignKey("videos.id", ondelete="CASCADE"), primary_key=True)
    tag: Mapped[str] = mapped_column(String(200), primary_key=True)
    source: Mapped[str] = mapped_column(String(50), nullable=False, default="api")
