from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class UserSubscription(Base):
    __tablename__ = "user_subscriptions"

    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    channel_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("channels.id", ondelete="CASCADE"), primary_key=True
    )
    subscribed_since: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
