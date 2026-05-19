from __future__ import annotations

from fastapi import HTTPException, Request, status
from sqlalchemy import select

from app.models.session import Session
from app.models.user import User


async def get_current_user(request: Request) -> User:
    token = None
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]

    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    session_factory = request.app.state.session_factory
    async with session_factory() as db:
        result = await db.execute(
            select(User)
            .join(Session, Session.user_id == User.id)
            .where(Session.session_token == token)
            .where(User.is_active == True)  # noqa: E712
        )
        user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session")

    return user
