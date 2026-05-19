from __future__ import annotations

import asyncio
import json
import logging
import math
from datetime import datetime, timedelta, timezone

import numpy as np
from sqlalchemy import func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings
from app.models.user import User
from app.models.user_interest import UserInterest
from app.models.user_subscription import UserSubscription
from app.models.video import Video
from app.models.video_embedding import VideoEmbedding
from app.models.watch_event import WatchEvent
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)

FEED_CACHE_TTL = 900  # 15 min — matches beat schedule
FEED_CACHE_SIZE = 60  # pre-rank top 60 videos per user


def _get_session_factory() -> async_sessionmaker[AsyncSession]:
    settings = get_settings()
    engine = create_async_engine(settings.database_url, pool_pre_ping=True)
    return async_sessionmaker(engine, expire_on_commit=False)


def _weight(completion_rate: float, days_ago: float) -> float:
    return completion_rate * math.exp(-days_ago / 30)


def _cosine(a: list[float], b: list[float]) -> float:
    va, vb = np.array(a), np.array(b)
    denom = np.linalg.norm(va) * np.linalg.norm(vb)
    return float(np.dot(va, vb) / denom) if denom > 0 else 0.0


def _freshness(published_at: datetime | None) -> float:
    if not published_at:
        return 0.0
    days = (datetime.now(timezone.utc) - published_at).total_seconds() / 86_400
    return math.exp(-days / 14)


async def _rebuild_taste_for_user(user_id: str, session: AsyncSession) -> list[float] | None:
    cutoff = datetime.now(timezone.utc) - timedelta(days=90)
    events = (
        await session.execute(
            select(WatchEvent)
            .where(WatchEvent.user_id == user_id)
            .where(WatchEvent.created_at >= cutoff)
            .order_by(WatchEvent.created_at.desc())
            .limit(100)
        )
    ).scalars().all()

    if not events:
        return None

    video_ids = [e.video_id for e in events]
    emb_rows = (
        await session.execute(
            select(VideoEmbedding).where(VideoEmbedding.video_id.in_(video_ids))
        )
    ).scalars().all()

    emb_map = {r.video_id: r.get_vector() for r in emb_rows}
    now = datetime.now(timezone.utc)

    weighted_sum = np.zeros(384, dtype=np.float64)
    total_w = 0.0
    for ev in events:
        vec = emb_map.get(ev.video_id)
        if vec is None:
            continue
        days_ago = (now - ev.created_at).total_seconds() / 86_400
        w = _weight(ev.completion_rate, days_ago)
        weighted_sum += np.array(vec) * w
        total_w += w

    if total_w == 0:
        return None

    taste = weighted_sum / total_w
    norm = np.linalg.norm(taste)
    if norm > 0:
        taste = taste / norm

    taste_list = taste.tolist()

    await session.execute(
        update(User)
        .where(User.id == user_id)
        .values(
            taste_embedding=json.dumps(taste_list),
            taste_updated_at=datetime.now(timezone.utc),
        )
    )

    return taste_list


async def _precompute_feed_for_user(
    user_id: str,
    taste_vec: list[float] | None,
    session: AsyncSession,
    redis_client: object,
) -> None:
    channel_ids = (
        await session.execute(
            select(UserSubscription.channel_id).where(UserSubscription.user_id == user_id)
        )
    ).scalars().all()

    if not channel_ids:
        return

    videos = (
        await session.execute(
            select(Video)
            .where(Video.channel_id.in_(channel_ids))
            .where(or_(Video.duration_secs.is_(None), Video.duration_secs > 60))
            .order_by(Video.published_at.desc())
            .limit(200)
        )
    ).scalars().all()

    if not videos:
        return

    interests: dict[str, float] = {
        row.topic.lower(): row.weight
        for row in (
            await session.execute(
                select(UserInterest.topic, UserInterest.weight)
                .where(UserInterest.user_id == user_id)
            )
        ).all()
    }

    aff_rows = (
        await session.execute(
            select(Video.channel_id, func.count(WatchEvent.id).label("cnt"))
            .join(WatchEvent, WatchEvent.video_id == Video.id)
            .where(WatchEvent.user_id == user_id)
            .group_by(Video.channel_id)
        )
    ).all()
    total_w = sum(r.cnt for r in aff_rows) or 1
    channel_affinity = {r.channel_id: r.cnt / total_w for r in aff_rows}

    emb_map: dict[str, list[float]] = {}
    if taste_vec:
        video_ids = [v.id for v in videos]
        emb_rows = (
            await session.execute(
                select(VideoEmbedding).where(VideoEmbedding.video_id.in_(video_ids))
            )
        ).scalars().all()
        emb_map = {e.video_id: e.get_vector() for e in emb_rows}

    has_embeddings = bool(taste_vec and emb_map)
    has_interests = bool(interests)

    def score(v: Video) -> float:
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
            return (
                0.35 * semantic
                + 0.25 * interest_score
                + 0.20 * freshness
                + 0.15 * affinity
            )
        return 0.50 * interest_score + 0.30 * freshness + 0.20 * affinity

    ranked = sorted(videos, key=score, reverse=True)

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

    top = ranked[:FEED_CACHE_SIZE]

    payload = json.dumps([
        {
            "id": v.id,
            "title": v.title,
            "channel_id": v.channel_id,
            "channel_name": v.channel_name,
            "thumbnail_url": v.thumbnail_url,
            "published_at": v.published_at.isoformat() if v.published_at else None,
            "duration_secs": v.duration_secs,
            "view_count": v.view_count,
        }
        for v in top
    ])

    await redis_client.setex(f"feed:precomputed:{user_id}", FEED_CACHE_TTL, payload)  # type: ignore[union-attr]
    logger.debug("precomputed feed for user %s (%d items)", user_id, len(top))


async def _run() -> None:
    import redis.asyncio as aioredis  # noqa: PLC0415

    session_factory = _get_session_factory()
    settings = get_settings()
    redis_client = aioredis.from_url(settings.redis_url, decode_responses=True)
    cutoff = datetime.now(timezone.utc) - timedelta(hours=1)

    try:
        async with session_factory() as session:
            active_ids = (
                await session.execute(
                    select(WatchEvent.user_id)
                    .where(WatchEvent.created_at >= cutoff)
                    .distinct()
                )
            ).scalars().all()

            if not active_ids:
                logger.info("rerank_user_feed: no active users")
                return

            for user_id in active_ids:
                try:
                    taste_vec = await _rebuild_taste_for_user(user_id, session)
                    await _precompute_feed_for_user(user_id, taste_vec, session, redis_client)
                except Exception:
                    logger.exception("Failed taste rebuild/precompute for user %s", user_id)

            await session.commit()
            logger.info("rerank_user_feed: updated %d users", len(active_ids))
    finally:
        await redis_client.aclose()


@celery_app.task(name="app.workers.tasks.rerank_user_feed.rerank_user_feed")
def rerank_user_feed() -> None:
    asyncio.run(_run())
