"""Add budget_limit and budget_spent to rules table.

Revision ID: g7h8i9j0k1l2
Revises: f6a7b8c9d0e1
Create Date: 2026-03-17 04:15:00.000000+00:00
"""
from alembic import op
import sqlalchemy as sa

revision = "g7h8i9j0k1l2"
down_revision = "f6a7b8c9d0e1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "rules",
        sa.Column(
            "budget_limit",
            sa.Float(),
            nullable=True,
            comment="Max spend (account currency) before rule auto-acts",
        ),
    )
    op.add_column(
        "rules",
        sa.Column(
            "budget_spent",
            sa.Float(),
            nullable=False,
            server_default="0",
            comment="Spend accumulated against this rule's budget",
        ),
    )


def downgrade() -> None:
    op.drop_column("rules", "budget_spent")
    op.drop_column("rules", "budget_limit")
