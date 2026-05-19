from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timezone

from celery.signals import worker_ready
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings
from app.models.video import Video
from app.models.video_embedding import VideoEmbedding
from app.models.video_tag import VideoTag
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)

_model = None  # loaded once at worker startup
_kw_model = None

BATCH_SIZE = 32
MODEL_NAME = "all-MiniLM-L6-v2"


@worker_ready.connect
def load_models(**kwargs: object) -> None:
    global _model, _kw_model
    try:
        from sentence_transformers import SentenceTransformer  # noqa: PLC0415
        _model = SentenceTransformer(MODEL_NAME)
        logger.info("Loaded SentenceTransformer: %s", MODEL_NAME)
    except Exception:
        logger.exception("Failed to load SentenceTransformer")

    try:
        from keybert import KeyBERT  # noqa: PLC0415
        _kw_model = KeyBERT(model=MODEL_NAME)
        logger.info("Loaded KeyBERT")
    except Exception:
        logger.exception("Failed to load KeyBERT")


def _build_input(video: Video) -> str:
    parts = [video.title]
    if video.description:
        parts.append(video.description[:400])
    tags = video.tags or []
    if tags:
        parts.append("Topics: " + ", ".join(tags[:10]))
    return ". ".join(parts)


def _get_session_factory() -> async_sessionmaker[AsyncSession]:
    settings = get_settings()
    engine = create_async_engine(settings.database_url, pool_pre_ping=True)
    return async_sessionmaker(engine, expire_on_commit=False)


async def _run() -> None:
    if _model is None:
        logger.warning("embed_new_videos: model not loaded, skipping")
        return

    session_factory = _get_session_factory()
    async with session_factory() as session:
        # Find videos without embeddings
        rows = (
            await session.execute(
                select(Video)
                .outerjoin(VideoEmbedding, VideoEmbedding.video_id == Video.id)
                .where(VideoEmbedding.video_id.is_(None))
                .limit(200)
            )
        ).scalars().all()

        if not rows:
            logger.info("embed_new_videos: no new videos to embed")
            return

        logger.info("embed_new_videos: embedding %d videos", len(rows))

        for i in range(0, len(rows), BATCH_SIZE):
            batch = rows[i : i + BATCH_SIZE]
            texts = [_build_input(v) for v in batch]

            try:
                vectors = _model.encode(texts, normalize_embeddings=True).tolist()
            except Exception:
                logger.exception("Encoding failed for batch %d", i)
                continue

            for video, vector in zip(batch, vectors):
                await session.execute(
                    insert(VideoEmbedding)
                    .values(
                        video_id=video.id,
                        embedding=json.dumps(vector),
                        model_ver=MODEL_NAME,
                        embedded_at=datetime.now(timezone.utc),
                    )
                    .on_conflict_do_nothing()
                )

                # KeyBERT keyphrases → video_tags
                if _kw_model is not None:
                    text = _build_input(video)
                    try:
                        kws = _kw_model.extract_keywords(
                            text, keyphrase_ngram_range=(1, 2), top_n=8, stop_words="english"
                        )
                        for phrase, _ in kws:
                            if phrase:
                                await session.execute(
                                    insert(VideoTag)
                                    .values(
                                        video_id=video.id,
                                        tag=phrase.lower()[:200],
                                        source="keyphrase",
                                    )
                                    .on_conflict_do_nothing()
                                )
                    except Exception:
                        logger.warning("KeyBERT failed for video %s", video.id)

        await session.commit()
        logger.info("embed_new_videos: done, committed %d videos", len(rows))


@celery_app.task(name="app.workers.tasks.embed_new_videos.embed_new_videos")
def embed_new_videos() -> None:
    asyncio.run(_run())
