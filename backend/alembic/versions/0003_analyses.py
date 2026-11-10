"""add cv metadata and analyses

Revision ID: 0003_analyses
Revises: 0002_cv_profile_skills
Create Date: 2026-11-10
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0003_analyses"
down_revision: Union[str, None] = "0002_cv_profile_skills"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "cvs", sa.Column("page_count", sa.Integer(), nullable=True)
    )
    op.add_column(
        "cvs",
        sa.Column(
            "has_tables",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.add_column(
        "cvs",
        sa.Column(
            "has_images",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )

    op.create_table(
        "analyses",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("cv_id", sa.Uuid(), nullable=False),
        sa.Column("total_score", sa.Integer(), nullable=False),
        sa.Column("score_breakdown", sa.JSON(), nullable=False),
        sa.Column("suggestions", sa.JSON(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["cv_id"], ["cvs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_analyses_cv_id", "analyses", ["cv_id"])


def downgrade() -> None:
    op.drop_index("ix_analyses_cv_id", table_name="analyses")
    op.drop_table("analyses")
    op.drop_column("cvs", "has_images")
    op.drop_column("cvs", "has_tables")
    op.drop_column("cvs", "page_count")
