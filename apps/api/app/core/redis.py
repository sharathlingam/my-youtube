import redis.asyncio as aioredis

from app.core.config import get_settings


async def create_redis_pool():
    settings = get_settings()
    return aioredis.from_url(
        settings.redis_url,
        encoding="utf-8",
        decode_responses=True,
        socket_connect_timeout=5,
        socket_timeout=5,
    )


async def close_redis_pool(client) -> None:
    await client.aclose()
