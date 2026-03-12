"""Add meta_page_id and meta_page_token to accounts.

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-03-12
"""

from alembic import op
import sqlalchemy as sa

revision = "d4e5f6a7b8c9"
down_revision = "c3d4e5f6a7b8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "accounts",
        sa.Column("meta_page_id", sa.String(100), nullable=True),
    )
    op.add_column(
        "accounts",
        sa.Column("meta_page_token", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("accounts", "meta_page_token")
    op.drop_column("accounts", "meta_page_id")
