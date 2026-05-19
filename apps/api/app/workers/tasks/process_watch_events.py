from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings
from app.models.user_interest import UserInterest
from app.models.video import Video
from app.models.watch_event import WatchEvent
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


def _weight_delta(completion_rate: float) -> float:
    if completion_rate > 0.80:
        return 0.15
    if completion_rate > 0.40:
        return 0.05
    if completion_rate > 0.10:
        return 0.0
    return -0.10


def _get_session_factory() -> async_sessionmaker[AsyncSession]:
    settings = get_settings()
    engine = create_async_engine(settings.database_url, pool_pre_ping=True)
    return async_sessionmaker(engine, expire_on_commit=False)


async def _run() -> None:
    session_factory = _get_session_factory()
    since = datetime.now(timezone.utc) - timedelta(minutes=10)

    async with session_factory() as session:
        rows = (
            await session.execute(
                select(WatchEvent, Video)
                .join(Video, Video.id == WatchEvent.video_id)
                .where(WatchEvent.created_at >= since)
            )
        ).all()

        if not rows:
            return

        # Deduplicate: per (user_id, video_id) keep highest completion_rate
        best: dict[tuple[str, str], tuple[float, list[str]]] = {}
        for ev, vid in rows:
            key = (ev.user_id, ev.video_id)
            tags: list[str] = vid.tags or []
            if vid.channel_id:
                tags = [*tags, f"channel:{vid.channel_id}"]
            current_rate = best.get(key, (0.0, []))[0]
            if ev.completion_rate >= current_rate:
                best[key] = (ev.completion_rate, tags)

        for (user_id, _), (completion_rate, tags) in best.items():
            delta = _weight_delta(completion_rate)
            if delta == 0.0:
                continue
            for tag in tags:
                if not tag:
                    continue
                tag_lower = tag.lower()[:200]
                # Upsert interest: insert at 0 or update existing
                await session.execute(
                    insert(UserInterest)
                    .values(
                        user_id=user_id,
                        topic=tag_lower,
                        weight=max(0.0, min(1.0, delta)),
                        updated_at=datetime.now(timezone.utc),
                    )
                    .on_conflict_do_update(
                        index_elements=["user_id", "topic"],
                        set_={
                            "weight": UserInterest.weight + delta,
                            "updated_at": datetime.now(timezone.utc),
                        },
                    )
                )

        # Clamp weights to [0, 1]
        await session.execute(
            update(UserInterest)
            .where(UserInterest.weight > 1.0)
            .values(weight=1.0)
        )
        await session.execute(
            update(UserInterest)
            .where(UserInterest.weight < 0.0)
            .values(weight=0.0)
        )

        await session.commit()
        logger.info("process_watch_events: processed %d (user, video) pairs", len(best))


@celery_app.task(name="app.workers.tasks.process_watch_events.process_watch_events")
def process_watch_events() -> None:
    asyncio.run(_run())
