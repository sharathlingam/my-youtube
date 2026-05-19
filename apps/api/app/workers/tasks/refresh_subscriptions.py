from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings
from app.models.channel import Channel
from app.models.user import User
from app.models.user_subscription import UserSubscription
from app.models.video import Video
from app.services.youtube.client import YouTubeClient
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


def _get_session_factory() -> async_sessionmaker[AsyncSession]:
    settings = get_settings()
    engine = create_async_engine(settings.database_url, pool_pre_ping=True)
    return async_sessionmaker(engine, expire_on_commit=False)


async def _refresh_user(
    user: User,
    session: AsyncSession,
    yt: YouTubeClient,
) -> None:
    if not user.google_id:
        return

    # Need access token — stored in sessions table
    from app.models.session import Session  # noqa: PLC0415

    result = await session.execute(
        select(Session)
        .where(Session.user_id == user.id)
        .order_by(Session.created_at.desc())
        .limit(1)
    )
    db_session = result.scalar_one_or_none()
    if not db_session or not db_session.access_token:
        logger.warning("No access token for user %s", user.id)
        return

    try:
        subs = await yt.get_subscriptions(db_session.access_token, user.id)
    except Exception:
        logger.exception("Failed to fetch subscriptions for user %s", user.id)
        return

    channel_ids = [s["channel_id"] for s in subs if s["channel_id"]]
    if not channel_ids:
        return

    # Upsert channels
    try:
        channel_details = await yt.get_channels(channel_ids)
        for ch in channel_details:
            await session.execute(
                insert(Channel)
                .values(**ch)
                .on_conflict_do_update(
                    index_elements=["id"],
                    set_={k: v for k, v in ch.items() if k != "id"},
                )
            )
    except Exception:
        logger.exception("Failed to fetch channel details")

    # Upsert subscriptions
    for sub in subs:
        if not sub["channel_id"]:
            continue
        raw_since = sub.get("subscribed_since")
        if isinstance(raw_since, str):
            raw_since = datetime.fromisoformat(raw_since.replace("Z", "+00:00"))
        await session.execute(
            insert(UserSubscription)
            .values(
                user_id=user.id,
                channel_id=sub["channel_id"],
                subscribed_since=raw_since,
            )
            .on_conflict_do_nothing()
        )

    # Fetch recent videos from each channel's uploads playlist
    video_ids: list[str] = []
    for channel_id in channel_ids[:20]:  # cap at 20 channels per run
        uploads_playlist = "UU" + channel_id[2:]  # UC... → UU...
        try:
            async for vid_id in yt.iter_playlist_videos(uploads_playlist, max_pages=2):
                video_ids.append(vid_id)
        except Exception:
            logger.warning("Failed playlist fetch for channel %s", channel_id)
            continue

    if not video_ids:
        await session.commit()
        return

    # Filter already-fetched videos
    existing = set(
        (
            await session.execute(
                select(Video.id).where(Video.id.in_(video_ids))
            )
        ).scalars()
    )
    new_ids = [v for v in video_ids if v not in existing]

    if new_ids:
        try:
            videos = await yt.get_videos(new_ids)
            for v in videos:
                # Skip Shorts (≤60s)
                dur = v.get("duration_secs")
                if dur is not None and dur <= 60:
                    continue
                await session.execute(
                    insert(Video)
                    .values(**v)
                    .on_conflict_do_update(
                        index_elements=["id"],
                        set_={k: val for k, val in v.items() if k != "id"},
                    )
                )
        except Exception:
            logger.exception("Failed to fetch video details")

    await session.commit()


async def _run() -> None:
    session_factory = _get_session_factory()
    import redis.asyncio as aioredis  # noqa: PLC0415

    settings = get_settings()
    redis_client = aioredis.from_url(settings.redis_url, decode_responses=True)
    yt = YouTubeClient(redis_client)

    try:
        async with session_factory() as session:
            result = await session.execute(
                select(User).where(User.is_active == True)  # noqa: E712
            )
            users = result.scalars().all()
            for user in users:
                await _refresh_user(user, session, yt)
    finally:
        await yt.aclose()
        await redis_client.aclose()


@celery_app.task(name="app.workers.tasks.refresh_subscriptions.refresh_all_subscriptions")
def refresh_all_subscriptions() -> None:
    asyncio.run(_run())
