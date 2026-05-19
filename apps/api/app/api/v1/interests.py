from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.core.dependencies import get_db
from app.models.user import User
from app.models.user_interest import UserInterest

router = APIRouter()


class InterestOut(BaseModel):
    topic: str
    weight: float
    updated_at: str


class InterestIn(BaseModel):
    topic: str = Field(min_length=1, max_length=100)
    weight: float = Field(default=0.5, ge=0.0, le=5.0)


class WeightUpdate(BaseModel):
    weight: float = Field(ge=0.0, le=5.0)


@router.get("/api/v1/interests", response_model=list[InterestOut])
async def list_interests(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> list[InterestOut]:
    rows = (
        await db.execute(
            select(UserInterest)
            .where(UserInterest.user_id == current_user.id)
            .order_by(UserInterest.weight.desc(), UserInterest.topic)
        )
    ).scalars().all()
    return [
        InterestOut(
            topic=r.topic,
            weight=round(r.weight, 3),
            updated_at=r.updated_at.isoformat(),
        )
        for r in rows
    ]


@router.post("/api/v1/interests", response_model=InterestOut, status_code=201)
async def add_interest(
    body: InterestIn,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> InterestOut:
    topic = body.topic.strip().lower()
    now = datetime.now(timezone.utc)
    await db.execute(
        insert(UserInterest)
        .values(user_id=current_user.id, topic=topic, weight=body.weight)
        .on_conflict_do_update(
            constraint="uq_user_interests_user_topic",
            set_={"weight": body.weight},
        )
    )
    return InterestOut(topic=topic, weight=body.weight, updated_at=now.isoformat())


@router.patch("/api/v1/interests/{topic}", response_model=InterestOut)
async def update_interest(
    topic: str,
    body: WeightUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> InterestOut:
    row = (
        await db.execute(
            select(UserInterest)
            .where(UserInterest.user_id == current_user.id)
            .where(UserInterest.topic == topic.lower())
        )
    ).scalar_one_or_none()

    if not row:
        raise HTTPException(status_code=404, detail="Interest not found")

    row.weight = body.weight
    row.updated_at = datetime.now(timezone.utc)
    return InterestOut(
        topic=row.topic,
        weight=round(row.weight, 3),
        updated_at=row.updated_at.isoformat(),
    )


@router.delete("/api/v1/interests/{topic}", status_code=204)
async def delete_interest(
    topic: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> None:
    await db.execute(
        delete(UserInterest)
        .where(UserInterest.user_id == current_user.id)
        .where(UserInterest.topic == topic.lower())
    )
