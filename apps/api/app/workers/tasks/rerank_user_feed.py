from __future__ import annotations

import asyncio
import json
import logging
import math
from datetime import datetime, timedelta, timezone

import numpy as np
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings
from app.models.user import User
from app.models.video_embedding import VideoEmbedding
from app.models.watch_event import WatchEvent
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


def _get_session_factory() -> async_sessionmaker[AsyncSession]:
    settings = get_settings()
    engine = create_async_engine(settings.database_url, pool_pre_ping=True)
    return async_sessionmaker(engine, expire_on_commit=False)


def _weight(completion_rate: float, days_ago: float) -> float:
    return completion_rate * math.exp(-days_ago / 30)


async def _rebuild_taste_for_user(user_id: str, session: AsyncSession) -> None:
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
        return

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
        return

    taste = weighted_sum / total_w
    norm = np.linalg.norm(taste)
    if norm > 0:
        taste = taste / norm

    await session.execute(
        update(User)
        .where(User.id == user_id)
        .values(
            taste_embedding=json.dumps(taste.tolist()),
            taste_updated_at=datetime.now(timezone.utc),
        )
    )


async def _run() -> None:
    session_factory = _get_session_factory()
    cutoff = datetime.now(timezone.utc) - timedelta(hours=1)

    async with session_factory() as session:
        # Active users: watched something in last hour
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
                await _rebuild_taste_for_user(user_id, session)
            except Exception:
                logger.exception("Failed taste rebuild for user %s", user_id)

        await session.commit()
        logger.info("rerank_user_feed: updated taste for %d users", len(active_ids))


@celery_app.task(name="app.workers.tasks.rerank_user_feed.rerank_user_feed")
def rerank_user_feed() -> None:
    asyncio.run(_run())
