"""phase3 tables: user_interests, watch_events, video_tags

Revision ID: 0003
Revises: 0002
Create Date: 2026-05-19
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "user_interests",
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("topic", sa.String(200), nullable=False),
        sa.Column("weight", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("user_id", "topic"),
        sa.UniqueConstraint("user_id", "topic", name="uq_user_interests_user_topic"),
    )

    op.create_table(
        "watch_events",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("video_id", sa.String(50), sa.ForeignKey("videos.id", ondelete="CASCADE"), nullable=False),
        sa.Column("watch_duration_secs", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("completion_rate", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("session_id", sa.String(36), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_watch_events_user_id", "watch_events", ["user_id"])
    op.create_index("ix_watch_events_video_id", "watch_events", ["video_id"])

    op.create_table(
        "video_tags",
        sa.Column("video_id", sa.String(50), sa.ForeignKey("videos.id", ondelete="CASCADE"), nullable=False),
        sa.Column("tag", sa.String(200), nullable=False),
        sa.Column("source", sa.String(50), nullable=False, server_default="api"),
        sa.PrimaryKeyConstraint("video_id", "tag"),
    )


def downgrade() -> None:
    op.drop_table("video_tags")
    op.drop_index("ix_watch_events_video_id", table_name="watch_events")
    op.drop_index("ix_watch_events_user_id", table_name="watch_events")
    op.drop_table("watch_events")
    op.drop_table("user_interests")
