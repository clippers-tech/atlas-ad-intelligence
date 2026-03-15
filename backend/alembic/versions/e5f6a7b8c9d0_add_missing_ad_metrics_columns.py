"""add_missing_ad_metrics_columns

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-03-16 00:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e5f6a7b8c9d0'
down_revision: Union[str, None] = 'd4e5f6a7b8c9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add missing columns to ad_metrics that exist in the model
    # but were not included in the initial migration.
    op.add_column('ad_metrics', sa.Column('link_clicks', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('ad_metrics', sa.Column('clicks_all', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('ad_metrics', sa.Column('ctr_link', sa.Float(), nullable=False, server_default='0.0'))
    op.add_column('ad_metrics', sa.Column('ctr_all', sa.Float(), nullable=False, server_default='0.0'))
    op.add_column('ad_metrics', sa.Column('cpc_link', sa.Float(), nullable=False, server_default='0.0'))
    op.add_column('ad_metrics', sa.Column('cpc_all', sa.Float(), nullable=False, server_default='0.0'))
    op.add_column('ad_metrics', sa.Column('landing_page_views', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('ad_metrics', sa.Column('cost_per_lpv', sa.Float(), nullable=False, server_default='0.0'))
    op.add_column('ad_metrics', sa.Column('outbound_clicks', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('ad_metrics', sa.Column('cost_per_result', sa.Float(), nullable=False, server_default='0.0'))


def downgrade() -> None:
    op.drop_column('ad_metrics', 'cost_per_result')
    op.drop_column('ad_metrics', 'outbound_clicks')
    op.drop_column('ad_metrics', 'cost_per_lpv')
    op.drop_column('ad_metrics', 'landing_page_views')
    op.drop_column('ad_metrics', 'cpc_all')
    op.drop_column('ad_metrics', 'cpc_link')
    op.drop_column('ad_metrics', 'ctr_all')
    op.drop_column('ad_metrics', 'ctr_link')
    op.drop_column('ad_metrics', 'clicks_all')
    op.drop_column('ad_metrics', 'link_clicks')
