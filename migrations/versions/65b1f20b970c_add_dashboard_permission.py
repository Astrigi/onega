"""add dashboard permission

Revision ID: 65b1f20b970c
Revises: 19bab491f66b
Create Date: 2026-09-04
"""

from alembic import op
import sqlalchemy as sa


revision = "65b1f20b970c"
down_revision = "19bab491f66b"
branch_labels = None
depends_on = None


def upgrade():
    permission_table = sa.table(
        "permissions",
        sa.column("code", sa.String),
        sa.column("description", sa.String),
    )

    op.bulk_insert(
        permission_table,
        [
            {
                "code": "dashboard.read",
                "description": "Доступ к личному кабинету",
            }
        ],
    )

    op.execute(
        sa.text("""
            INSERT INTO role_permissions (role_id, permission_id)
            SELECT r.id, p.id
            FROM roles r
            CROSS JOIN permissions p
            WHERE p.code = 'dashboard.read'
        """)
    )


def downgrade():
    op.execute(
        sa.text("""
            DELETE FROM role_permissions
            WHERE permission_id = (
                SELECT id
                FROM permissions
                WHERE code = 'dashboard.read'
            )
        """)
    )

    op.execute(
        sa.text("""
            DELETE FROM permissions
            WHERE code = 'dashboard.read'
        """)
    )
