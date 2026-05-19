"""videos_channels_subscriptions

Revision ID: 0002
Revises: 0001
Create Date: 2026-05-19

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "channels",
        sa.Column("id", sa.String(50), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("thumbnail_url", sa.String(1024), nullable=True),
        sa.Column("subscriber_count", sa.BigInteger(), nullable=True),
        sa.Column(
            "fetched_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "videos",
        sa.Column("id", sa.String(20), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("channel_id", sa.String(50), nullable=False),
        sa.Column("channel_name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("thumbnail_url", sa.String(1024), nullable=True),
        sa.Column("duration_secs", sa.Integer(), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("category_id", sa.String(10), nullable=True),
        sa.Column("tags", sa.ARRAY(sa.String()), nullable=True),
        sa.Column("view_count", sa.BigInteger(), nullable=True),
        sa.Column(
            "fetched_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_videos_channel_id", "videos", ["channel_id"])
    op.create_index("ix_videos_published_at", "videos", ["published_at"])

    op.create_table(
        "user_subscriptions",
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("channel_id", sa.String(50), nullable=False),
        sa.Column("subscribed_since", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["channel_id"], ["channels.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id", "channel_id"),
    )


def downgrade() -> None:
    op.drop_table("user_subscriptions")
    op.drop_table("videos")
    op.drop_table("channels")
