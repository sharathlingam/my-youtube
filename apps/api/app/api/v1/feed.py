from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from typing import Annotated

import numpy as np
from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel
from sqlalchemy import func, or_, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.core.dependencies import get_db
from app.models.user import User
from app.models.user_interest import UserInterest
from app.models.user_subscription import UserSubscription
from app.models.video import Video
from app.models.video_embedding import VideoEmbedding
from app.models.watch_event import WatchEvent

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


def _freshness(published_at: datetime | None) -> float:
    if not published_at:
        return 0.0
    days = (datetime.now(timezone.utc) - published_at).total_seconds() / 86_400
    return math.exp(-days / 14)


def _cosine(a: list[float], b: list[float]) -> float:
    va, vb = np.array(a), np.array(b)
    denom = np.linalg.norm(va) * np.linalg.norm(vb)
    if denom == 0:
        return 0.0
    return float(np.dot(va, vb) / denom)


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

    if not subscribed_channel_ids:
        return FeedResponse(items=[], next_cursor=None)

    candidate_limit = min(limit * 5, 300)
    base_query = (
        select(Video)
        .where(Video.channel_id.in_(subscribed_channel_ids))
        .where(or_(Video.duration_secs.is_(None), Video.duration_secs > 60))
        .order_by(Video.published_at.desc())
        .limit(candidate_limit)
    )
    if cursor:
        cursor_dt = datetime.fromisoformat(cursor.replace("Z", "+00:00"))
        base_query = base_query.where(Video.published_at < cursor_dt)

    videos = (await db.execute(base_query)).scalars().all()
    if not videos:
        return FeedResponse(items=[], next_cursor=None)

    video_ids = [v.id for v in videos]

    # User interests
    interests: dict[str, float] = {
        row.topic.lower(): row.weight
        for row in (
            await db.execute(
                select(UserInterest.topic, UserInterest.weight).where(
                    UserInterest.user_id == current_user.id
                )
            )
        ).all()
    }

    # Channel affinity
    channel_affinity: dict[str, float] = {}
    aff_rows = (
        await db.execute(
            select(Video.channel_id, func.count(WatchEvent.id).label("cnt"))
            .join(WatchEvent, WatchEvent.video_id == Video.id)
            .where(WatchEvent.user_id == current_user.id)
            .group_by(Video.channel_id)
        )
    ).all()
    total_w = sum(r.cnt for r in aff_rows) or 1
    for r in aff_rows:
        channel_affinity[r.channel_id] = r.cnt / total_w

    # User taste vector
    taste_vec: list[float] | None = None
    if current_user.taste_embedding:
        try:
            taste_vec = json.loads(current_user.taste_embedding)
        except Exception:
            taste_vec = None

    # Video embeddings map
    emb_map: dict[str, list[float]] = {}
    if taste_vec:
        emb_rows = (
            await db.execute(
                select(VideoEmbedding).where(VideoEmbedding.video_id.in_(video_ids))
            )
        ).scalars().all()
        for e in emb_rows:
            emb_map[e.video_id] = e.get_vector()

    has_embeddings = bool(taste_vec and emb_map)
    has_interests = bool(interests)

    def score(v: Video) -> float:
        # Interest tag score (Phase 3 signal)
        tags = [t.lower() for t in (v.tags or [])]
        if tags and has_interests:
            matched = [interests[t] for t in tags if t in interests]
            interest_score = sum(matched) / len(tags) if matched else 0.0
        else:
            interest_score = 0.0

        freshness = _freshness(v.published_at)
        affinity = channel_affinity.get(v.channel_id, 0.0)

        if has_embeddings:
            vec = emb_map.get(v.id)
            semantic = _cosine(taste_vec, vec) if vec else 0.0  # type: ignore[arg-type]
            # Phase 4 formula
            diversity_bonus = 0.0  # post-processing handled below
            return (
                0.35 * semantic
                + 0.25 * interest_score
                + 0.20 * freshness
                + 0.15 * affinity
                + 0.05 * diversity_bonus
            )

        # Phase 3 fallback
        return 0.50 * interest_score + 0.30 * freshness + 0.20 * affinity

    ranked = sorted(videos, key=score, reverse=True)

    # Diversity post-processing: boost first video per unseen primary tag
    if has_embeddings:
        seen_tags: set[str] = set()
        diversified: list[Video] = []
        deferred: list[Video] = []

        for v in ranked:
            primary = (v.tags or [None])[0]
            if primary and primary.lower() not in seen_tags:
                seen_tags.add(primary.lower())
                diversified.append(v)
            else:
                deferred.append(v)

        ranked = diversified + deferred

    page = ranked[:limit]
    has_more = len(ranked) > limit

    next_cursor = None
    if has_more and page:
        oldest = min(
            page,
            key=lambda v: v.published_at or datetime.min.replace(tzinfo=timezone.utc),
        )
        if oldest.published_at:
            next_cursor = oldest.published_at.isoformat()

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
            for v in page
        ],
        next_cursor=next_cursor,
    )
