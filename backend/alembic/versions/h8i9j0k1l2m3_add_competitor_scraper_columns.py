"""Add Apify scraper config columns to competitor_configs.

Revision ID: h8i9j0k1l2m3
Revises: g7h8i9j0k1l2
Create Date: 2026-03-18 00:05:00.000000+00:00
"""
from alembic import op
import sqlalchemy as sa

revision = "h8i9j0k1l2m3"
down_revision = "g7h8i9j0k1l2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "competitor_configs",
        sa.Column("facebook_url", sa.Text(), nullable=True),
    )
    op.add_column(
        "competitor_configs",
        sa.Column(
            "scraper_country", sa.String(10),
            nullable=False, server_default="ALL",
        ),
    )
    op.add_column(
        "competitor_configs",
        sa.Column(
            "scraper_media_type", sa.String(20),
            nullable=False, server_default="all",
        ),
    )
    op.add_column(
        "competitor_configs",
        sa.Column(
            "scraper_platforms", sa.String(100),
            nullable=False, server_default="facebook,instagram",
        ),
    )
    op.add_column(
        "competitor_configs",
        sa.Column(
            "scraper_language", sa.String(10),
            nullable=False, server_default="en",
        ),
    )


def downgrade() -> None:
    op.drop_column("competitor_configs", "scraper_language")
    op.drop_column("competitor_configs", "scraper_platforms")
    op.drop_column("competitor_configs", "scraper_media_type")
    op.drop_column("competitor_configs", "scraper_country")
    op.drop_column("competitor_configs", "facebook_url")
