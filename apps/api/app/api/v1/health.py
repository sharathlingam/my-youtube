from fastapi import APIRouter, Request
from pydantic import BaseModel
from sqlalchemy import text

router = APIRouter()


class HealthResponse(BaseModel):
    status: str
    db: str
    redis: str
    version: str = "0.1.0"


@router.get("/health", response_model=HealthResponse)
async def health_check(request: Request):
    db_status = "ok"
    redis_status = "ok"

    try:
        async with request.app.state.session_factory() as session:
            await session.execute(text("SELECT 1"))
    except Exception:
        db_status = "error"

    try:
        await request.app.state.redis.ping()
    except Exception:
        redis_status = "error"

    overall = "ok" if db_status == "ok" and redis_status == "ok" else "degraded"
    return HealthResponse(status=overall, db=db_status, redis=redis_status)
