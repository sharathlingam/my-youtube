from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.models.session import Session
from app.models.user import User

router = APIRouter()


class SyncRequest(BaseModel):
    session_token: str
    access_token: str
    refresh_token: str | None = None
    expires_at: int | None = None
    email: str
    name: str | None = None
    image: str | None = None
    google_id: str | None = None


class SyncResponse(BaseModel):
    user_id: str
    synced: bool


@router.post("/api/v1/auth/sync", response_model=SyncResponse)
async def sync_session(
    request: Request,
    body: SyncRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SyncResponse:
    # Upsert user
    user_id = str(uuid.uuid4())
    await db.execute(
        insert(User)
        .values(
            id=user_id,
            email=body.email,
            name=body.name,
            image=body.image,
            google_id=body.google_id,
            is_active=True,
        )
        .on_conflict_do_update(
            index_elements=["email"],
            set_={
                "name": body.name,
                "image": body.image,
                "google_id": body.google_id,
                "updated_at": datetime.now(UTC),
            },
        )
    )

    # Fetch the real user_id (may differ if user already existed)
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one()

    expires_at = (
        datetime.fromtimestamp(body.expires_at / 1000, tz=UTC)
        if body.expires_at
        else datetime.fromtimestamp(
            datetime.now(UTC).timestamp() + 3600, tz=UTC
        )
    )

    # Upsert session by session_token (stable UUID from JWT)
    await db.execute(
        insert(Session)
        .values(
            id=str(uuid.uuid4()),
            user_id=user.id,
            session_token=body.session_token,
            access_token=body.access_token,
            refresh_token=body.refresh_token,
            expires_at=expires_at,
        )
        .on_conflict_do_update(
            index_elements=["session_token"],
            set_={
                "access_token": body.access_token,
                "refresh_token": body.refresh_token,
                "expires_at": expires_at,
            },
        )
    )

    return SyncResponse(user_id=user.id, synced=True)
