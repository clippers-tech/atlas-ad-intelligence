"""Add optimization_event to ad_sets, conversion_breakdown to ad_metrics."""

from alembic import op
import sqlalchemy as sa

revision = "f6a7b8c9d0e1"
down_revision = "e5f6a7b8c9d0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "ad_sets",
        sa.Column(
            "optimization_event",
            sa.String(200),
            nullable=True,
        ),
    )
    op.add_column(
        "ad_metrics",
        sa.Column(
            "conversion_breakdown",
            sa.Text(),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("ad_metrics", "conversion_breakdown")
    op.drop_column("ad_sets", "optimization_event")
