"""add_lead_meta_fields

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-03-12 15:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c3d4e5f6a7b8"
down_revision: Union[str, None] = "b2c3d4e5f6a7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "leads",
        sa.Column(
            "meta_lead_id",
            sa.String(length=100),
            nullable=True,
        ),
    )
    op.create_index(
        "ix_leads_meta_lead_id",
        "leads",
        ["meta_lead_id"],
        unique=True,
    )
    op.add_column(
        "leads",
        sa.Column(
            "meta_form_id",
            sa.String(length=100),
            nullable=True,
        ),
    )
    op.add_column(
        "leads",
        sa.Column(
            "meta_ad_id",
            sa.String(length=100),
            nullable=True,
        ),
    )
    op.add_column(
        "leads",
        sa.Column(
            "stage",
            sa.String(length=50),
            server_default="new",
            nullable=False,
        ),
    )
    op.add_column(
        "leads",
        sa.Column(
            "meta_created_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("leads", "meta_created_at")
    op.drop_column("leads", "stage")
    op.drop_column("leads", "meta_ad_id")
    op.drop_column("leads", "meta_form_id")
    op.drop_index(
        "ix_leads_meta_lead_id", table_name="leads"
    )
    op.drop_column("leads", "meta_lead_id")
