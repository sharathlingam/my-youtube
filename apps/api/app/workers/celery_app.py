import ssl

from celery import Celery
from celery.schedules import crontab

from app.core.config import get_settings

settings = get_settings()

_is_tls = settings.redis_url.startswith("rediss://")
_ssl_opts = {"ssl_cert_reqs": ssl.CERT_NONE} if _is_tls else {}

celery_app = Celery(
    "yt_pwa",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=[
        "app.workers.tasks.refresh_subscriptions",
        "app.workers.tasks.process_watch_events",
        "app.workers.tasks.decay_interest_weights",
        "app.workers.tasks.youtube_search",
        # embed_new_videos + rerank_user_feed excluded: require sentence-transformers
        # (~500MB RAM), incompatible with free-tier 512MB constraint.
        # Feed falls back to Phase 3 tag-based ranking.
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    broker_connection_retry_on_startup=True,
    broker_use_ssl=_ssl_opts or None,
    redis_backend_use_ssl=_ssl_opts or None,
)

celery_app.conf.beat_schedule = {
    "refresh-subscriptions-every-2h": {
        "task": "app.workers.tasks.refresh_subscriptions.refresh_all_subscriptions",
        "schedule": crontab(minute=0, hour="*/2"),
    },
    "process-watch-events-every-5m": {
        "task": "app.workers.tasks.process_watch_events.process_watch_events",
        "schedule": crontab(minute="*/5"),
    },
    "decay-interest-weights-daily": {
        "task": "app.workers.tasks.decay_interest_weights.decay_interest_weights",
        "schedule": crontab(minute=0, hour=0),
    },
}
