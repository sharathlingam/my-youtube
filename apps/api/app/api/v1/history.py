from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.core.dependencies import get_db
from app.models.user import User
from app.models.video import Video
from app.models.watch_event import WatchEvent

router = APIRouter()


class WatchEventIn(BaseModel):
    video_id: str
    watch_duration_secs: int = Field(ge=0)
    completion_rate: float = Field(ge=0.0, le=1.0)
    session_id: str | None = None


class WatchEventOut(BaseModel):
    id: str
    video_id: str


class HistoryItem(BaseModel):
    event_id: str
    video_id: str
    title: str
    channel_name: str
    thumbnail_url: str | None
    duration_secs: int | None
    completion_rate: float
    watched_at: str

    model_config = {"from_attributes": True}


class HistoryResponse(BaseModel):
    items: list[HistoryItem]


@router.post("/api/v1/history", response_model=WatchEventOut, status_code=201)
async def record_watch_event(
    request: Request,
    body: WatchEventIn,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> WatchEventOut:
    event = WatchEvent(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        video_id=body.video_id,
        watch_duration_secs=body.watch_duration_secs,
        completion_rate=body.completion_rate,
        session_id=body.session_id,
    )
    db.add(event)
    await db.commit()
    return WatchEventOut(id=event.id, video_id=event.video_id)


@router.get("/api/v1/history", response_model=HistoryResponse)
async def get_history(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    limit: int = Query(default=50, ge=1, le=200),
) -> HistoryResponse:
    rows = (
        await db.execute(
            select(WatchEvent, Video)
            .join(Video, Video.id == WatchEvent.video_id)
            .where(WatchEvent.user_id == current_user.id)
            .where(or_(Video.duration_secs.is_(None), Video.duration_secs > 60))
            .order_by(WatchEvent.created_at.desc())
            .limit(limit)
        )
    ).all()

    items = [
        HistoryItem(
            event_id=ev.id,
            video_id=ev.video_id,
            title=vid.title,
            channel_name=vid.channel_name,
            thumbnail_url=vid.thumbnail_url,
            duration_secs=vid.duration_secs,
            completion_rate=ev.completion_rate,
            watched_at=ev.created_at.isoformat(),
        )
        for ev, vid in rows
    ]
    return HistoryResponse(items=items)
