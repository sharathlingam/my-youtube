import asyncio
from contextlib import asynccontextmanager

import sentry_sdk
from alembic import command as alembic_command
from alembic.config import Config as AlembicConfig
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.api.v1 import auth, feed, health, history, interests, search
from app.core.config import get_settings
from app.core.database import create_engine, get_session_factory
from app.core.redis import close_redis_pool, create_redis_pool


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()

    if settings.sentry_dsn:
        sentry_sdk.init(
            dsn=settings.sentry_dsn,
            environment=settings.environment,
            traces_sample_rate=0.1,
        )

    alembic_cfg = AlembicConfig("alembic.ini")
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, lambda: alembic_command.upgrade(alembic_cfg, "head"))

    engine = create_engine()
    app.state.engine = engine
    app.state.session_factory = get_session_factory(engine)

    redis_client = await create_redis_pool()
    app.state.redis = redis_client

    yield

    await close_redis_pool(redis_client)
    await engine.dispose()


def create_app() -> FastAPI:
    settings = get_settings()
    limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])

    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        docs_url="/docs" if settings.debug else None,
        redoc_url=None,
        lifespan=lifespan,
    )

    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore[arg-type]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router, tags=["health"])
    app.include_router(auth.router, tags=["auth"])
    app.include_router(feed.router, tags=["feed"])
    app.include_router(history.router, tags=["history"])
    app.include_router(search.router, tags=["search"])
    app.include_router(interests.router, tags=["interests"])

    return app


app = create_app()
