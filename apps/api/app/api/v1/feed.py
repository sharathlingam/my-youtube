from __future__ import annotations

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.core.dependencies import get_db
from app.models.user import User
from app.models.user_subscription import UserSubscription
from app.models.video import Video

router = APIRouter()


class VideoOut(BaseModel):
    id: str
    title: str
    channel_id: str
    channel_name: str
    thumbnail_url: str | None
    published_at: str | None
    duration_secs: int | None
    view_count: int | None

    model_config = {"from_attributes": True}


class FeedResponse(BaseModel):
    items: list[VideoOut]
    next_cursor: str | None


@router.get("/api/v1/feed", response_model=FeedResponse)
async def get_feed(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    limit: int = Query(default=20, ge=1, le=100),
    cursor: str | None = Query(default=None),
) -> FeedResponse:
    subscribed_channel_ids = (
        await db.execute(
            select(UserSubscription.channel_id).where(
                UserSubscription.user_id == current_user.id
            )
        )
    ).scalars().all()

    query = (
        select(Video)
        .where(Video.channel_id.in_(subscribed_channel_ids))
        .order_by(Video.published_at.desc())
        .limit(limit + 1)
    )

    if cursor:
        cursor_dt = datetime.fromisoformat(cursor.replace("Z", "+00:00"))
        query = query.where(Video.published_at < cursor_dt)

    videos = (await db.execute(query)).scalars().all()

    has_more = len(videos) > limit
    items = videos[:limit]

    next_cursor = None
    if has_more and items:
        last = items[-1]
        next_cursor = last.published_at.isoformat() if last.published_at else None

    return FeedResponse(
        items=[
            VideoOut(
                id=v.id,
                title=v.title,
                channel_id=v.channel_id,
                channel_name=v.channel_name,
                thumbnail_url=v.thumbnail_url,
                published_at=v.published_at.isoformat() if v.published_at else None,
                duration_secs=v.duration_secs,
                view_count=v.view_count,
            )
            for v in items
        ],
        next_cursor=next_cursor,
    )
