from __future__ import annotations

import asyncio
import logging

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings
from app.models.user_interest import UserInterest
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)

_DECAY_FACTOR = 0.97


def _get_session_factory() -> async_sessionmaker[AsyncSession]:
    settings = get_settings()
    engine = create_async_engine(settings.database_url, pool_pre_ping=True)
    return async_sessionmaker(engine, expire_on_commit=False)


async def _run() -> None:
    session_factory = _get_session_factory()
    async with session_factory() as session:
        result = await session.execute(
            update(UserInterest)
            .values(weight=UserInterest.weight * _DECAY_FACTOR)
            .returning(UserInterest.user_id)
        )
        count = len(result.fetchall())
        await session.commit()
        logger.info("decay_interest_weights: decayed %d rows by %.2f", count, _DECAY_FACTOR)


@celery_app.task(name="app.workers.tasks.decay_interest_weights.decay_interest_weights")
def decay_interest_weights() -> None:
    asyncio.run(_run())
