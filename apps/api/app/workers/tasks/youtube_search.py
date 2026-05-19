from __future__ import annotations

import asyncio
import logging

import redis.asyncio as aioredis
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings
from app.models.video import Video
from app.services.youtube.client import YouTubeClient
from app.services.youtube.quota import QuotaBudgetExhausted
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


def _get_session_factory() -> async_sessionmaker[AsyncSession]:
    settings = get_settings()
    engine = create_async_engine(settings.database_url, pool_pre_ping=True)
    return async_sessionmaker(engine, expire_on_commit=False)


async def _run(query: str) -> None:
    settings = get_settings()
    redis_client = aioredis.from_url(settings.redis_url, decode_responses=True)
    yt = YouTubeClient(redis_client)

    try:
        try:
            video_ids = await yt.search_videos(query)
        except QuotaBudgetExhausted:
            logger.warning("youtube_search: quota exhausted for query=%r", query)
            return
        except Exception:
            logger.exception("youtube_search: search.list failed for query=%r", query)
            return

        if not video_ids:
            logger.info("youtube_search: no results for query=%r", query)
            return

        session_factory = _get_session_factory()
        async with session_factory() as session:
            existing = set(
                (await session.execute(select(Video.id).where(Video.id.in_(video_ids)))).scalars()
            )
            new_ids = [v for v in video_ids if v not in existing]

            if new_ids:
                try:
                    videos = await yt.get_videos(new_ids)
                    for v in videos:
                        await session.execute(
                            insert(Video)
                            .values(**v)
                            .on_conflict_do_update(
                                index_elements=["id"],
                                set_={k: val for k, val in v.items() if k != "id"},
                            )
                        )
                    await session.commit()
                    logger.info("youtube_search: stored %d new videos for query=%r", len(videos), query)
                except Exception:
                    logger.exception("youtube_search: failed to store videos for query=%r", query)
            else:
                logger.info("youtube_search: all %d videos already in DB for query=%r", len(video_ids), query)
    finally:
        await yt.aclose()
        await redis_client.aclose()


@celery_app.task(name="app.workers.tasks.youtube_search.youtube_search")
def youtube_search(query: str) -> None:
    asyncio.run(_run(query))
