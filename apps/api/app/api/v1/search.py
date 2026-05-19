from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.core.dependencies import get_db
from app.models.user import User
from app.models.user_subscription import UserSubscription
from app.models.video import Video

router = APIRouter()


class VideoResult(BaseModel):
    id: str
    title: str
    channel_id: str
    channel_name: str
    thumbnail_url: str | None
    published_at: str | None
    duration_secs: int | None
    view_count: int | None

    model_config = {"from_attributes": True}


class SearchResponse(BaseModel):
    items: list[VideoResult]
    query: str


@router.get("/api/v1/search", response_model=SearchResponse)
async def search_videos(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    q: str = Query(default="", min_length=0, max_length=200),
    limit: int = Query(default=20, ge=1, le=100),
) -> SearchResponse:
    if not q.strip():
        return SearchResponse(items=[], query=q)

    subscribed_channel_ids = (
        await db.execute(
            select(UserSubscription.channel_id).where(
                UserSubscription.user_id == current_user.id
            )
        )
    ).scalars().all()

    if not subscribed_channel_ids:
        return SearchResponse(items=[], query=q)

    term = f"%{q.strip()}%"
    rows = (
        await db.execute(
            select(Video)
            .where(Video.channel_id.in_(subscribed_channel_ids))
            .where(
                or_(
                    Video.title.ilike(term),
                    Video.channel_name.ilike(term),
                )
            )
            .order_by(Video.published_at.desc())
            .limit(limit)
        )
    ).scalars().all()

    return SearchResponse(
        items=[
            VideoResult(
                id=v.id,
                title=v.title,
                channel_id=v.channel_id,
                channel_name=v.channel_name,
                thumbnail_url=v.thumbnail_url,
                published_at=v.published_at.isoformat() if v.published_at else None,
                duration_secs=v.duration_secs,
                view_count=v.view_count,
            )
            for v in rows
        ],
        query=q,
    )
