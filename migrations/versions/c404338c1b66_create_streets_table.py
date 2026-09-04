"""create streets table

Revision ID: c404338c1b66
Revises: 65b1f20b970c
Create Date: 2026-09-04
"""

from alembic import op
import sqlalchemy as sa


revision = "c404338c1b66"
down_revision = "65b1f20b970c"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "streets",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column(
            "sort_order",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("name", name="uq_streets_name"),
    )

    op.bulk_insert(
        sa.table(
            "streets",
            sa.column("name", sa.String()),
            sa.column("sort_order", sa.Integer()),
            sa.column("is_active", sa.Boolean()),
        ),
        [
            {"name": "Просека 1", "sort_order": 1, "is_active": True},
            {"name": "Просека 2", "sort_order": 2, "is_active": True},
            {"name": "Просека 3", "sort_order": 3, "is_active": True},
            {"name": "РЯДОМ", "sort_order": 4, "is_active": True},
        ],
    )


def downgrade() -> None:
    op.drop_table("streets")
