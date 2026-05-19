from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class WatchEvent(Base):
    __tablename__ = "watch_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    video_id: Mapped[str] = mapped_column(String(50), ForeignKey("videos.id", ondelete="CASCADE"), nullable=False, index=True)
    watch_duration_secs: Mapped[int] = mapped_column(nullable=False, default=0)
    completion_rate: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    session_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))
