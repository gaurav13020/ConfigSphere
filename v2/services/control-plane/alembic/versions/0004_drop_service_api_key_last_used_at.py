"""drop service api key last_used_at

Revision ID: 0004_drop_last_used
Revises: 0003_service_api_keys
Create Date: 2026-04-11 17:05:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0004_drop_last_used"
down_revision = "0003_service_api_keys"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_column("service_api_keys", "last_used_at")


def downgrade() -> None:
    op.add_column("service_api_keys", sa.Column("last_used_at", sa.DateTime(), nullable=True))
