"""pgvector extension + video_embeddings + user taste vector

Revision ID: 0004
Revises: 0003
Create Date: 2026-05-19
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels = None
depends_on = None

DIMS = 384


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.execute(f"""
        CREATE TABLE IF NOT EXISTS video_embeddings (
            video_id    TEXT        NOT NULL PRIMARY KEY
                            REFERENCES videos(id) ON DELETE CASCADE,
            embedding   vector({DIMS}) NOT NULL,
            model_ver   TEXT        NOT NULL DEFAULT 'all-MiniLM-L6-v2',
            embedded_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """)

    op.execute(f"""
        CREATE INDEX IF NOT EXISTS ix_video_embeddings_embedding
        ON video_embeddings USING ivfflat (embedding vector_cosine_ops)
        WITH (lists = 100)
    """)

    op.add_column("users", sa.Column("taste_embedding", sa.Text(), nullable=True))
    op.add_column("users", sa.Column("taste_updated_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "taste_updated_at")
    op.drop_column("users", "taste_embedding")
    op.drop_table("video_embeddings")
