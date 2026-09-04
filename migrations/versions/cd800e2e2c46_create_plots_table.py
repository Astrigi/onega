"""create plots table

Revision ID: cd800e2e2c46
Revises: c404338c1b66
Create Date: 2026-09-04
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "cd800e2e2c46"
down_revision: Union[str, Sequence[str], None] = "c404338c1b66"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "plots",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "street_id",
            sa.Integer(),
            sa.ForeignKey("streets.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "plot_number",
            sa.String(length=20),
            nullable=False,
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
        sa.UniqueConstraint(
            "street_id",
            "plot_number",
            name="uq_plots_street_number",
        ),
    )


def downgrade() -> None:
    op.drop_table("plots")
