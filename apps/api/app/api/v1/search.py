from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.core.dependencies import get_db, get_redis
from app.models.user import User
from app.models.video import Video
from app.services.youtube.client import YouTubeClient
from app.services.youtube.quota import QuotaBudgetExhausted

router = APIRouter()
logger = logging.getLogger(__name__)


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
    has_more: bool = False
    source: str = "youtube"  # "youtube" | "cache" | "db_fallback"


@router.get("/api/v1/search", response_model=SearchResponse)
async def search_videos(
    db: Annotated[AsyncSession, Depends(get_db)],
    redis: Annotated[object, Depends(get_redis)],
    current_user: Annotated[User, Depends(get_current_user)],
    q: str = Query(default="", min_length=0, max_length=200),
    limit: int = Query(default=20, ge=1, le=50),
    offset: int = Query(default=0, ge=0),
) -> SearchResponse:
    if not q.strip():
        return SearchResponse(items=[], query=q)

    query = q.strip()
    yt = YouTubeClient(redis)  # type: ignore[arg-type]

    # Fetch video IDs from YouTube (cached 6h — no extra quota cost on repeat searches)
    try:
        all_ids = await yt.search_videos(query, max_results=50)
        source = "youtube"
    except QuotaBudgetExhausted:
        logger.warning("search: quota exhausted, falling back to DB for query=%r", query)
        all_ids = []
        source = "db_fallback"
    except Exception:
        logger.exception("search: YouTube search.list failed for query=%r", query)
        all_ids = []
        source = "db_fallback"
    finally:
        await yt.aclose()

    if not all_ids:
        # Quota exhausted or error — fall back to local DB full-text search
        from sqlalchemy import or_  # noqa: PLC0415
        term = f"%{query}%"
        rows = (
            await db.execute(
                select(Video)
                .where(or_(Video.title.ilike(term), Video.channel_name.ilike(term)))
                .where(or_(Video.duration_secs.is_(None), Video.duration_secs > 60))
                .order_by(Video.published_at.desc())
                .offset(offset)
                .limit(limit + 1)
            )
        ).scalars().all()
        has_more = len(rows) > limit
        rows = rows[:limit]
        return SearchResponse(
            items=_to_out(rows),
            query=query,
            has_more=has_more,
            source=source,
        )

    # Paginate from cached ID list
    page_ids = all_ids[offset : offset + limit]
    has_more = offset + limit < len(all_ids)

    if not page_ids:
        return SearchResponse(items=[], query=query, has_more=False, source=source)

    # Fetch+cache video details (videos.list, cost=1 per 50, cached 24h)
    yt2 = YouTubeClient(redis)  # type: ignore[arg-type]
    try:
        video_details = await yt2.get_videos(page_ids)
    except Exception:
        logger.exception("search: get_videos failed for query=%r", query)
        video_details = []
    finally:
        await yt2.aclose()

    # Upsert into DB so videos appear in feed/history
    for v in video_details:
        try:
            await db.execute(
                insert(Video)
                .values(**v)
                .on_conflict_do_update(
                    index_elements=["id"],
                    set_={k: val for k, val in v.items() if k != "id"},
                )
            )
        except Exception:
            logger.warning("search: upsert failed for video %s", v.get("id"))

    # Build ordered response matching YouTube's ranking, excluding Shorts
    detail_map = {
        v["id"]: v for v in video_details
        if v.get("duration_secs") is None or v["duration_secs"] > 60
    }
    ordered = [detail_map[vid_id] for vid_id in page_ids if vid_id in detail_map]

    return SearchResponse(
        items=[
            VideoResult(
                id=v["id"],
                title=v["title"],
                channel_id=v["channel_id"],
                channel_name=v["channel_name"],
                thumbnail_url=v.get("thumbnail_url"),
                published_at=v["published_at"].isoformat() if v.get("published_at") else None,
                duration_secs=v.get("duration_secs"),
                view_count=v.get("view_count"),
            )
            for v in ordered
        ],
        query=query,
        has_more=has_more,
        source=source,
    )


def _to_out(rows: list[Video]) -> list[VideoResult]:
    return [
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
    ]
